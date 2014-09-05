import sys
from importlib import import_module

import gpool


class GuestManager(object):

    def __init__(self, cfg):
        setting = cfg.setting('guests', 'vms').split(',')
        self.vm_map = dict(zip(setting, [None for i in setting]))
        self.populate_map(VmFactory(cfg))
        self.pool = gpool.GuestPool(self.vm_map)

    def populate_map(self, factory):
        for vm in self.vm_map:
            self.vm_map[vm] = factory.make(vm)


class VmFactory(object):

    def __init__(self, cfg):
        self.cfg = cfg

    @staticmethod
    def make(self, vmname):
        vm = self.cfg.setting('guests', vmname)
        type_, delim, vm = vm.partition(',')
        return self.instanciate(type_, vm)

    @staticmethod
    def instanciate(self, type_, cfgvm):
        try:
            gmodule = import_module(type_)
        except ImportError:
            sys.stderr.write("Unable to import virtual device module: %s\n" % type_)
            return None
        else:
            name, addr, port = cfgvm.split(',')
            return gmodule(name, addr, port)