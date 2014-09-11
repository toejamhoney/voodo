import sys
from xmlrpclib import ServerProxy, Error
from time import sleep

from vlibs.proc_mgmt import ProcMgr


CMD = '/usr/bin/VBoxManage'


class VirtualMachine(object):


    def __init__(self, name, addr, port):
        """
        :type self.guest: vo2.net.guest.EvalServer
        :param name:
        :param addr:
        :param port:
        :return:
        """
        self.name = name
        self.addr = addr
        self.port = port
        self.proc = ProcMgr()
        self.guest = None

    def start(self):
        cmd = [CMD, 'startvm', self.name]
        pid = self.proc.execute(cmd, fatal=True)
        out, err = self.proc.get_output(pid)
        while not self.ping_agent():
            sleep(2)

    def poweroff(self):
        cmd = [CMD, 'controlvm', self.name, 'poweroff']
        pid = self.proc.execute(cmd, fatal=True)
        out, err = self.proc.get_output(pid)

    def restore(self, name=''):
        cmd = [CMD, 'snapshot', self.name]
        if name:
            cmd.extend(['restore', name])
        else:
            cmd.append('restorecurrent')
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
            self.guest.ping()


