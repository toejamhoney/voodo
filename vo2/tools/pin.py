import sys
import os
import logging
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
    if not task.init():
        return task

    print 'RUN: %s' % task.sample.name

    pincmd = task.cfg.pincmd.format(pinbat=task.cfg.pinbat, pintool=task.cfg.pintool)

    spoofs = task.cfg.spoofs.split(',')

    for s in spoofs:
        logging.warn(s)
        if not task.vm.guest:
            logging.warn("Setting up VM")
            task.setup_vm(suffix=".%s" % s)

        logging.warn("Loading sample")
        if not task.vm.push_sample(task.sample.path, task.cfg.guestworkingdir):
            sys.stderr.write("Guest pull failed on sample: %s -> %s\n" % (task.sample.path, task.cfg.guestworkingdir))
            sleep(15)
            task.teardown_vm()
            return task

        bincmd = '"%s\\spoofs\\%s" "%s\\%s"' % (task.cfg.guestworkingdir, s, task.cfg.guestworkingdir, task.sample.name)
        cmd = ' -- '.join([pincmd, bincmd])

        logging.warn(cmd)

        rv = task.vm.guest.handle_popen(cmd)
        sleep(10)
        if not rv[0]:
            task.errors = rv[2]
        else:
            print "PIN stdout: %s\n" % rv[1]

        src = '\\'.join([task.cfg.guestworkingdir, task.cfg.pinlog])
        dst = os.path.join(task.cfg.hostlogdir, task.cfg.name, '%s.%s.out' % (task.sample.name, s))
        rv = task.vm.guest.push(src, dst)
        if not rv:
            sys.stderr.write("Guest push failed on loggings: %s -> %s\n" % (src, dst))

        sleep(30)

        task.teardown_vm()

    return task


def callback(task):
    """
    :type task: vo2.work.task.Task
    :param task:
    :return:
    """
    task.complete()
