#!/usr/bin/env python
import sys
import os
import json
tcp_max_orphans_file = "/proc/sys/net/ipv4/tcp_max_orphans"
sockstat_file = "/proc/net/sockstat"


def main(arg):
    required_files = [tcp_max_orphans_file, sockstat_file]

    for required_file in required_files:
        if not os.path.exists(required_file):
            print "{} does not exist.".format(required_file)
            print "Cannot continue."
            sys.exit(1)
    # get max orphans value
    with open(tcp_max_orphans_file) as tcp_max_orphans:
        max_orphans = int(tcp_max_orphans.readline().strip())

    # TCP: inuse 7 orphan 0 tw 0 alloc 11 mem 0
    with open(sockstat_file) as sockstat:
        for line in sockstat:
            if line.startswith("TCP"):
                line = line.strip().split()
                # ['TCP:', 'inuse', '7', 'orphan', '0', 'tw',
                # '0', 'alloc', '11', 'mem', '0']
                tcp_sockets_inuse = int(line[2])
                tcp_orphans = int(line[4])
                tcp_mem = int(line[10])
            elif line.startswith("UDP:"):
                # UDP: inuse 5 mem 1
                line = line.strip().split()
                udp_sockets_inuse = int(line[2])
                udp_mem = int(line[4])
    # print out  the output and if argument 'json' has been provided
    # then do as the nice human has requested and output json

    if arg == "json":
        json_str = {"tcp.orphans": tcp_orphans,
                    "tcp.sockets_in_use": tcp_sockets_inuse,
                    "tcp.mem": tcp_mem,
                    "tcp.max_orphans": max_orphans,
                    "udp.sockets_in_use": udp_sockets_inuse,
                    "udp.mem": udp_mem}
        print json.dumps(json_str)

    else:
        print "tcp.orphans=%s" % tcp_orphans
        print "tcp.sockets_in_use=%s" % tcp_sockets_inuse
        print "tcp.mem=%s" % tcp_mem
        print "tcp.max_orphans=%s" % max_orphans
        print "udp.sockets_in_use=%s" % udp_sockets_inuse
        print "udp.mem=%s" % udp_mem


if __name__ == "__main__":
    if len(sys.argv) == 2:
        # an argument has been provided
        arg = sys.argv[1]
    else:
        arg = None
    # forward the argument to main()
    main(arg)
