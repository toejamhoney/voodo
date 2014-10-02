import logging as log
import os
import sys

from catalog.samples import Sample


def analyze(task, pincmd, bincmd, execution_time, suffix):
    log.info('%s running %s for %s seconds' % (task.vm.name, suffix, execution_time))
    task.log("\tLYZER TIME: %s\n" % execution_time)

    if not task.vm.guest:
        log.debug("Setting up VM: %s" % task.vm.name)
        task.log("\tLYZER setting up VM: %s\n" % task.vm.name)
        task.setup_vm(suffix=".%s" % suffix)

    log.debug("Loading sample")
    task.log("\tLYZER loading sample: %s\n" % task.sample.name)
    if not task.vm.winscp_push(task.sample.path, task.cfg.guestworkingdir + "\\"):
        log.error("Failed to push sample: %s -> %s\n" % (task.sample.path, task.cfg.guestworkingdir))
        task.log("\tLYZER failed to push sample: %s -> %s\n" % (task.sample.path, task.cfg.guestworkingdir))
        task.teardown_vm()
        return task

    bincmd += '"%s\\%s"' % (task.cfg.guestworkingdir, task.sample.name)
    cmd = ' -- '.join([pincmd, bincmd])

    log.debug("\nEXECUTE on guest: %s\n" % cmd)
    task.log("\tLYZER execute: %s\n" % cmd)
    rv = task.vm.guest.execute(cmd, execution_time, True, task.cfg.guestworkingdir)
    log.debug("\nRETURNED: %s" % rv)
    task.log("\tLYZER retval: %s\n" % rv)

    src = '\\'.join([task.cfg.guestworkingdir, task.cfg.pinlog])
    dst = os.path.join(task.cfg.outputdir, task.cfg.name, '"%s.%s.out"' % (task.sample.name, suffix))
    log.debug("\nPULLING PIN output:\n%s\t->\t%s\n" % (src, dst))
    task.log("\tLYZER pulls from: %s\n\tLYZER pulls to: %s\n" % (src, dst))
    rv = task.vm.winscp_pull(src, dst)
    if not rv:
        task.errors.append('Failed to pull pin log from guest: %s -> %s\n' % (src, dst))
        sys.stderr.write("Failed to pull pin log from guest: %s -> %s\n" % (src, dst))

    task.log("\tLYZER no VM is a match. Tearing it down\n\n")
    task.teardown_vm()


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

    task.log("RUN TASK: %s\n\tPINCMD: %s\n\tSPOOFS:%s\n" % (task.sample.name, pincmd, spoofs))

    try:
        execution_time = int(task.cfg.exectime)
    except ValueError:
        log.error("Run 'exectime' not set in cfg. Exiting.")
        sys.exit(0)

    if task.sample.type is Sample.PDF:
        execution_time *= 3
        bincmd = '"%s" ' % task.cfg.pdfreader
        analyze(task, pincmd, bincmd, execution_time, task.cfg.pdfreader.rpartition('\\')[2])
        task.log("RUN PDF: %s" % task.sample.name)
    elif task.sample.type is Sample.DLL:
        task.log("RUN DLL: %s" % task.sample.name)
        for s in spoofs:
            task.log("RUN SPOOF: %s %s" % (s, task.sample.name))
            bincmd = '"%s\\spoofs\\%s" ' % (task.cfg.guestworkingdir, s)
            log.debug("\nSpoofing: %s for %s sec\n" % (bincmd, execution_time))
            analyze(task, pincmd, bincmd, execution_time, s)
    elif task.sample.type is Sample.EXE:
        bincmd = ''
        analyze(task, pincmd, bincmd, execution_time, '')
    elif task.sample.type is Sample.DOS:
        log.error("Can not analyze MS-DOS executables")
        task.log("RUN FAIL: %s, %s" % (task.cfg.sample.name, task.cfg.sample.filetype))
    else:
        log.error("Unrecognized file type: %s" % task.sample.filetype)
        task.log("RUN FAIL: %s, %s" % (task.cfg.sample.name, task.cfg.sample.filetype))

    task.log("RUN ENDS\n")
    task.close_log()
    return task


def callback(task):
    """
    :type task: vo2.work.task.Task
    :param task:
    :return:
    """
    task.complete()
