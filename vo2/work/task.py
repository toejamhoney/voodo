import os
import sys
from time import sleep

from catalog.samples import Sample


class Task(object):

    def __init__(self, vm, name, path, cfg):
        """
        :type cfg: vo2.vcfg.Config
        :type vm: vo2.guests.vbox.VirtualMachine
        :param cfg:
        :return:
        """
        self.sample = Sample(name, path)
        self.cfg = cfg
        self.vm = vm
        self.errors = []
        self.log = None

    def init(self):
        logpath = os.path.join(self.cfg.log, self.cfg.name, "%s.log" % self.sample.name)
        try:
            self.log = open(logpath, 'w')
        except IOError:
            sys.stderr.write("Unable to create log file: %s\n" % logpath)
            return False
        else:
            return True

    def setup_vm(self, suffix=''):
        self.vm.restore(self.cfg.snapshot)
        self.vm.start(os.path.join(self.cfg.pcap, '%s%s.pcap' % (self.sample.name, suffix)))

    def teardown_vm(self):
        self.vm.poweroff()

    def remote_eval(self, src):
        if not src:
            return False
        rv = None
        try:
            rv = self.vm.guest.guest_eval(src)
        except Exception as e:
            self.errors.append("%s" % e)
            rv = False
        finally:
            return rv

    def complete(self):
        if self.log:
            self.log.close()
        if self.vm:
            self.vm.release()

    def __str__(self):
        return "Task\n\tSample: %s\n\tVM: %s\n" % (self.sample.path, self.vm.name)
