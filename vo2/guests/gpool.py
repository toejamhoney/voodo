import time


root_cmd = '/usr/bin/VBoxManage'
cmds = {'showvminfo': [root_cmd, 'showvminfo', '', '--machinereadable'],
        'list': [root_cmd, 'list', 'vms'], }


class GuestPool(object):

    def __init__(self, vm_map):
        self.pool = vm_map
        self.ready = dict(zip(vm_map.keys(), [False for i in vm_map]))

    def acquire(self, names, block=False, timeout=90):
        if block:
            rv = self.wait_on(names, timeout)
        else:
            rv = self.check_on(names)
        return rv

    def release(self, name):
        self.ready[name] = True

    def wait_on(self, names, timeout):
        rv = None
        cnt = 0
        while not rv and cnt < timeout:
            for name in names:
                if self.ready.get(name):
                    self.ready[name] = False
                    rv = self.pool.get(name)
            time.sleep(1)
            cnt += 1
        return rv

    def check_on(self, names):
        rv = None
        for name in names:
            if self.ready.get(name):
                self.ready[name] = False
                rv = self.pool.get(name)
                break
        return rv

    def __str__(self):
        string = 'Pool:'
        for vm in self.ready:
            string += vm + ": " + str(self.ready.get(vm)) + ", "
        return string


if __name__ == '__main__':
    d2 = {'vm1':'a', 'vm2':'b'}
    pool = GuestPool(d2)
    print pool

    poss = ['vm1', 'vm2']
    print 'Acquire 2'
    for i in range(2):
        print pool.acquire(poss)
    pool.release('vm1')
    print 'Released 1'
    print 'Acquire 2'
    for i in range(2):
        print pool.acquire(poss)

    print 'Wait on 1 for 5'
    print pool.acquire(['vm2'], block=True, timeout=5)
