# Python Modules
import os
import sqlite3

import samples


class Catalog(object):

    def __init__(self, dbgw):
        """
        :type dbgw: vo2.storage.db.DatabaseGateway
        """
        self.storage = CatalogMapper(dbgw)

    def remove(self, path):
        pass

    def add(self, cmdline):
        path = args_list[0]
        if not os.path.isdir(path):
            print 'Path must be a directory'
            return
        set_name = path.rpartition('/')[2]
        try:
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

    def __str__(self):
        return str(self.db_path)


class CatalogMapper(object):

    def __init__(self, dbgw):
        """
        :type dbgw: vo2.storage.db.DatabaseGateway
        """
        self.dbgw = dbgw

        self.db_curr.execute('INSERT INTO sample_sets (set_name, set_path) VALUES (?, ?)', [set_name, path])

        self.db_curr.executemany('INSERT OR REPLACE INTO samples (path, name, set_id) VALUES (?, ?, ?)', samples)
