import Queue
import os
import signal
from subprocess import Popen, PIPE
import sys
from threading import Thread


class ProcMgr(object):
    
    def __init__(self):
        self.procs = {}

    def execute(self, cmd, verbose=False, fatal=False):
        cmd_str = cmd
        use_shell = True
        if isinstance(cmd, list):
            cmd_str = ' '.join(cmd)
            use_shell = False
        if verbose:
            print cmd_str
        try:
            proc = Popen(cmd, preexec_fn=os.setsid, shell=use_shell, stdout=PIPE, stderr=PIPE)
        except OSError as error:
            print 'ProcMgr.execute cmd:',cmd_str
            print 'ProcMgr.execute:',error
            if not fatal:
                return -1
            else:
                sys.exit(1)
        else:
            self.procs[proc.pid] = proc
            return proc.pid

    def get_output(self, proc_pid, timeout=180):
        result_qu = Queue.Queue()
        comm_timer = Thread(target = self._communicate, args=(proc_pid, result_qu) )
        comm_timer.start()
        comm_timer.join(timeout)
        if comm_timer.is_alive():
            self.terminate(proc_pid)
            out, err = (None, 'SIGTERM')
            if comm_timer.is_alive():
              self.terminate(proc_pid, kill=True)
              out, err = (None, 'SIGKILL')
        else:
            out, err = result_qu.get()
        return out, err

    def _communicate(self, proc_pid, result_qu):
        proc = self.get_popen_obj(proc_pid)
        out, err = proc.communicate()
        result_qu.put( (out, err) )

    def terminate(self, proc_pid, kill=False):
        if not kill:
          os.killpg(proc_pid, signal.SIGTERM)
        else:
          os.killpg(proc_pid, signal.SIGKILL)

    def get_popen_obj(self, proc_pid):
        proc = self.procs.get(proc_pid)
        if not proc:
          print 'ProcMgr got invalid PID:',proc
          sys.exit(1)
        return proc
