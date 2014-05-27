import os
import urllib

import basic_tools
import config
import tool_functions.tool_admin as tool
import tool_functions.web_comm as spiderman


google_trends = config.SEARCH_SETTINGS['GOOGLE_TRENDS']

def get_search_terms(job_dict = None):
    aol_terms = spiderman.get_aol_terms()
    gtrends_terms = spiderman.get_aol_terms(google_trends)
    file_out = open('data_files/search_terms.txt', 'w')
    for term in aol_terms:
      file_out.write(term+'\n')
    for term in gtrends_terms:
      file_out.write(term+'\n')
    file_out.close()

def get_search_urls(job_dict = None):
    try:
      terms_file = open('data_files/search_terms.txt', 'r')
    except Exception as error:
      print error
      return False
    terms = []
    for line in terms_file:
      terms.append(line.rstrip('\n'))
    terms_file.close()
    for term in terms:
      links = spiderman.google_search(term, 3)
      serp_file = open('data_files/serp.txt', 'w')
      for link in links:
        serp_file.write(link + '\n')
      serp_file.close()

def analyze_launch(job_dict, fork_arg=None):
    if fork_arg:
      job_dict['job'] = os.path.join(job_dict.get('job'), urllib.quote_plus(fork_arg))
    print 'Analyzing',job_dict['job'],'on',job_dict['dest_vm']
    tool.create_log_dirs(job_dict)
    job_dict = basic_tools.guest_exec(job_dict, fork_arg)
    if 'registry' in job_dict.get('analyzers'):
      job_dict['method'] = 'shadow'
      basic_tools.guest_exec(job_dict)
    for analyzer in job_dict.get('analyzers'):
      job_dict['method'] = analyzer
      basic_tools.guest_exec(job_dict)
    if 'autorunsc' in job_dict.get('analyzers'):
      job_dict['method'] = 'autorunsc'
      tool.diff_logs(job_dict)
