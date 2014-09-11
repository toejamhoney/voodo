import sys
from importlib import import_module
from threading import Thread
from multiprocessing import Queue

import gpool


class GuestManager(object):

    def __init__(self, cfg):
        setting = cfg.setting('guests', 'vms').split(',')
        self.vm_map = dict(zip(setting, [None for i in setting]))
        self.populate_map(cfg)
        self.pool = gpool.GuestPool(self.vm_map)
        self.msgs = Queue()
        self.reader = Thread(self.check_msgs)
        self.reader.start()

    def populate_map(self, cfg):
        factory = VmFactory(cfg)
        for vm in self.vm_map:
            self.vm_map[vm] = factory.make(vm)

    def find_vm(self, names):
        rv = None
        for name in names:
            rv = self.pool.acquire(name)
            if rv:
                rv.msgs = self.msgs
                break
        return rv

    def release_vm(self, name):
        self.pool.release(name)

    def check_msgs(self):
        while True:
            msg = self.msgs.get()
            self.release_vm(msg)


class VmFactory(object):

    def __init__(self, cfg):
        self.cfg = cfg

    def make(self, vmname):
        vm = self.cfg.setting('guests', vmname)
        type_, delim, vm = vm.partition(',')
        return self.instanciate(type_, vm)

    def instanciate(self, type_, cfgvm):
        try:
            gmodule = import_module('guests.%s' % type_)
        except ImportError as e:
            sys.stderr.write("%s\n\n" % e)
            sys.stderr.write("Unable to import virtual device module: %s\n" % type_)
            return None
        else:
            name, addr, port = cfgvm.split(',')
            return gmodule.VirtualMachine(name, addr, port)