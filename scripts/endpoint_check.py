#!/usr/bin/env python
#
# Repeatedly connect to same server to check if it is responding.
# Try to grab a banner.
# If it does not send a banner, send an HTTP request.
#

import socket
import sys
import time
import datetime
import argparse
from threading import Thread, Semaphore
from Queue import Queue
import json

DEBUG = False
# time in secons to wait for the threads to complete
MAX_WAIT_TIME = 3

def die(msg=None):
    if msg:
        print msg
    sys.exit(1)


def connect(target, port):
    """
    Try to connecto to the target.
    Return a dictionary with results.
    """
    result = {}
    result["connection_status"] = False  # TODO: document
    time_socket_connected = None  # TODO: document
    result["time_http_banner"] = None  # TODO: document
    result["time_banner"] = None  # TODO: dopcument
    result["time_socket"] = None  # time spent to connect on TCP
    time_socket_start = datetime.datetime.now()
    socket.setdefaulttimeout(1)
    s = socket.socket()

    banner = None
    try:
        if DEBUG:
            print "Connecting to {}:{}".format(target, port)
        s.connect((target, int(port)))
        time_socket_connected = datetime.datetime.now()
        time_socket = time_socket_connected - time_socket_start
        # socket establishment time determined
        result["time_socket"] = time_socket.total_seconds()

        if DEBUG:
            print "Connected"
        # connection established
        result["connection_status"] = True
    except Exception, e:
        if DEBUG:
            print "Failed to connect"
            print e
        return result
    if DEBUG:
        print "Receiving..."
    try:
        banner = s.recv(2048)
        time_banner = datetime.datetime.now() - time_socket_start
        result["time_banner"] = float(time_banner.total_seconds())
    except Exception, e:
        if "timed out" in e:
            if DEBUG:
                print "Got a timeout, lets try sendig something first"
            if DEBUG:
                print "Sending 'hi!'..."
            hi = "GET /index.html HTTP/1.1\nUser-Agent: Python/0.01\nHost: {}\nAccept: */*\n\n".format(
                target)
            s.send(hi)
            if DEBUG:
                print "Reveiving..."
            banner = s.recv(2048)
            time_http_banner = datetime.datetime.now() - time_socket_start
            # http banner received
            result["time_http_banner"] = time_http_banner.total_seconds()
        else:
            if DEBUG:
                print "Unknown exception"
            if DEBUG:
                print e
    if banner:
        if DEBUG:
            print "Banner:\n{}".format(banner)
        if "HTTP/1.1 200 OK" in banner:
            time_http_banner = datetime.datetime.now() - time_socket_start
            result["time_http_banner"] = float(time_http_banner.total_seconds(
            ))
    return result


def check_hostname(target):
    try:
        if socket.gethostbyname(target):
            return True
    except Exception, e:
        if DEBUG:
            print "Exception: ", e
        return False


def check_target(target, port, result_queue):
    time_socket = connect(target, port)
    time_socket["timestamp"] = get_timestamp()
    time_socket["target"] = target
    time_socket["port"] = port
    result_queue.put(time_socket)
    return True


def get_timestamp():
    # TODO: Assert that : (datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds() - float(datetime.datetime.now().strftime("%s"))
    return (datetime.datetime.utcnow() - datetime.datetime(1970, 1,
                                                           1)).total_seconds()


def main():
    s = Semaphore()
    result_queue = Queue()
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Target IP or hostname")
    parser.add_argument("port", type=int, help="Target port")
    parser.add_argument("-c", default=1, type=int, help="Request count")
    parser.add_argument("-s",
                        default=1,
                        type=int,
                        help="Sleep time between retries (seconds)")
    parser.add_argument("-d", action='store_true', help="Enable debug mode")
    parser.add_argument("-a", action='store_true', help="Output only average")
    parser.add_argument("-j", action='store_true', help="JSON output")
    args = parser.parse_args()

    target = args.target
    if len(target.split(",")) > 1:
        targets = target.split(",")
    else:
        targets = [target]
    for target in targets:
        if not check_hostname(target):
            print "Could not resolve {}".format(target)
            print "Cannot continue..."
            sys.exit(1)
    port = args.port
    count = args.c
    sleep_time = args.s
    average_only = args.a
    global DEBUG  # TODO: there must be a better way to handle this
    DEBUG = args.d
    use_json_output = args.j
    if not use_json_output:
        print "Target: {}, port: {}, connect count: {}".format(target, port,
                                                               count)
    for i in range(0, count):
        for target in targets:
            t = Thread(target=check_target, args=(target, port, result_queue))
            t.start()
    wait_start = datetime.datetime.now()
    while result_queue.qsize() != count:
        # we wait MAX_WAIT_TIME for the thread to return results
        # if it takes longer, most likely it crashed
        # something to debug
        wait_time = datetime.datetime.now() - wait_start
        if wait_time.seconds > MAX_WAIT_TIME:
            break
        if not use_json_output:
            sys.stdout.write(".")
            sys.stdout.flush()
        time.sleep(0.1)
    if not use_json_output:
        print  #  print a newline after all the dots
    # once all threads are done, check result_queue for results
    if result_queue.empty():
        die("No results?")
    # average output only 
    if average_only:
        averages = {}
        time_socket = []
        time_http_banner = []
        result_count = 0
        while not result_queue.empty():
            result = result_queue.get()
            result_count += 1
            if "time_socket" in result:
                time_socket.append(result["time_socket"])
            if "time_http_banner" in result:
                time_http_banner.append(result["time_http_banner"])
        print "Result count: {}".format(result_count)
        print "Time socket: {}".format(average(time_socket))
        print "Time HTTP banner: {}".format(average(time_http_banner))
    # non-average output
    else:
        if not use_json_output:
            print "{} results".format(result_queue.qsize())

        if result_queue.qsize() == 1:
            # if there's only one result,
            # encapsulate the result in additional layers 
            # that describe target host and port
            results = {}
            results[target] = {}
            results[target][port]=result_queue.get()
            print json.dumps(results)
        else:
            while not result_queue.empty():
                # if there's more than one result, we can't handle it at the moment
                # so just iterate over results queue and dump it all 
                print json.dumps(result_queue.get())


def average(result_list):
    total = 0
    for member in result_list:
        total += member
    return total / len(result_list)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print
        print "Ctrl-c pressed. Aborting."
        sys.exit(0)
