#!/usr/bin/env python
"""
Repeatedly connect to same server to check if it is responding.
Try to grab a banner.
If it does not send a banner, send an HTTP request.
"""

import socket
import sys
import time
import datetime
import argparse
from threading import Thread, Semaphore
from Queue import Queue
import json
import re

DEBUG = False
# maximum time in secons to wait for the threads to complete
# this is not the same as timeout for the tcp connections
# but rather a way to abort if a thread gets 'stuck'
MAX_THREAD_WAIT_TIME = 3


def die(error_msg=None):
    """
    Exit with code 1.
    Optionally print an error message.
    """
    if error_msg:
        print "Error: {0}".format(error_msg)
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
    """Return true if target hostname can be resolved"""
    try:
        if socket.gethostbyname(target):
            return True
    except Exception:
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


def target_is_ip(target):
    """Return true if target is an IPv4 IP"""
    pattern = "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$"
    return re.match(pattern, target)


def validate_target(target):
    """Return true if target is valid

    Determine if it's a valid IP or a hostname.
    For hostnames, check if it can be resolved.
    """
    if target_is_ip(target):
        return True
    else:
        if check_hostname(target):
            return True
    return False


def parse_args():
    """Parse arguments and return them"""
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Target IP or hostname")
    parser.add_argument("-p",
                        type=int,
                        default=80,
                        help="Target port. Default port is 80")
    parser.add_argument("-c", default=1, type=int, help="Request count")
    parser.add_argument("-s",
                        default=1,
                        type=int,
                        help="Sleep time between retries (seconds)")
    parser.add_argument("-a", action='store_true', help="Output only average")
    parser.add_argument("-j", action='store_true', help="JSON output")
    parser.add_argument("-b", action='store_true', help="Batch mode (non-interactive")
    args = parser.parse_args()
    return args


def main():
    """Main logic happens here"""

    # set up required variables
    # TODO: this can probably be done in a better way
    args = parse_args()
    target = args.target
    port = args.p
    sleep_time = args.s
    average_only = args.a
    s = Semaphore()
    result_queue = Queue()
    use_json_output = args.j

    # interactive mode or batch mode?
    if args.b:
        interactive_mode = False
    else:
        interactive_mode = True

    # validate the target
    if not validate_target(target):
        msg = "Invalid target provided. Target has to be an IP address or a hostname."
        die(msg)
    # print out a summary of work to be done
    if interactive_mode:
        print "Target: {}, port: {}, connect count: {}".format(target, port, args.c)

    # launch the actual test(-s)

    for i in range(args.c):
        t = Thread(target=check_target, args=(target, port, result_queue))
        t.start()
    if interactive_mode:
        print "All the threads are running, wait please"

    # all threads running, wait on results
    wait_start = datetime.datetime.now()
    while result_queue.qsize() != args.c:
        # we wait MAX_THREAD_WAIT_TIME for the thread to return results
        # if it takes longer, most likely it crashed
        # something to debug
        wait_time = datetime.datetime.now() - wait_start
        if wait_time.total_seconds() > MAX_THREAD_WAIT_TIME:
             die("MAX_THREAD_WAIT_TIME violation")

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
            results[target][port] = result_queue.get()
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
