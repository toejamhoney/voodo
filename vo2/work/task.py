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
        try:
            self.log = open(self.cfg.setting('job', 'log'), 'w')
        except IOError:
            sys.stderr.write("Unable to create log file: %s\n" % self.cfg.setting('job', 'log'))
        self.vm.restore(self.cfg.setting('snapshot'))
        self.vm.start()

    def remote_exec(self, src):
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
        self.log.close()
        self.vm.poweroff()
        self.vm.release()
