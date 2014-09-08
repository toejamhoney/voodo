import sqlite3

import vo2.vcfg as cfg


class DatabaseFactory(object):

    def __init__(self):
        self.dbs = {}

    def get_db_gw(self, name, type_):
        if not name in self.dbs:
            path = cfg.Config().setting('database', type_)
            conn = self.__get_conn(type_, path)
            dbgw = DatabaseGateway(conn)
            self.dbs[name] = {'type': type_, 'gw': dbgw}
        return self.dbs.get(name).get('gw')

    def __get_conn(self, type_, path):
        conn = None
        if type_ == 'sqlite3':
            conn = sqlite3.connect(path, timeout=30)
            conn.row_factory = sqlite3.Row
        if type_ == 'postgres':
            raise NotImplementedError
        if type_ == 'neo4j':
            raise NotImplementedError
        return conn


class DatabaseGateway(object):

    def __init__(self, conn):
        """
        :type conn: sqlite3.Connection
        :param conn:
        :return:
        """
        self.error = ''
        self.conn = conn

    def exec_one(self, cmd, params=''):
        try:
            cur = self.conn.cursor()
            if params:
                cur.execute(cmd, params)
            else:
                cur.execute(cmd)
        except Exception as e:
            self.conn.rollback()
            self.error = str(e)
            return None
        else:
            return self.__get_result(cur)

    def exec_many(self, cmd, params):
        try:
            cur = self.conn.cursor()
            cur.executemany(cmd, params)
        except Exception as e:
            self.conn.rollback()
            self.error = str(e)
            return None
        else:
            return self.__get_result(cur)

    def exec_wait(self, cmd, params='', n=30):
        done = None
        tries = 0
        while not done and tries < n:
            tries += 1
            done = self.exec_one(cmd, params)
        return done

    def __get_result(self, cur):
        self.conn.commit()
        rv = cur.fetchall()
        if rv == []:
            rv = True
        cur.close()
        return rv

    def get_error(self):
        err = self.error
        self.error = ''
        return err

    def disconnect(self):
        self.conn.commit()
        self.conn.close()
