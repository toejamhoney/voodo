class Guest(object):

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
