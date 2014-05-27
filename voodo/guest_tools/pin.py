import os
import config
import utils

def rpc_hook(args):
    args['output'] = config.SETTINGS['MALWARE_DEST']
    args['input'] = args['sample_path']
    args = utils.pull_file(args)
    if args['results']['pull_file']:
        args = launch_pin(args)
    else:
        args['results']['pin_tool.rpc_hook'] = [ False, 'Failed to pull sample' ]
    return args
    
def launch_pin(job_dict):
    job_dict['exe'] = '"' + config.SETTINGS['MALWARE_DEST'].rstrip('/ \\') + '\\' + job_dict.get('input').rpartition('/')[2] + '"'
    pin_tool = job_dict.get('pin_tool')
    if not pin_tool:
        job_dict['results']['Error'] = [ False, 'No pin tool dll specified' ]
        return job_dict
    if pin_tool.startswith('v5'):
        # V5 tool still generates a V3.out log file
        log_name = 'V3.out'
    else:
        log_name = job_dict.get('pin_tool').partition('.')[0] + '.out'
        
    exe_path, exe_name = utils.split_path_name(job_dict.get('exe'))
    exe_name = exe_name.rstrip('"')
    result_name = log_name[:-4] + '_V5_msvc10_winxpsp3_' + exe_name
    kill_cmd = 'taskkill /f /t /IM "' + exe_name + '"'
   
    # Format pin cmd
    job_dict = format_cmd(job_dict)

    # Create results key
    job_dict['results'][result_name] = []
    check = utils.make_dir('c:\\tmp')
    if check:
        job_dict['results'][result_name].append(check)
        job_dict['results'][result_name].append('Failed to create c:\\tmp dir')
        return job_dict

    # Change to tmp dir for *.out result file in a clean plase
    os.chdir('c:\\tmp')

    # Run PIN tool
    ret_val, stdout, stderr = utils.handle_popen(job_dict.get('pin_cmd'), use_shell=True, wait=False)
    job_dict['results'][result_name].extend([ret_val, job_dict.get('pin_cmd')])
    job_dict['results'][result_name].extend([job_dict.get('pin_cmd') + '-STDOUT', stdout])
    job_dict['results'][result_name].extend([job_dict.get('pin_cmd') + '-STDERR', stderr])
    utils.manual_sleep(job_dict.get('wait'))

    # Try and close process started, if ! force close
    ret_val, stdout, stderr = utils.handle_popen(kill_cmd, use_shell=False)
    job_dict['results'][result_name].extend([kill_cmd, ret_val, stdout, stderr])
    if stderr.startswith('ERROR'):
        kill_cmd += ' /f'
        ret_val, stdout, stderr = utils.handle_popen(kill_cmd, use_shell=False)
        job_dict['results'][result_name].extend([kill_cmd, ret_val, stdout, stderr])

    # Send log file back with pscp
    if job_dict.get('log'):
        dst = job_dict.get('out_path')
        utils.manual_sleep(1)
        ret_val, stdout, stderr = utils.pscp_push(log_name, dst)
        job_dict['results'][result_name].extend(['pscp pushed pin output', ret_val, stdout, stderr])
    os.chdir(utils.server_dir)
    return job_dict

    
def format_cmd(job_dict):
    # Add pin flags
    pin_cmd = '"' + config.SETTINGS['PIN_BAT_DIR'].rstrip('\\/') + '\\pin" '
    if job_dict.get('flag'):
        pin_cmd = ' '.join([pin_cmd, job_dict.get('flag'), '-t'])
    else:
        pin_cmd = ' '.join([pin_cmd, '-t'])
    # Add tool flags
    if job_dict.get('flag2'):
        pin_cmd = ' '.join([pin_cmd, '"' + config.SETTINGS['PIN_TOOLS_DIR'].rstrip('\\/') + '\\' + job_dict.get('pin_tool') + '"', job_dict.get('flag2')])
    else:
        pin_cmd = ' '.join([pin_cmd, '"' + config.SETTINGS['PIN_TOOLS_DIR'].rstrip('\\/') + '\\' + job_dict.get('pin_tool') + '"'])
    # Add binary flags
    if job_dict.get('flag3'):
        pin_cmd = ' '.join([pin_cmd, '--', job_dict.get('exe'), job_dict.get('flag3')])
    else:
        pin_cmd = ' '.join([pin_cmd, '--', job_dict.get('exe')])
    job_dict['pin_cmd'] = pin_cmd
    return job_dict
