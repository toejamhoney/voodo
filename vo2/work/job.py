import sys
from importlib import import_module

from catalog.samples import Sample


class Job(object):

    def __init__(self, job_scandir, job_cfg):
        self.jobs = job_scandir
        self.cfg = job_cfg
        self.tool = None

    def import_tool(self):
        try:
            self.tool = import_module(self.cfg.setting('job', 'host_tool'))
        except ImportError as e:
            sys.stderr.write("%s\n" % e)
            return False
        else:
            return True


if __name__ == "__main__":
    sys.path.append('/Users/honey/src/Voodo')
    import vo2.vlibs.scandir
    j = Job(vo2.vlibs.scandir.scandir(sys.argv[1]), sys.argv[2])
