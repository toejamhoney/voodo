import os
import shlex
import subprocess

import config
import proc_mgmt
import virt_dev
import v_parser


root_cmd = '/usr/bin/VBoxManage'
cmds = {'showvminfo': [root_cmd, 'showvminfo', '', '--machinereadable' ], 'list'        : [ root_cmd, 'list', 'vms' ], }

class VBoxDriver(object):
  
    def __init__(self):
        self.proc_mgr = proc_mgmt.ProcMgr()
        self.vm_map = self.init_vm_map()
        self.parser = v_parser.VBoxParser()

    def parse_arguments(self, line):
        return self.parser.parse_args(line)
   
    def load_cd(self, args):
        file_in = args.get('input')
        if not file_in:
            print 'Error loading cd. Input not specified.'
            return False
        file_in = os.path.expanduser(file_in)
        file_in = os.path.expandvars(file_in)
        iso = self.create_iso(file_in)
        for vm in args.get('machines'):
            self.attach_iso(iso, vm, '0')

    def create_iso(self, path):
        if os.name == 'nt':
            file_name = path.rpartition('\\')[2] + '.iso'
        else:
            file_name = path.rpartition('/')[2] + '.iso'
        path_out = os.path.join(config.SETTINGS['ISO_DIR'].replace(' ','\ '), file_name)
        hdi_cmd = 'hdiutil makehybrid -ov -o ' + path_out + ' ' + path + ' -iso -joliet'
        print hdi_cmd
        proc = subprocess.Popen(hdi_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(subprocess.PIPE)
        if stdout.rstrip():
            print stdout
        if stderr.rstrip():
            print stderr
        return file_name

    def attach_iso(self, iso, vm, device='1'):
        path = os.path.join(config.SETTINGS['ISO_DIR'].replace(' ', '\ '), iso)
        cmd = 'VBoxManage storageattach ' + vm + ' --storagectl "IDE" --port 1 --device ' + device + ' --type dvddrive --medium ' + path
        print cmd
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(subprocess.PIPE)
        if stdout.rstrip():
            print stdout
        if stderr.rstrip():
            print stderr

    def get_vm(self, name):
        if name not in self.vm_map.keys():
            return None
        vm_obj = self.vm_map.get(name)
        if vm_obj.busy:
            return None
        else:
            vm_obj.busy = True
            return name

    def get_vm_map(self):
        return self.vm_map

          
    def return_vm(self, name):
        if name not in self.vm_map.keys():
            return None
        vm_obj = self.vm_map.get(name)
        vm_obj.busy = False

    def start(self, args):
        vms = args.get('machines')
        restore = args.get('restore')
        for vm in vms:
            vm_obj = self.vm_map.get(vm)
            if not vm_obj:
                print "start() could not find VM:",vm
                continue
            if restore and vm_obj.state != 'saved':
                self.restore( [vm,] )
            vm_obj.start()

    def stop(self, args):
        vms = args.get('machines')
        for vm in vms:
          vm_obj = self.vm_map.get(vm)
          if not vm_obj:
                print "stop() could not find VM:",vm
                continue
          vm_obj.poweroff()

    def restore(self, args):
        vms = args.get('machines')
        for vm in vms:
          vm_obj = self.vm_map.get(vm)
          if not vm_obj:
                print "stop() could not find VM:",vm
                continue
          vm_obj.restore()

    def snapshot(self, args):
        vms = args.get('machines')
        action = args.get('action')
        name = args.get('name')
        for vm in vms:
          vm_obj = self.vm_map.get(vm)
          if not vm_obj:
                print "stop() could not find VM:",vm
                continue
          if not action:
                vm_obj.snapshot()
          elif action.startswith('del'):
                vm_obj.snapshot(delete=True, snap_name=name)

    def init_vm_map(self):
        dic = {}
        for vm in self.list_vms():
            new_dev = virt_dev.VBoxMachine(vm)
            if new_dev:
                dic[vm] = new_dev
                new_dev.update_state()
        return dic

    def list_vms(self):
        pid  = self.proc_mgr.execute(cmds['list'])
        out, err = self.proc_mgr.get_output(pid)
        if not out:
            print "Error initializing VM list"
            if err:
              print "Error:",err
            return False
        vm_list = []
        for line in out.split('\n'):
            line = shlex.split(line)
            if line:
                vm_name = line[0]
                vm_list.append(vm_name)
        return vm_list

if __name__ == '__main__':
    driver = VBoxDriver()

