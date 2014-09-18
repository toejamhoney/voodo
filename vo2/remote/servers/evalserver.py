import os
from subprocess import Popen, PIPE
from Queue import Queue
import logging as log

VDIR = "c:\\remote"
EXEDIR = "c:\\remote\\bin"
KEYSDIR = "c:\\keys"
MALDIR = "c:\\malware"
PSCP = '%s' % os.path.join(EXEDIR, "pscp.exe")
KEY = '%s' % os.path.join(KEYSDIR, "voo_priv.ppk")
USER = 'logger'


class EvalServer(object):

    children = {}

    def ping(self):
        return True

    def pull(self, src, dst, dst_addr):
        cmd = '"%s" -r -i "%s" %s@%s:"%s" "%s"' % (PSCP, KEY, USER, dst_addr, src, dst)
        child = Popen(cmd, shell=True)
        child.wait()
        return True

    def push(self, src, dst, dst_addr):
        cmd = '"%s" -i "%s" "%s" %s@%s:"%s"' % (PSCP, KEY, src, USER, dst_addr, dst)
        child = Popen(cmd, shell=True)
        child.wait()
        return True

    def guest_eval(self, src):
        try:
            code_obj = compile(src, "<string>", "exec")
        except (SyntaxError, TypeError) as e:
            return [False, str(e)]
        else:
            rv, msg = self.run_arbitrary_code(code_obj)
            return [rv, msg]

    def run_arbitrary_code(self, code_obj):
        try:
            exec code_obj
        except Exception as e:
            return [False, str(e)]
        return [True, '']

    def execute(self, cmd):
        try:
            if isinstance(cmd, list):
                child = Popen(cmd)
            else:
                child = Popen(cmd, shell=True)
            self.children[child.pid] = child
            return [True, child.pid]
        except (OSError, ValueError) as e:
            return [False, str(e)]

    def terminate(self, pid):
        cmd = 'taskkill /f /t /pid %s' % pid
        return self.handle_popen(cmd)

    def handle_popen(self, cmd, use_shell=True):
        print cmd
        rv = True
        stdout = ''
        stderr = ''
        try:
            child = Popen(cmd, shell=use_shell, stdout=PIPE, stderr=PIPE)
        except (OSError, ValueError) as error:
            rv = False
            stderr = "STDERR: %s" % error
            log.error('%s' % error)
        else:
            stdout, stderr = child.communicate()
            if stdout:
                print stdout
            if stderr:
                print stderr
            if child.returncode:
                rv = False
        return [rv, stdout, stderr]