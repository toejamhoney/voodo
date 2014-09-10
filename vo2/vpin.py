import os
import sys

from vcfg import Config
from guests import gman
from vlibs.scandir import scandir
from work.scheduler import Scheduler
from work.job import Job

if __name__ == "__main__":
    try:
        arg1 = sys.argv[1]
    except IndexError:
        print('No samples input')
        sys.exit(0)
    else:
        try:
            job_cfg = Config(name=sys.argv[2])
        except IndexError:
            job_cfg = Config(name='job_default')
        if not job_cfg.parsed:
            sys.stderr.write("Job job_cfg file not found: %s" % os.path.join('conf', sys.argv[2]))
            sys.exit(0)
        if not os.path.isdir(arg1):
            sys.stderr.write("Input should be a directory of samples\n")
            sys.exit(0)
        samples = scandir(arg1)
        job = Job(samples, job_cfg)
        if not job.import_tool():
            sys.stderr.write("Could not import specified tool\n")
            sys.exit(0)
        gman = gman.GuestManager(Config())
        scheduler = Scheduler(job, gman)
        scheduler.start()
