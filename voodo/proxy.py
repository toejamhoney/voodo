# Python Modules
import logging

# Voodo Modules
from config import RPC_SERVERS
import clients
import voodo_errors

class RPCProxy(object):

    def __init__(self, *names):
        self.servers = {}
        for name in names:
            self.register_server(name)

    def is_proxy(self, name):
        if self.servers.has_key(name):
            return True
        else:
            return False

    def get_proxy(self, name):
        if not self.is_proxy(name):
            return False
        return self.servers.get(name)

    def register_server(self, server_name):
        server = RPC_SERVERS.get(server_name)
        try:
            address = server.get('address')
        except AttributeError:
            raise voodo_errors.VoodoException(str(server_name) + ': not found')
        else:
            if server.get('type') == 'job':
                self.servers['job'] = RPCServer(address)
            self.servers[server_name] = RPCServer(address)

    def unregister_server(self, server_name):
        try:
            self.servers.pop(server_name)
        except KeyError:
            print str(server_name) + " did not exist"
        else:
            print str(server_name) + " is unregistered"

    def __getattr__(self, server_name):
        logging.debug("Proxy getattr: %s", server_name)
        return self.servers.get(server_name)

    def __str__(self):
        return "I am the c-omni-muni-ca-nator!"


class RPCServer(object):

    def __init__(self, address_tuple):
        self.rpc_client = clients.RPCClient(address_tuple)

    def get_method(self, name):
        return RPCMethod(self.rpc_client, name)

    def __getattr__(self, method_name):
        logging.debug("Server getattr: %s", method_name)
        return RPCMethod(self.rpc_client, method_name)


class RPCMethod(object):

    def __init__(self, rpc_client, method_name):
        self.method_name = method_name
        self.client = rpc_client

    def __call__(self, params=None):
        return self.client.call(self.method_name, params)


if __name__ == '__main__':
    print 'Creating'
    rpc_test7a = RPCProxy('local_host')
    print str(rpc_test7a)
    rpc_test7a.test7a.debug('First debug string to test7a')
    rpc_test_result = rpc_test7a.test7a.echo('First echo call to test7a')
    print 'Result: ', rpc_test_result
