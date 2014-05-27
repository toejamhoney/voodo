#!/usr/bin/python
            #return self._kill(args.get('vm'))
#vim: set fileencoding=utf-8 :
import argparse
from contextlib import contextmanager
import os
import subprocess
import threading
import time

import vboxapi

import config
import voodo_comm


######################################################################
### VirtualBox Machines Driver / Controller
class VBoxDriver(object):

      def __init__(self):
          self.VBConstants = vboxapi.VirtualBoxReflectionInfo(False)
          self.VBMgr = vboxapi.VirtualBoxManager(None, None)
          self.VBox = self.VBMgr.vbox
          self.VBSession = self.VBMgr.mgr.getSessionObject(self.VBox)
          self.sender = voodo_comm.VoodoClient()
          self.lock = threading.Lock()

      def parse_arguments(self, line):
          parser = argparse.ArgumentParser()
          parser.add_argument('-a', '--action')
          parser.add_argument('-n', '--name', nargs='*', default='')
          parser.add_argument('-d', '--desc', default='none')
          parser.add_argument('-v', '--machines', default=[], nargs='*')
          parser.add_argument('-r', '--restore',
                                default=False,
                                action='store_true')
          try:
            result = parser.parse_args(line)
            result = vars(result)
          except SystemExit:
            print 'Parsing failed:',line
            return None
          else:
            result['name'] = ' '.join(result['name'])
            return result


      ##################################################
      ##### Handles

      def start(self, args):
          if args:
            vms = args.get('machines')
            restore = args.get('restore')
            
            # Get the machines ready for start
            for vm in vms:
                cmd = ['/usr/bin/VBoxManage', 'showvminfo', vm]
                subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = subproc.communicate()
                if not stdout:
                    print str(cmd) + 'failed'
                    return False
                for line in stdout:
                    if line.startswith('State:'):
                        if 'aborted' in line:
                            if not self.restore({'machines': [vm,]}):
                                print 'Restoring aborted machine failed'
                                return False
                        elif 'saved' not in line and restore:
                            if not self.restore({'machines': [vm,]}):
                                print 'Restoring powered off machine failed'
                                return False

            for vm in vms:
                self.lock.acquire()
                cmd = ['/usr/bin/VBoxManage', 'startvm',  vm]
                #subproc = subprocess.Popen(cmd, shell=True)
                subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout,stderr = subproc.communicate()
                if stdout:
                  pass
                  #print stdout
                if stderr:
                  pass
                self.lock.release()

            for vm in vms:
                # Poll the machine for its IP address
                # this will generally return after windows gets settings through DHCP
                probe_max_attempts = 60
                attempts = 0
                while attempts < probe_max_attempts:
                  attempts += 1
                  if self.sender.probe_server(vm, config.GUESTS[vm]['address']):
                    break
                  self.manual_sleep(1)

            return True
            #return self._start(args.get('vm'))

      def kill(self, args):
          if args:
            self.lock.acquire()
            vms = args.get('machines')
            for vm in vms:
                cmd = ['/usr/bin/VBoxManage', 'controlvm', vm, 'poweroff']
                subproc = subprocess.Popen(cmd)#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if self.check_ret_code(10, subproc) != 0:
                    print 'VirtualBox hung while terminating machine'
                    try:
                        subproc.kill()
                    except OSError as e:
                        if e.errno == 3:
                            pass
            self.lock.release()

      def check_ret_code(self, timeout, process):
          for x in range(timeout):
              ret = process.poll()
              if ret == 0:
                print 'VirtualBox killed machine. Attempts: ',x
                return 0
              self.manual_sleep(1)
          return ret

      def restore(self, args):
          if args:
            self.lock.acquire()
            vms = args.get('machines')
            for vm in vms:
                if args.get('name'):
                    cmd = ['/usr/bin/VBoxManage', 'snapshot', vm, 'restore', args.get('name')]
                else:
                    cmd = ['/usr/bin/VBoxManage', 'snapshot', vm, 'restorecurrent']
                subproc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout,stderr = subproc.communicate()
                if stdout:
                  pass
                if stderr:
                  pass
            self.lock.release()
            return True
            #return self._restore(args.get('vm'), args.get('name'))

      def snapshot(self, args):
          if args.get('action') == 'del':
            return self._del_snapshot(args.get('machines'), args.get('name'))
          else:
            return self._snapshot(args.get('machines'), args.get('name'), args.get('desc'))


      ##################################################
      ##### Functions

      # Starts up VMs in the names list
      def _start(self, VM):
          result = False
          probe_max_attempts = 100
          self.lock.acquire()
          # We cannot use the With...lock here since the launchVMProcess creates
          # a lock at the same time
          machine = self.VBox.findMachine(VM)
          if not machine:
            print 'Could not find VM:',VM
            return None
          try:
            progress = machine.launchVMProcess(self.VBSession,"gui","")
          except Exception as error:
            print 'Error starting VM:',repr(error)
          else:
            #wait indefinitely (-1) for progress to complete
            progress.waitForCompletion(-1)
            self.VBSession.unlockMachine()
            # Poll the machine for its IP address
            # this will generally return after windows gets settings through DHCP
            attempts = 0
            while attempts < probe_max_attempts:
              attempts += 1
              if self.sender.probe_server(VM, config.GUESTS[VM]['address']):
                break
              self.manual_sleep(1)
          self.lock.release()
          return result

      # Unfriendly shutdown method. Unplugs the VM basically.
      # Needs to be given some time for VirtualBox to shut it down.
      # The waitforcompletion function does not work well enough
      # for the device to be ready for a restore and startup so we
      # sleep it manually.
      def _kill(self, VM, sleep_time = 10):
          result = False
          with self.locked(VM) as machine:
            progress = self.VBSession.console.powerDown()
            progress.waitForCompletion(-1)
            result = True
          if result:
            self.manual_sleep(sleep_time)
          return result

      # Restores to the machine's 'current' snapshot, which is generally the last one
      def _restore(self, VM, snapshot_name, sleep_time = 7):
          result = False
          with self.locked(VM) as machine:
            if not snapshot_name:
              snapshot = machine.currentSnapshot
            else:
              snapshot = machine.findSnapshot(snapshot_name)
            progress = self.VBSession.console.restoreSnapshot(snapshot)
            progress.waitForCompletion(-1)
            result = True
          if result:
            self.manual_sleep(sleep_time)
          return result

      def _snapshot(self, machines, name=None, desc=None):
          result = False
          for VM in machines:
              with self.locked(VM) as machine:
                if not name:
                  name = time.strftime('SNAP_%I:%M:%S', time.localtime())
                # Pausing the machine is the workaround for a bug that would crash the guest
                # if you take a snapshot while Win Explorer is open, esp with network folders
                self.VBSession.console.pause()
                progress = self.VBSession.console.takeSnapshot(name, desc)
                progress.waitForCompletion(-1)
                self.VBSession.console.resume()
                result = True
          return result

      def _del_snapshot(self, machines, name):
          result = False
          for VM in machines:
              with self.locked(VM) as machine:
                shot = machine.findSnapshot(name)
                progress = self.VBSession.console.deleteSnapshot(shot.id)
                progress.waitForCompletion(-1)
                result = True
          return result

      # Useful really only in the voodo cli. All names are Unicode
      def list_machines(self):
          result = []
          for machine in self.VBMgr.getArray(self.VBox, 'machines'):
            result.append(machine.name)
            print result[-1]
          return result

      # The python sleep function seems to vary in duration.
      # A manual function that blocks for the duration has
      # been much more reliable in allowing VirtualBox the
      # time it needs to kill a machine, and be ready for a
      # restore to snapshot.
      def manual_sleep(self, duration):
          start = time.time()
          while time.time() - duration < start:
            pass

      # Generator style mgr for all the 'with ...' statements
      @contextmanager
      def locked(self, name):
          self.lock.acquire()
          machine = self.VBox.findMachine(name)
          machine.lockMachine(self.VBSession, self.VBConstants.LockType_Shared)
          try:
            yield machine
          finally:
            self.VBSession.unlockMachine()
            self.lock.release()
