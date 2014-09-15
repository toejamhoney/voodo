import os
from subprocess import Popen, PIPE

VDIR = "c:\\remote"
EXEDIR = "c:\\remote\\bin"
KEYSDIR = "c:\\keys"
MALDIR = "c:\\malware"
PSCP = '%s' % os.path.join(EXEDIR, "pscp.exe")
KEY = '%s' % os.path.join(KEYSDIR, "voo_priv.ppk")
USER = 'logger'
HOST_ADDR = '10.3.3.1'


class EvalServer(object):

    def ping(self):
        return True

    def pull(self, src, dst):
        cmd = '"%s" -r -i "%s" %s@%s:"%s" "%s"' % (PSCP, KEY, USER, HOST_ADDR, src, dst)
        child = Popen(cmd, shell=True)
        child.wait()
        return True

    def push(self, src, dst):
        cmd = '"%s" -i "%s" "%s" %s@%s:"%s"' % (PSCP, KEY, src, USER, HOST_ADDR, dst)
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

    def handle_popen(self, cmd, use_shell=True):
        print cmd
        rv = True
        stdout = ''
        stderr = ''
        try:
            child = Popen(cmd, shell=use_shell, stdout=PIPE, stderr=PIPE)
        except (OSError, ValueError) as error:
            rv = False
            stderr = "STDERR: " + unicode(repr(error))
        else:
            stdout, stderr = child.communicate()
            if stdout:
                print stdout
            if stderr:
                print stderr
            if child.returncode:
                rv = False
        return [rv, stdout, stderr]