import time
import logging
import os

import proc_mgmt
import clients
import proxy
import config
import tasks
from tasks import Task

class VirtualDevice(object):
  
    def __init__(self, name=''):
        self.name = name
        self.state = ''
        self.busy = False
        self.proc_mgr = proc_mgmt.ProcMgr()
    
    def start(self):
        pass
    def poweroff(self):
        pass
    def save(self):
        pass
    def delete(self):
        pass
    def restore(self):
        pass
    def run_task(self, task):
        pass
      
class VBoxMachine(VirtualDevice):

    root_cmd = '/usr/bin/VBoxManage'

    def __init__(self, name=''):
        logging.debug('Init VBoxMachine: ' + name)
        address = config.GUESTS.get(name)
        if not address:
            print name + ' is not in config module. No address, port set.'
            print '    Device is unusable.'
            self.rpc_proxy = None
        else:
            address = address.get('address')
            port = config.SETTINGS.get('NEW_PORT')
            self.rpc_proxy = clients.RPCClient( (address, port) )
        super(VBoxMachine, self).__init__(name)

    def run_task(self, task):
        task.log("Machine state: " + self.state)
        self.update_state()
        task.log("Updated machine state: " + self.state)
        if self.state != 'running':
            task.log("Machine is not in a running state. Reseting machine")
            self.reset()
        else:
            task.log("Machine is up and running. Assumed good state")
        if self.rpc_proxy and self.ping_agent():
            task.log("Machine agent is reachable via the network")
            task.log("BEGIN task execution")
            results = self.rpc(task)
            task.log("RESULTS:")
            if isinstance(results, dict):
                for result in results.get('results'):
                    if isinstance(result, list):
                        for item in list:
                            task.log(str(item))
                    else:
                        task.log(str(result))
            task.log("END task execution")
        if task.getArg('reset'):
            task.log("Resetting virtual device")
            # TODO Why isn't this resetting, blocking?
            self.reset()
            task.log("Reset")
        else:
            task.log('Cannot determine machine network location')

    def ping_agent(self):
        method_target = proxy.RPCMethod(self.rpc_proxy, "echo")
        return method_target(None)

    def rpc(self, task):
        method_name = task.getArg('method')
        task.log("Creating RPC callee: " + method_name)
        method_target = proxy.RPCMethod(self.rpc_proxy, method_name)
        task.log("Calling")
        job_dic = task.job_dic
        return method_target(job_dic)
      
    def update_state(self):
        cmd = [ VBoxMachine.root_cmd, 'showvminfo', self.name, '--machinereadable']
        pid = self.proc_mgr.execute(cmd)
        out, err = self.proc_mgr.get_output(pid)
        if not out:
            print "Error getting VM state: " + str(err)
            self.state = 'unknown'
            return False
        for line in out.split('\n'):
            if line.startswith('VMState='):
                self.state = line.partition('=')[2].strip('"')

    def start(self):
        cmd = [ VBoxMachine.root_cmd, 'startvm', self.name ]
        pid = self.proc_mgr.execute(cmd, fatal=True)
        out, err = self.proc_mgr.get_output(pid)
        logging.debug('Issued start cmd. PID: %s', pid)
        while not self.ping_agent():
            time.sleep(1)

    def poweroff(self):
        cmd = [ VBoxMachine.root_cmd, 'controlvm', self.name, 'poweroff' ]
        pid = self.proc_mgr.execute(cmd, fatal=True)
        out, err = self.proc_mgr.get_output(pid, timeout=10)
        if err == 'SIGTERM' or err == 'SIGKILL':
          print "Hung process. Sent",err,"to process:",str(pid)

    def save(self, name='no_name', desc='none'):
        self.snapshot(snap_name, desc)
      
    def delete(self, snap_name='no_name'):
        self.snapshot(snap_name, desc, delete=True)
    
    def reset(self):
        self.restore()
        self.start()

    def restore(self, name=None):
        if name:
            cmd = [ VBoxMachine.root_cmd, 'snapshot', self.name, 'restore', name ]
        else:
            cmd = [ VBoxMachine.root_cmd, 'snapshot', self.name, 'restorecurrent' ]
        pid = self.proc_mgr.execute(cmd, fatal=True)
        out, err = self.proc_mgr.get_output(pid)
    
    def snapshot(self, snap_name='no_name', desc='none', delete=False):
        if delete:
            cmd = [ VBoxMachine.root_cmd, 'snapshot', self.name, 'delete', snap_name ]
        else:
            cmd = [ VBoxMachine.root_cmd, 'snapshot', self.name, 'take', snap_name, '--description', desc, '--pause' ]
        pid = self.proc_mgr.execute(cmd, fatal=True)
        out, err = self.proc_mgr.get_output(pid)

    def __getattr__(self, method_name):
        return proxy.RPCMethod(self.rpc_proxy, method_name)
      
if __name__ == "__main__":
    '''
    tester = VBoxMachine('test7a')
    print 'Restoring test7a'
    tester.restore()
    print 'Start test7a'
    tester.start()
    print 'Connecting to agent...'
    result = tester.echo('Test string')
    print 'Response: ', result
    print 'Killing test7a'
    tester.poweroff()
    '''
    testerb = VBoxMachine('test7b')
    result = testerb.echo("Testing test7b")
    print result
