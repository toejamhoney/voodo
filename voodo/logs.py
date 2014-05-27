import os
import sys
import logging

import config

class Logger(object):

    def __init__(self, path):
        self.base_path = config.SETTINGS['LOG_DIR']
        self.path = os.path.join(self.base_path, path)
        self.make_dirs(self.path)
        self.logs = {}

    def make_dirs(self, path):
        try:
            os.makedirs(path)
        except OSError as error:
            if error.errno == 17:
                pass
            else:
                raise error
                sys.exit(1)

    def add(self, name, sub_folder=True):
        if sub_folder:
            self.path = os.path.join(self.path, name)
        new_log = Log(self.path, name) 

class Log(object):
    
    def __init__(self, path, name):
        self.path = path
        self.name = name
        self.full_path = os.path.join(self.path, self.name)
        try:
            open(self.full_path, 'a')
        except IOError as error:
            print 'Log creation error:', error
            sys.exit(2)
