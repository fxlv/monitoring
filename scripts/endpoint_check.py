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
from threading import Thread
from Queue import Queue
import json
import re

DEBUG = False
# maximum time in seconds to wait for the threads to complete
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


def average(result_list):
    """Return and average from a list"""
    total = 0
    for member in result_list:
        # it is possible that one if the results is 'None'
        # in such case return None as well
        if member == None:
            return None
        total += member
    return total / len(result_list)


def success_ratio(results):
    """Calculate success ratio from list of booleans"""
    ratio = 0  # default value
    oneresult = 100 / float(len(results))
    for result in results:
        if result:
            ratio += oneresult
    return int(ratio)


def parse_results(result_queue):
    """Iterate over the result queue and return results as a dictionary"""

    results = {}
    results["target"] = None
    results["port"] = None
    results["connection_status"] = []
    results["time_socket"] = []
    results["time_banner"] = []
    results["time_http_banner"] = []

    while not result_queue.empty():
        result = result_queue.get()
        results["target"] = result["target"]
        results["port"] = result["port"]
        results["connection_status"].append(result["connection_status"])
        results["time_socket"].append(result["time_socket"])
        results["time_banner"].append(result["time_banner"])
        results["time_http_banner"].append(result["time_http_banner"])

    results["success_rate"] = success_ratio(results["connection_status"])
    results["time_socket_avg"] = average(results["time_socket"])
    results["time_banner_avg"] = average(results["time_banner"])
    results["time_http_banner_avg"] = average(results["time_http_banner"])
    return results


def human_output(results):
    """Render the results in a human friendly output"""
    print "Target: {}:{}".format(results["target"], results["port"])
    print "Success rate: {}%".format(results["success_rate"])
    if results["time_socket_avg"]:
        print "Time socket: {}".format(results["time_socket_avg"])
    if results["time_banner_avg"]:
        print "Time banner: {}".format(results["time_banner_avg"])
    if results["time_http_banner_avg"]:
        print "Time HTTP banner: {}".format(results["time_http_banner_avg"])


def json_output(results):
    """Render the results as JSON"""
    # for easier use in influxdb, add to extra layers around
    json_results = {}
    json_results[results["target"]] = {}
    json_results[results["target"]][results["port"]] = results
    print json.dumps(json_results)


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
    parser.add_argument("-b",
                        action='store_true',
                        help="Batch mode (non-interactive")
    args = parser.parse_args()
    return args


def main():
    """Main logic happens here"""

    # set up required variables
    # TODO: this can probably be done in a better way
    args = parse_args()
    target = args.target
    port = args.p
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
        print "Target: {}, port: {}, connect count: {}".format(target, port,
                                                               args.c)

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
        if interactive_mode:
            sys.stdout.write(".")
            sys.stdout.flush()

        time.sleep(0.1)
    if interactive_mode:
        print  #  print a newline after all the dots

    # once all threads are done, check result_queue for results
    if result_queue.empty():
        die("No results?")  # TODO: more meaningful error would be nice

    results = parse_results(result_queue)

    # present the results in the requested way
    if interactive_mode:
        human_output(results)
    else:
        json_output(results)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print
        print "Ctrl-c pressed. Aborting."
        sys.exit(0)
