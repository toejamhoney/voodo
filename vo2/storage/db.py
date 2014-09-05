import os
import sqlite3

from config import STORAGE

class DBGateway(object):

    def __init__(self, db_type = None):
        self.db_dir = STORAGE.get('DB_DIR')
        if not db_type:
            self.db_name = STORAGE.get('MAIN_DB')
        elif db_type.startswith('job'):
            self.db_name = STORAGE.get('JOB_DB')
        elif db_type.startswith('test'):
            self.db_name = 'test.sqlite'
        elif db_type.startswith('mem'):
            self.db_name = ':memory:'
            self.db_dir = ''
        db_path = os.path.join(self.db_dir, self.db_name)
        #print 'Using:',db_path
        self.db_conn = sqlite3.connect(db_path)
        self.db_curr = self.db_conn.cursor()

    def attach(self, db_name):
        db = "'" + os.path.join(config.SETTINGS.get('DB_DIR'), db_name) + "'"
        self.db_curr.execute('ATTACH DATABASE ' + db + ' AS ' + db_name)
        self.db_conn.commit()

    def create_tbl(self, table, **kwargs):
        try:
            kwargs = self.format_args(**kwargs)
            cmd = 'CREATE TABLE ' + table
            if kwargs.get('select'):
                cmd += ' AS SELECT ' + kwargs.get('select') + ' FROM ' + kwargs.get('from') + ' WHERE ' + kwargs.get('where') + '=' + kwargs.get('is')
            else:
                cmd += ' (' + kwargs.get('cols') + ', PRIMARY KEY(' + kwargs.get('primary') + '))'
        except TypeError as error:
            print 'Invalid arguments passed to database gateway:', kwargs
            raise error
        else:
            print 'FINAL CMD:',cmd
            try:
                self.db_curr.execute(cmd)
            except sqlite3.OperationalError as error:
                print 'Invalid operation in database gateway:', error
                raise error
            else:
                self.db_conn.commit()
                self.dump()

    def drop(self, name):
        self.db_curr.execute("DROP TABLE IF EXISTS " + name)
        self.db_conn.commit()

    def format_args(self, **kwargs):
        if isinstance(kwargs.get('primary'), (tuple, list)):
            kwargs['primary'] = ', '.join(kwargs['primary'])
        if isinstance(kwargs.get('cols'), (tuple, list)):
            kwargs['subs'] = ', '.join( ['?' for arg in kwargs['cols']] )
            kwargs['cols'] = ', '.join(kwargs['cols'])
        else:
            kwargs['subs'] = '?'
        return kwargs
    
    def insert(self, table, **kwargs):
        kwargs = self.format_args(**kwargs)
        cmd = 'INSERT INTO ' + table + '(' + kwargs.get('cols') + ') VALUES (' + kwargs.get('subs') + ')'
        self.db_curr.execute(cmd, kwargs.get('vals'))
        self.db_conn.commit()


    def select(self, table, **kwargs):
        pass

    def update(self, **kwargs):
        kwargs = self.format_args(**kwargs)
        cmd = 'UPDATE :table SET :col = :val WHERE :key = :kval'
        print kwargs
        self.db_curr.execute(cmd, kwargs)
        self.db_conn.commit()

    def delete(self, *ids):
        pass

    def dump(self):
        print ':MEMORY DB DUMP:'
        for val in self.db_conn.iterdump():
            print val
        print ':MEMORY DB DUMP END:'

# Testing
if __name__ == "__main__":
    import threading
    num_threads = 10

    gw = DBGateway('test')
    '''
    table = 'test_table'

    print '-'*20, 'Test Full Iterables', '-'*20
    col = [ "id INT", "date DATETIME", "name TEXT" ]
    prime = ('id', 'name')
    try:
        gw.create_tbl(table, cols=col, primary=prime)
    except Exception as error:
        repr(error)

    print '-'*20, 'Test Singles', '-'*20
    cols = 'id INT'
    primary = 'id'
    kwargs = { 'cols':cols, 'primary':primary }
    try:
        gw.create_tbl(table, **kwargs)
    except Exception as error:
        print repr(error)

    print '-'*20, 'Test Nones', '-'*20
    cols = None
    primary = None
    kwargs = { 'cols':cols, 'primary':primary }
    try:
        gw.create_tbl(table, **kwargs)
    except Exception as error:
        print repr(error)

    print '-'*20, 'Test Mix', '-'*20
    cols = ('id INT', None)
    primary = 'id'
    kwargs = { 'cols':cols, 'primary':primary }
    try:
        gw.create_tbl(table, **kwargs)
    except Exception as error:
        print repr(error)
    '''

    print '-'*20, 'Test Threads', '-'*20
    table = 'thread_table'
    cols = ('thread_id INT', 'value TEXT')
    primary = 'thread_id'
    gw.drop(table)
    gw.create_tbl(table, cols=cols, primary=primary)
    gw.insert(table, cols='thread_id', vals=('all',))

    def work(i):
        db_gw = DBGateway('test')
        stuff = str(i)*100
        db_gw.update(table='thread_table', col='value', val=stuff, key='thread_id', kval='all')

    threads = []
    for i in range(num_threads):
        thr = threading.Thread(target=work, args=(i,))
        threads.append(thr)
        thr.start()

    for thread in threads:
        thread.join()

    gw.dump()

