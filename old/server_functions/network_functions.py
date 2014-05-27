import os
import signal
import subprocess

import config
import functions
import tools.tool_functions.web_comm as spiderman


#################################################################################
#### Global var
# For tcpdump functions
pid = 9999
vm_addrs = config.GUESTS


#################################################################################
#### Job Functions

def download_source_code(job_dict):
    url = job_dict['url']
    urls = spiderman.check_redirects(url, guest=True)
    ret_val = '<!--Original URL:'+url+'-->\n'
    for url in urls:
      ret_val += '<!--Destination URL:'+url+'-->\n'
    html = spiderman.get_HTML(url, guest=True)
    try:
      ret_val = html.decode('ascii')
    except UnicodeDecodeError:
      print 'Not ASCII'
      try:
        ret_val = html.decode('utf8')
        print ret_val
      except UnicodeDecodeError:
        print 'Not UTF8'
    return ret_val

def server_status(job_dict):
    job_dict['results']['server_status']=['', True]
    return job_dict


#################################################################################
#### Gateway Functions

def tcpdump_start(job_dict):
    log_dir = config.SETTINGS['LOG_DIR']
    path, name = functions.split_path_name(log_dir)
    prefix = r'/media/sf_' + name
    path = os.path.join(prefix , job_dict['dest_vm'], job_dict['date_stamp'], job_dict['job'], job_dict['job']+'.pcap')
    pcap_cmd = r'/usr/sbin/tcpdump -ennSvXXs 1514 -i eth1 -w ' + path 
    print pcap_cmd
    try:
        pcap_process = subprocess.Popen(pcap_cmd, shell=True)
    except Exception as error:
        print error
        job_dict['results']['tcpdump_start'] = ['', False]
    else:
        global pid
        pid = pcap_process.pid
        job_dict['results']['tcpdump_start'] = ['', True]
    return job_dict

def tcpdump_stop(job_dict):
    try:
      os.kill(pid, signal.SIGKILL)
      job_dict['results']['tcpdump_stop'] = ['', True]
    except Exception as error:
      print error
      job_dict['results']['tcpdump_stop'] = ['', False]
    return job_dict
