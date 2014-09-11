import sys
import os
from time import sleep


def read_file(filename):
    try:
        fin = open(filename, 'r')
    except IOError as e:
        sys.stderr.write("%s\n" % e)
    else:
        rv = fin.read()
        fin.close()
        return rv


def run(task):
    """
    :type task: vo2.work.task.Task
    :param task:
    :return:
    """
    task.init()

    src = os.path.join(task.sample.path, task.sample.name)
    dst = task.cfg.setting('job', 'guestworkingdir')
    rv = task.vm.guest.pull(src, dst)
    if not rv:
        sys.stderr.write("Guest pull failed on sample: %s -> %s" % (src, dst))
        return task


    src = os.path.join(task.cfg.setting('job', 'guestlogdir'), task.cfg.setting('job', 'pinlog'))
    dst = os.path.join(task.cfg.setting('job', 'hostlogdir'), task.sample.name)
    rv = task.vm.guest.push(src, dst)
    if not rv:
        sys.stderr.write("Guest push failed on logs: %s -> %s" % (src, dst))

    return task


def callback(task):
    """
    :type task: vo2.work.task.Task
    :param task:
    :return:
    """
    task.complete()
