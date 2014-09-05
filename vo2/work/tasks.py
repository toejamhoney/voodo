import os
import sqlite3
import logging

from config import SETTINGS as settings

class Task(object):

    def __init__(self, dic, vm_name):
        dic['results'] = {}
        self.job_dic = dic
        self.proceed = True
        self.job_dic['dest_vm'] = vm_name
        self.name = '_'.join( [vm_name, dic.get('sample_name')] )

        out = '.'.join([self.job_dic.get('dest_vm') + '-sp3', 'v5-msvc10', self.job_dic.get('sample_name'), 'out'])
        err = '.'.join([self.job_dic.get('dest_vm') + '-sp3', 'v5-msvc10', self.job_dic.get('sample_name'), 'err'])

        oldmask = os.umask(0007)
        log_dir = os.path.join(settings.get('LOG_DIR'), dic.get('job'))
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except os.error:
                self.proceed = False
        os.umask(oldmask)

        self.job_dic['out_path'] = os.path.join(log_dir, out)
        self.job_dic['err_path'] = os.path.join(log_dir, err)

        self.log_path = os.path.join(log_dir, dic.get('err_path'))
        fileFormat = logging.Formatter(fmt='%(asctime)s:%(name)s:%(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

        logHandler = logging.FileHandler(self.log_path)
        logHandler.setLevel(logging.DEBUG)
        logHandler.setFormatter(fileFormat)

        self.logger = logging.getLogger(self.name)
        self.logger.addHandler(logHandler)

        self.log("Task created, init log")

    def setArg(self, key, value):
        if key in self.job_dic:
            self.log("Updating key: " + str(key))
            self.log("   Old value: " + str(self.job_dic.get(key)))
            self.log("   New value: " + str(value))
        else:
            self.log("Adding key: " + str(key) + " = " + str(value))
        self.job_dic[key] = value

    def getArg(self, key):
        return self.job_dic.get(key)

    def logResults(self):
        pass

    def log(self, msg, level='DEBUG'):
        level = level.upper()
        if level == "CRITICAL":
            self.logger.critical(msg)
        elif level == "ERROR":
            self.logger.error(msg)
        elif level == "WARNING":
            self.logger.warning(msg)
        elif level == "INFO":
            self.logger.info(msg)
        else:
            self.logger.debug(msg)
