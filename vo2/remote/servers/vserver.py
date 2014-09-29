import os
from subprocess import Popen, PIPE
import logging as log


class VServer(object):

    children = {}

    @staticmethod
    def ping():
        return True

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

    def handle_popen(self, cmd, use_shell=True):
        print cmd
        rv = True
        try:
            child = Popen(cmd, shell=use_shell, stdout=PIPE, stderr=PIPE)
        except (OSError, ValueError) as error:
            rv = False
            stdout = ''
            stderr = "handle_popen error: %s" % error
            log.error('%s' % error)
        else:
            stdout, stderr = child.communicate()
            if stdout:
                log.info(stdout)
            if stderr:
                log.info(stderr)
            if child.returncode:
                rv = False
        return [rv, stdout, stderr]


class EvalServer(VServer):

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
