import sys
import os
import traceback
import logging as log
from threading import Thread
from Queue import Queue, Empty


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
        log.info('%s running %s' % (task.vm.name, s))

        if not task.vm.guest:
            log.debug("Setting up VM: %s" % task.vm.name)
            task.setup_vm(suffix=".%s" % s)

        log.debug("Loading sample")
        if not task.vm.winscp_push(task.sample.path, task.cfg.guestworkingdir):
            log.error("Failed to push sample: %s -> %s\n" % (task.sample.path, task.cfg.guestworkingdir))
            task.teardown_vm()
            return task

        try:
            execution_time = int(task.cfg.exectime)
        except ValueError:
            execution_time = 30

        bincmd = ''
        if 'pdf' in task.sample.type.lower():
            bincmd = '"%s" ' % task.cfg.pdfreader
            execution_time *= 4
        elif 'dll' in task.sample.type.lower():
            bincmd = '"%s\\spoofs\\%s" ' % (task.cfg.guestworkingdir, s)
        bincmd += '"%s\\%s"' % (task.cfg.guestworkingdir, task.sample.name)

        cmd = ' -- '.join([pincmd, bincmd])
        killcmd = 'taskkill /f /t /IM "%s"' % task.sample.name

        log.debug(cmd)

        results_qu = Queue()
        exec_thread = Thread(target=guest_popen, args=(task.vm.guest, cmd, results_qu))
        exec_thread.start()

        log.debug('%s waiting on results. Timeout = %s' % (task.vm.name, execution_time))

        try:
            rv = results_qu.get(True, execution_time)
        except Empty:
            log.debug('%s execution timeout' % task.vm.name)
            task.errors.append('\nExecution time expired: (%s) %s\n' % (task.sample.type, task.sample.name))
            rv = task.vm.guest.handle_popen(killcmd)
        except Exception as e:
            log.debug('%s' % traceback.format_exc())
            log.debug('%s popen thread error: %s' % (task.vm.name, e))
            rv = task.vm.guest.handle_popen(killcmd)

        if not rv[0]:
            log.error("%s\n%s" % (rv[1], rv[2]))
            task.errors.extend(list(rv[1:]))

        src = '\\'.join([task.cfg.guestworkingdir, task.cfg.pinlog])
        dst = os.path.join(task.cfg.hostlogdir, task.cfg.name, '%s.%s.out' % (task.sample.name, s))
        rv = task.vm.winscp_pull(src, dst)
        if not rv:
            task.errors.append('Failed to pull pin log from guest: %s -> %s\n' % (src, dst))
            sys.stderr.write("Failed to pull pin log from guest: %s -> %s\n" % (src, dst))

        task.teardown_vm()

    return task


def guest_popen(guest, cmd, results_qu):
    log.info('Running cmd: %s' % cmd)
    rv = guest.handle_popen(cmd)
    log.debug('CMD results: %s' % rv)
    results_qu.put(rv)


def callback(task):
    """
    :type task: vo2.work.task.Task
    :param task:
    :return:
    """
    task.complete()
