import os
import sys
from importlib import import_module


class Job(object):

    def __init__(self, job_scandir, job_cfg):
        self.jobs = job_scandir
        self.cfg = job_cfg
        self.tool = None

    def setup(self):
        self.import_tool()

        dirs = [os.path.join(self.cfg.log, self.cfg.name),
                os.path.join(self.cfg.outputdir, self.cfg.name),
                os.path.join(self.cfg.pcap, self.cfg.name)]

        old_mask = os.umask(0007)

        for d in dirs:
            if d and d != self.cfg.name:
                try:
                    os.makedirs(d, 0770)
                except OSError as e:
                    if e.errno == 17:
                        # Exists
                        pass
                    else:
                        sys.stderr.write("Failed to create logging directories: %s\n\t%s" % (d, e))
                        sys.exit(0)

        os.umask(old_mask)

    def import_tool(self):
        try:
            self.tool = import_module(self.cfg.host_tool)
        except ImportError as e:
            sys.stderr.write("Job failed to import specified tool: %s\n\t%s\n" % (self.cfg.host_tool, e))
            sys.exit(0)


if __name__ == "__main__":
    sys.path.append('/Users/honey/src/Voodo')
    import vo2.vlibs.scandir
    j = Job(vo2.vlibs.scandir.scandir(sys.argv[1]), sys.argv[2])
