import sys
import logging as log
from time import sleep, time
from xmlrpclib import ServerProxy

from vlibs.proc_mgmt import ProcMgr


CMD = '/usr/bin/VBoxManage'


class VirtualMachine(object):

    def __init__(self, name, addr, port):
        """
        :type self.msgs: multiprocessing.Queue
        :type self.guest: vo2.net.guest.EvalServer
        :return:
        """
        self.name = name
        self.addr = addr
        self.host_addr = "10.%s.%s.1" % (addr.split('.')[1], addr.split('.')[1])
        self.port = port
        self.proc = ProcMgr()
        self.msgs = None
        self.guest = None
        self.sniff = False
        self.state = None

    def start(self, pcap=''):
        log.debug("Start %s [%s:%s]" % (self.name, self.addr, self.port))
        self.update_state()
        if self.state != 'saved':
            self.restore()
        cmd = [CMD, 'startvm', self.name]
        if self.proc.exec_quiet(cmd) != 0:
            self.error('start failure: %s' % cmd)
            sys.exit(1)
        sleep(1)
        if pcap:
            self.stop_sniff()
            self.set_pcap(pcap)
            self.start_sniff()
        sleep(1)
        while not self.ping_agent():
            sleep(1)

    def poweroff(self):
        cmd = [CMD, 'controlvm', self.name, 'poweroff']
        if self.proc.exec_quiet(cmd) != 0:
            self.error('poweroff error: %s' % cmd)
            sys.exit(1)
        if self.sniff:
            self.stop_sniff()
        self.guest = None

    def restore(self, name=''):
        self.update_state()
        if self.state == 'running':
            self.poweroff()
        cmd = [CMD, 'snapshot', self.name]
        if name:
            cmd.extend(['restore', name])
        else:
            cmd.append('restorecurrent')
        if self.proc.exec_quiet(cmd) != 0:
            sys.exit(1)

    def take_snap(self, name=''):
        if not name:
            name = str(time())
        cmd = [CMD, 'snapshot', self.name, 'take', name]
        if self.proc.exec_quiet(cmd) != 0:
            self.error('take_snap error: %s' % cmd)
            sys.exit(1)

    def del_snap(self, name):
        cmd = [CMD, 'snapshot', self.name, 'delete', name]
        if self.proc.exec_quiet(cmd) != 0:
            self.error('del_snap error: %s' % cmd)
            sys.exit(1)

    def update_state(self):
        cmd = [CMD, 'showvminfo', self.name, '--machinereadable']
        pid = self.proc.execute(cmd)
        out, err = self.proc.get_output(pid)
        if not out:
            self.state = None
            return False
        for line in out.split('\n'):
            if line.startswith('VMState='):
                self.state = line.partition('=')[2].strip('"')
                break

    def start_sniff(self):
        cmd = [CMD, 'controlvm', self.name, 'nictrace1', 'on']
        if self.proc.exec_quiet(cmd) != 0:
            self.error('start_sniff error: %s' % cmd)
            sys.exit(1)
        self.sniff = True

    def stop_sniff(self):
        cmd = [CMD, 'controlvm', self.name, 'nictrace1', 'off']
        if self.proc.exec_quiet(cmd) != 0:
            self.error('stop_sniff error: %s' % cmd)
            sys.exit(1)
        self.sniff = False

    def set_pcap(self, filepath):
        self.error("Set PCAP on %s -> %s" % (self.name, filepath))
        cmd = [CMD, 'controlvm', self.name, 'nictracefile1', filepath]
        if self.proc.exec_quiet(cmd) != 0:
            self.error('set_pcap error: %s' % cmd)
            sys.exit(1)

    def reset(self):
        self.poweroff()
        self.restore()
        self.start()

    def connect(self):
        try:
            self.guest = ServerProxy("http://%s:%s" % (self.addr, self.port))
        except Exception as e:
            self.error("connect error: %s" % e)
            return False
        else:
            return True

    def ping_agent(self):
        if self.connect():
            return self.guest.ping()

    def push_sample(self, src, dst):
        try:
            return self.guest.pull(src, dst, self.host_addr)
        except AttributeError:
            return False

    def release(self):
        """
        :type self.msgs: multiprocessing.Queue
        """
        try:
            self.msgs.put(self.name)
        except AttributeError:
            sys.stderr.write("%s: unable to signal completion to VM manager. Messages queue not set\n" % self.name)

    def error(self, msg):
        log.error('%s(%s:%s) %s' % (self.name, self.addr, self.port, msg))
