#!/usr/bin/env python

import telnetlib
import sys


def reset(port):
    port = str(port)
    print "Resetting connection on port %s" % port
    try:
        tn = telnetlib.Telnet('localhost', port)

    except Exception as e:
        print "Failed to connect Tor"
        print e
        sys.exit(2)

    tn.write('authenticate ""\n')
    tn.write('signal newnym\n')
    tn.close()
    print "Reset successful!"

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print "Must specify port number!"
        sys.exit(1)

    port = sys.argv[1]
    reset(port)
