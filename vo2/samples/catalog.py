# Python Modules
import sys
import logging
import os
import sqlite3

import config
import v_parser


# Voodo Modules
class Catalog(object):
    
    def __init__(self):
        self.db_conn = None
        self.db_curr = None
        self.parser = v_parser.JobParser()
        self.db_dir = config.SETTINGS.get('DB_DIR')
        if not self.db_dir:
            print 'DB_DIR key not set in config.SETTINGS (config.py)'
            self.db_dir = None
            self.db_path = None
        else:
            self.db_path = os.path.join(self.db_dir, 'voodo.sqlite')
        print 'Using catalog db:',self.db_path

    def connect(self):
        try:
            self.db_conn = sqlite3.connect(self.db_path)
        except ValueError:
            raise ValueError('Catalog does not have DB_DIR set in config.py')
        else:
            self.db_conn.row_factory = sqlite3.Row
            self.db_curr = self.db_conn.cursor()

    def disconn(self):
        self.db_conn.commit()
        self.db_conn.close()

    def parse_arguments(self, split_line):
        return self.parser.parse_args(split_line)
      
    def get(self, cat_name):
        pass
      
    def find(self, sample_name):
        pass

    def list(self):
        self.connect()
        self.db_curr.execute('SELECT * FROM sample_sets')
        rows = self.db_curr.fetchall()
        for row in rows:
            print row['set_name'] + ': ' + row['set_path']
        self.disconn()
      
    def remove(self, path):
        pass
      
    def add(self, args_list):
        self.connect()
        path = args_list[0]
        if not os.path.isdir(path):
            print 'Path must be a directory'
            return
        set_name = path.rpartition('/')[2]
        try:
            self.db_curr.execute('INSERT INTO sample_sets (set_name, set_path) VALUES (?, ?)', [set_name, path])
        except sqlite3.IntegrityError:
            print 'Set already exists by this name'
        else:
            set_id = self.db_curr.lastrowid
            self.refresh(path, set_id)
        finally:
            self.disconn()
    
    def refresh(self, path, set_id):
        for root, dirs, files in os.walk(path):
            samples = []
            for f in files:
                samples.append( (os.path.join(root, f), f, set_id) )
            break
        self.db_curr.executemany('INSERT OR REPLACE INTO samples (path, name, set_id) VALUES (?, ?, ?)', samples)

    def __str__(self):
        return str(self.db_path)


class Sample(object):

    def __init__(self, path):
        self.path = path

