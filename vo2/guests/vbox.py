import logging
import sys
from xmlrpclib import ServerProxy, Error
from time import sleep

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
        self.port = port
        self.proc = ProcMgr()
        self.msgs = None
        self.guest = None
        self.sniff = False

    def start(self, pcap=''):
        logging.debug("Start %s [%s:%s]" % (self.name, self.addr, self.port))
        cmd = [CMD, 'startvm', self.name]
        pid = self.proc.execute(cmd, fatal=True)
        out, err = self.proc.get_output(pid)
        sleep(1)
        if pcap:
            self.stop_sniff()
            self.set_pcap(pcap)
            self.start_sniff()
        sleep(1)
        while not self.ping_agent():
            sleep(2)

    def poweroff(self):
        cmd = [CMD, 'controlvm', self.name, 'poweroff']
        pid = self.proc.execute(cmd, fatal=True)
        out, err = self.proc.get_output(pid)
        if self.sniff:
            self.stop_sniff()
        self.guest = None

    def restore(self, name=''):
        cmd = [CMD, 'snapshot', self.name]
        if name:
            cmd.extend(['restore', name])
        else:
            cmd.append('restorecurrent')
        pid = self.proc.execute(cmd, fatal=True)
        out, err = self.proc.get_output(pid)

    def start_sniff(self):
        cmd = [CMD, 'controlvm', self.name, 'nictrace1', 'on']
        pid = self.proc.execute(cmd, fatal=True)
        out, err = self.proc.get_output(pid)
        self.sniff = True

    def stop_sniff(self):
        cmd = [CMD, 'controlvm', self.name, 'nictrace1', 'off']
        pid = self.proc.execute(cmd, fatal=True)
        out, err = self.proc.get_output(pid)
        self.sniff = False

    def set_pcap(self, filepath):
        logging.debug("Set PCAP on %s -> %s" % (self.name, filepath))
        cmd = [CMD, 'controlvm', self.name, 'nictracefile1', filepath]
        pid = self.proc.execute(cmd, fatal=True)
        out, err = self.proc.get_output(pid)

    def reset(self):
        self.poweroff()
        self.restore()
        self.start()

    def connect(self):
        try:
            self.guest = ServerProxy("http://%s:%s" % (self.addr, self.port))
        except Exception as e:
            sys.stderr.write("%s\n" % e)
            return False
        else:
            return True

    def ping_agent(self):
        if self.connect():
            return self.guest.ping()

    def push_sample(self, src, dst):
        try:
            return self.guest.pull(src, dst)
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
