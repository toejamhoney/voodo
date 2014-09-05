# Python Modules
import os
import json
import sqlite3
from datetime import datetime

# Voodo Modules
import config


class Jobber(object):
    def __init__(self):
        self.db_conn = sqlite3.connect(os.path.join(config.SETTINGS.get('DB_DIR'), 'job_tables.sqlite'))
        self.db_curr = self.db_conn.cursor()
        main_db = "'" + os.path.join(config.SETTINGS.get('DB_DIR'), 'voodo.sqlite') + "'"
        self.db_curr.execute('ATTACH DATABASE ' + main_db + ' AS main_db')
        self.db_conn.commit()
        self.parser = v_parser.JobParser()

    def verify_params(self, params):
        if params:
            return True
        return False

    def add(self, line):
        job_dict = self.parser.parse_args(line)
        new_job = Job(job_dict)
        ret_val = 'Init'
        try:
            job_id = self.insert_job(new_job)
        except (sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            ret_val = 'Failed to add job to database:' + repr(err)
        except Exception as err2:
            print 'ERR:', err2
        else:
            new_job.set('job_id', job_id)
            ret_val = 'Added job to database'
        finally:
            return ret_val

    def insert_job(self, job):
        self.db_curr.execute("SELECT set_id FROM main_db.sample_sets WHERE set_name = '" + job.get('set') + "'")
        self.db_conn.commit()

        data = job.to_JSON()
        row = self.db_curr.fetchone()
        set_id = row[0]
        if not row:
            raise sqlite3.IntegrityError('Invalid sample set name, ' + job.get('set'))
        if not row:
            raise TypeError('Unable to JSON encode job samples')

        try:
            self.db_curr.execute('INSERT INTO main_db.jobs (job_name, set_id, dictionary) VALUES (?, ?, ?)',
                                 (job.job, set_id, data))
            self.db_conn.commit()
            job_id = self.db_curr.lastrowid

            self.db_curr.execute(
                'CREATE TABLE job_{0} AS SELECT * FROM main_db.samples WHERE set_id = {1}'.format(str(job_id),
                                                                                                  str(set_id)))
            self.db_curr.execute(
                'CREATE INDEX idx_{0} ON job_{1}(finished_at, state, sample_id, path)'.format(str(job_id), str(job_id)))
            self.db_curr.execute("INSERT INTO queue (job_id, priority, started_at) VALUES (?, ?, ?)",
                                 (job_id, job.priority, datetime.now()))
            self.db_conn.commit()
        except (Exception, sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            raise sqlite3.OperationalError(repr(err))
        else:
            return job_id

    def get_a_task(self):
        self.db_curr.execute("SELECT job_id FROM queue WHERE finished_at IS NULL ORDER BY priority LIMIT 1")
        row = self.db_curr.fetchone()
        if not row:
            print 'No jobs found in queue'
            return None
        job_id = row[0]

        self.db_curr.execute("SELECT dictionary FROM main_db.jobs WHERE job_id = " + str(job_id))
        row = self.db_curr.fetchone()
        job_params = json.loads(row[0])

        self.db_curr.execute("SELECT sample_id, path, name FROM job_" + str(
            job_id) + " WHERE finished_at IS NULL AND state is NULL LIMIT 1")
        row = self.db_curr.fetchone()
        if not row:
            print 'No sample found in job_' + str(job_id)
            self.db_curr.execute("UPDATE queue SET finished_at = ? WHERE job_id = ?", (datetime.now(), job_id))
            self.db_conn.commit()
            return None
        sample_id = row[0]
        path = row[1]
        name = row[2]

        job_params['job_id'] = job_id
        job_params['sample_id'] = sample_id
        job_params['sample_path'] = path
        job_params['sample_name'] = name
        job_params['host_user'] = config.SETTINGS['HOST_LOG_USERNAME']
        job_params['host_addr'] = config.SETTINGS['HOST_ADDR']
        job_params['host_log_dir'] = config.SETTINGS['LOG_DIR']
        job_params['guest_work_dir'] = config.SETTINGS['GUEST_VOODO_DIR']

        return job_params

    def begin_task(self, id_set):
        self.db_curr.execute("UPDATE job_" + str(id_set[0]) + " SET state=1 WHERE sample_id=" + str(id_set[1]))
        self.db_conn.commit()

    def complete_task(self, id_set):
        self.db_curr.execute(
            "UPDATE job_" + str(id_set[0]) + " SET finished_at=" + str(datetime.now()) + " WHERE sample_id=" + str(
                id_set[1]))
        self.db_conn.commit()


class Job(object):
    def __init__(self, job_dic):
        self.parameters = job_dic
        self.priority = self.parameters.pop('priority')
        self.job = self.parameters.get('job')
        self.set('log_path', self.parameters.get('job'))
        if self.parameters.get('before'):
            self.set('log_path', os.path.join(self.parameters.get('log_path'), 'before'))

    def complete(self):
        pass

    def set(self, key, value):
        self.parameters[key] = value

    def get(self, key):
        return self.parameters.get(key)

    def to_JSON(self):
        return json.dumps(self.parameters)

    def __str__(self):
        return str(self.parameters)


class JobParser(BaseParser):
    def __init__(self):
        super(JobParser, self).__init__()
        self.parser.add_argument('-a', '--analyzers', nargs='*', default=[],
                                 help='optional: specify analyzing tools to be run before and after launch. Options = '
                                      'autorunsc, registry')
        self.parser.add_argument('-b', '--before', action='store_true', default=False,
                                 help='optional: specify this job as creating a before analysis image used in diffs '
                                      'later')
        self.parser.add_argument('--date_stamp', default=datetime.today().strftime('%Y-%m-%d'))
        self.parser.add_argument('-d', '--diff', action='store_true', default=False,
                                 help='optional: specify this job should have a diff run on the logs')
        self.parser.add_argument('-f', '--flag', nargs='*', default=[],
                                 help='optional: flags for exe')
        self.parser.add_argument('--flag2', nargs='*', default=[],
                                 help='optional: flags for exe')
        self.parser.add_argument('--flag3', nargs='*', default=[],
                                 help='optional: flags for exe')
        self.parser.add_argument('-i', '--input', nargs='*', default=[],
                                 help='optional: use with a tool to specify an input file name')
        self.parser.add_argument('-j', '--job', default='no-name_' + datetime.today().strftime('%I-%M-%S'),
                                 help='optional: name for the job that will be run')
        self.parser.add_argument('-l', '--log', action='store_true', default=False,
                                 help='optional: name of log, or white space separated list of log names (from config'
                                      '.py). No entry = no logs')
        self.parser.add_argument('--lib', default='',
                                 help='optional: Specifies a library name (source of sample sets/catalogs)')
        self.parser.add_argument('-m', '--method', default='debug', help='RPC Method to run on guest')
        self.parser.add_argument('-o', '--output', nargs='*', default=[],
                                 help='optional: use with a tool to specify an output file name')
        self.parser.add_argument('--path', default='',
                                 help='optional: Set the path for a library or catalog, for example')
        self.parser.add_argument('-p', '--priority', type=int, default=2,
                                 help='optional: set the priority of the jobs being forked. High = 0, Med(Default) = '
                                      '1, Low = 2')
        self.parser.add_argument('--push_sample', default=False, action='store_true')
        self.parser.add_argument('-r', '--reset', action='store_true', default=False,
                                 help='optional: default is true, tells the driver to reset(kill, restore, '
                                      'start) the guests between forked procs')
        self.parser.add_argument('--results', default={})
        self.parser.add_argument('-s', '--set', default='',
                                 help='optional: Specify a sample set name. A set is a catalog, or sample set of '
                                      'artifacts')
        self.parser.add_argument('-t', '--pin_tool', nargs='*', default=[],
                                 help='optional: dll to be used with pin execution')
        self.parser.add_argument('--time_stamp', default=datetime.today().strftime('%I-%M'))
        self.parser.add_argument('--username', default=config.SETTINGS['LOG_USER'])
        self.parser.add_argument('-v', '--vms', nargs='*', default=[],
                                 help='list of virtual machine names to run job on')
        self.parser.add_argument('-w', '--wait', type=int, default=10,
                                 help='optional argument for a wait time. default is 10')
        self.parser.add_argument('-x', '--exe', nargs='*', default=[],
                                 help='required for launch command: path to file to load/run')

    def post_parse(self, dic):
        dic['exe'] = ' '.join(dic['exe'])
        dic['input'] = ' '.join(dic['input'])
        dic['output'] = ' '.join(dic['output'])
        dic['pin_tool'] = ' '.join(dic['pin_tool'])
        dic['flag'] = ' '.join(dic['flag']).replace('+', '-')
        dic['flag2'] = ' '.join(dic['flag2']).replace('+', '-')
        dic['flag3'] = ' '.join(dic['flag3']).replace('+', '-')
        if not dic['exe'] and dic['input']:
            dic['push_sample'] = True
        return dic

