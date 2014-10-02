import os
import sys

from catalog.samples import Sample


class Task(object):

    def __init__(self, cfg, vm, name='', path=''):
        """
        :type cfg: vo2.vcfg.Config
        :type vm: vo2.guests.vbox.VirtualMachine
        :param cfg:
        :return:
        """
        if name and path:
            self.sample = Sample(name, path)
        self.cfg = cfg
        self.vm = vm
        self.errors = []
        self.logfile = None

    def init(self):
        try:
            logpath = os.path.join(self.cfg.log, self.cfg.name, "%s.%s.log" % (self.sample.name, self.vm.name))
        except AttributeError:
            logpath = os.path.join(self.cfg.log, self.cfg.name, "%s.log" % self.vm.name)
        try:
            self.logfile = open(logpath, 'w')
        except IOError:
            sys.stderr.write("Unable to create log file: %s\n" % logpath)
            return False
        else:
            return True

    def setup_vm(self, suffix=''):
        self.vm.restore(self.cfg.snapshot)
        try:
            self.vm.start(os.path.join(self.cfg.pcap, self.cfg.name, '%s%s.pcap' % (self.sample.name, suffix)))
        except AttributeError:
            self.vm.start()

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
        if self.vm:
            self.vm.release()

    def close_log(self):
        if self.logfile:
            for e in self.errors:
                self.logfile.write(e)
            self.log("\n-- END LOG --\n")
            self.logfile.close()

    def log(self, msg):
        try:
            self.logfile.write(msg)
        except IOError as err:
            sys.stderr.write("Logging error: %s\n" % err)
        except AttributeError:
            sys.stderr.write(msg)
            sys.stderr.flush()
        else:
            self.logfile.flush()

    def __str__(self):
        try:
            s = "Task\n\tSample: %s\n\tVM: %s\n\tCfg: %s\n" % (self.sample.path, self.vm.name, self.cfg.name)
        except AttributeError:
            s = "Task\n\tVM: %s\n\tCfg: %s\n" % (self.vm.name, self.cfg.name)
        return s
