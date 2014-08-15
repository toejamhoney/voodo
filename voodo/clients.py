import sys
import socket
import logging
import xmlrpclib

if __name__ == "__main__":
    addr = sys.argv[1]
    port = sys.argv[2]
    fin = open(sys.argv[3], 'r')
    src = fin.read()
    try:
        proxy = xmlrpclib.ServerProxy('http://%s:%s' % (addr, port), allow_none=True)
        rv = proxy.guest_eval(src)
        print("Response: %s" % rv)
    except socket.error as e:
        print(str(e))
