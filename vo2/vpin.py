import os
import sys

from vcfg import Config
from guests import gman
from vlibs.scandir import scandir
from work.scheduler import Scheduler
from work.job import Job


if __name__ == "__main__":
    try:
        job_cfg = Config(name=sys.argv[1])
    except IndexError:
        sys.stderr.write("Job job_cfg file not found: %s\n" % os.path.join('conf', sys.argv[1]))
        sys.exit(0)

    if not job_cfg.parsed:
        sys.stderr.write("Bad job_cfg file failed to parse: %s\n" % os.path.join('conf', sys.argv[1]))
        sys.exit(0)

    if not os.path.isdir(job_cfg.jobdir):
        sys.stderr.write("Argument 'jobdir' is not a directory: %s\n" % job_cfg.jobdir)
        sys.exit(0)

    cfg = job_cfg.namespace()

    samples = scandir(cfg.jobdir)

    job = Job(samples, cfg)
    job.setup()

    gman = gman.GuestManager(Config())

    scheduler = Scheduler(job, gman)
    scheduler.start()
