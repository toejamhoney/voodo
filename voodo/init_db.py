#******************************************************************#
# WARNING: This init script for the databases will DROP ALL TABLES #
#******************************************************************#
'''
Get db directory from config and connect to it
'''

import os
import sqlite3

import config


db_name = 'voodo.sqlite'
db_dir = config.SETTINGS.get('DB_DIR')

if not db_dir:
    print 'Directory for database not set in config.py. SETTINGS["DB_DIR"] == None'
    exit(1)
if not os.path.isdir(db_dir):
    print 'Invalid location for database in config.py SETTINGS["DB_DIR"]: ' + db_dir
    exit(2)
    
db = os.path.join(db_dir, db_name)

'''
Reset the job tables database
'''
db_conn = sqlite3.connect(os.path.join(db_dir, 'job_tables.sqlite'))
db_curr = db_conn.cursor()

db_curr.execute("SELECT name FROM sqlite_master WHERE type='table'")
rows = db_curr.fetchall()
for row in rows:
    db_curr.execute("DROP TABLE IF EXISTS " + row[0])
    
db_curr.execute("CREATE TABLE queue (job_id INTEGER, priority INTEGER, started_at DATETIME, finished_at DATETIME, PRIMARY KEY(job_id))")
db_curr.execute("CREATE INDEX queue_time_idx ON queue(priority, started_at, finished_at, job_id)")
 
db_conn.commit()
db_conn.close()

'''
Drop tables if they exist
'''
db_conn = sqlite3.connect(db)
db_curr = db_conn.cursor()

db_curr.execute("SELECT name FROM sqlite_master WHERE type='table'")
rows = db_curr.fetchall()
for row in rows:
    db_curr.execute("DROP TABLE IF EXISTS " + row[0])
db_conn.commit()

'''
Create tables
'''
tables = []
tables.append("CREATE TABLE samples (sample_id INTEGER, path TEXT UNIQUE, name TEXT, set_id INTEGER, state INTEGER, finished_at DATETIME, PRIMARY KEY(sample_id))")
tables.append("CREATE TABLE sample_sets (set_id INTEGER, set_name TEXT UNIQUE, set_path TEXT, PRIMARY KEY(set_id))")
tables.append("CREATE TABLE jobs (job_id INTEGER, job_name TEXT UNIQUE, set_id INTEGER, dictionary TEXT, state INTEGER, finished_at DATETIME, PRIMARY KEY(job_id))")
tables.append("CREATE TABLE results (job_id INTEGER, sample_id INTEGER, results TEXT, PRIMARY KEY(job_id, sample_id))")
for create in tables:
    db_curr.execute(create)


'''
Create indices
'''
indices = []
indices.append("CREATE INDEX jobs_finished_idx ON jobs(finished_at)") 
indices.append("CREATE INDEX set_name_idx ON sample_sets(set_name)") 
for index in indices:
  db_curr.execute(index)
  
'''
Commit changes and close
'''
db_conn.commit()

db_conn.close()
