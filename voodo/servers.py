import sys
import logging
from importlib import import_module
from SimpleXMLRPCServer import SimpleXMLRPCServer

import config


def get_backend(backend_type):
    logging.info('get_backend type %s' % backend_type)
    backend = None
    try:
        backing_module = import_module(backend_type)
    except ImportError as e:
        logging.warn(e)
    else:
        name = "%s%s" % (backend_type[0].upper(), backend_type[1:])
        try:
            backend = getattr(backing_module, name)
        except AttributeError as e:
            logging.error(e)
    finally:
        logging.info('get_backend backing object %s' % backend)
        return backend

def main(addr, port, type_):
    logging.info('main creating server on %s:%d' % (addr, port))
    server = SimpleXMLRPCServer((addr, port), allow_none=True)
    backend_type = get_backend(type_)
    if backend_type:
        logging.info('main registering and server')
        server.register_instance(backend_type())
        server.serve_forever()
    
if __name__ == '__main__':
    if 'debug' in sys.argv:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARN)

    try:
        addr = intern(sys.argv[1])
        port = int(sys.argv[2])
        type_ = intern(sys.argv[3])
    except IndexError:
        logging.info('No or invalid arguments found. Defaulting to defaults')
        addr = intern('0.0.0.0')
        port = 4000
        type_ = intern('guest')
    except ValueError:
        sys.stderr.write("Invalid port number string: %s\n" % sys.argv[2])
        sys.exit(0)
    
    main(addr, port, type_)
