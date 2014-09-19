import os
import Queue
import signal
import sys
import logging as log
from subprocess import Popen, PIPE
from threading import Thread


class ProcMgr(object):
    
    def __init__(self):
        self.devnull = open(os.devnull, 'w')
        self.procs = {}

    def exec_quiet(self, cmd):
        use_shell = True
        if isinstance(cmd, list):
            use_shell = False
        try:
            proc = Popen(cmd, shell=use_shell)
        except OSError as e:
            log.error('exec_null error: %s\n\tcmd: %s' % (e, cmd))
            return 1
        else:
            rc, out, err = self.cleanup_proc(proc, 10)
            return rc

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
            print 'ProcMgr.execute cmd:', cmd_str
            print 'ProcMgr.execute:', error
            if not fatal:
                return -1
            else:
                sys.exit(1)
        else:
            self.procs[proc.pid] = proc
            return proc.pid

    def get_output(self, pid, timeout=180):
        rc, out, err = self.cleanup_proc(self.get_popen_obj(pid), timeout, True)
        return out, err

    def end_proc(self, pid):
        rv = 'SIGTERM'
        proc = self.get_popen_obj(pid)
        os.killpg(pid, signal.SIGTERM)
        if proc.poll() is None:
            os.killpg(pid, signal.SIGKILL)
            rv = 'SIGKILL'
        return rv

    def cleanup_proc(self, proc, timeout, output=False):
        results = Queue.Queue()
        if output:
            target_handle = self._communicate
        else:
            target_handle = self._join
        t = Thread(target=target_handle, args=(proc, results))
        t.start()
        t.join(timeout)
        if t.is_alive():
            rc = 0
            out = ''
            err = self.end_proc(proc.pid)
        else:
            rc, out, err = results.get()
        return rc, out, err

    def get_popen_obj(self, proc_pid):
        proc = self.procs.get(proc_pid)
        if not proc:
            print 'ProcMgr got invalid PID:',proc
            sys.exit(1)
        return proc

    @staticmethod
    def _communicate(proc, result_qu):
        out, err = proc.communicate()
        result_qu.put((proc.poll(), out, err))

    @staticmethod
    def _join(proc, result_qu):
        proc.wait()
        result_qu.put((proc.poll(), '', ''))
