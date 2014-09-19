import logging
import sys
import tarfile


def run(task):
    task.init()
    task.setup_vm()

    tar = tarfile.open(task.cfg.tarball, 'w')
    tar.add(task.cfg.hostdir)
    tar.close()
    logging.debug("%s created" % task.cfg.tarball)

    if not task.vm.push_sample(task.cfg.tarball, task.cfg.guestdir):
        logging.error('failed to push sample to %s: %s -> %s' % (task.vm.name, task.cfg.tarball, task.cfg.guestdir))
        sys.exit(1)
    logging.debug("%s pushed to guest: %s -> %s" % (task.vm.name, task.cfg.tarball, task.cfg.guestdir))

    logging.debug("%s eval script %s" % (task.vm.name, task.cfg.update_script))
    src_file = open(task.cfg.update_script, 'r')
    src_code = src_file.read()
    src_code.format(tarball=task.cfg.tarball, guestdir=task.cfg.guestdir)
    src_file.close()
    print src_code
    task.vm.guest.guest_eval(src_code)
