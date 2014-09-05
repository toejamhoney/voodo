#vim: set fileencoding=utf-8 :

import argparse
import datetime
import glob
import hashlib
import os
import shutil
from subprocess import Popen, PIPE
import sys
import time

import config


class EmuHandler(object):

    """
    The driver that controls all Android Virtual Devices (AVDs) on QEMU Emulators (Emus)

    For the most part this class serves as a wrapper for the Emu objects. It accepts the
    args input, which is a dictionary created from the return of argparse.parse_argument().
    All methods intended to be used from the voodo cli should invoke a method in the handler
    first.

    """

    ini_vars = ['hw.cpu.arch', 'hw.sdCard', 'hw.sdCard.path',
                'disk.cachePartition','disk.cachePartition.path',
                'kernel.path', 'disk.ramdisk.path', 
                'disk.systemPartition.initPath', 'disk.dataPartition.path',
                'avd.name']

    def __init__(self):
        """
        Initialize certain handler settings.

        Finds all avds as determined by the AVD_DIR in the config module. This will usually
        be the default Android SDK install directory (~/.android/avd/). Then creates instances
        of all AVDs in this directory (does not start, just instanciates). After all possible
        emulators are noted then the handler checks if any of these are running, and terminates
        if so since the handler needs to control the process that runs the Emu.

        """
        self.emus = {}
        self.avds_dir = config.SETTINGS['AVD_DIR'].rstrip('/')
        self.find_avds()
        # Iterate through the AVDs in the dictionary and create instances
        for emu in self.emus.keys():
            try:
                self.hatch_emu(emu)
            except IOError as error:
                print 'Error creating object from AVD file:',str(error)
            else:
                if not isinstance(self.emus.get(emu), Emu):
                    print 'Unable to populate instance of AVD:',emu
                    self.emus.pop(emu)
        # Find emulators that may have been running when voodo began
        self.find_running()

    def find_avds(self):
        """Finds all *.avd directories in the AVD_DIR (from config module), and strips to simple name"""
        avds_list = glob.glob(self.avds_dir + '/*.avd')
        avds_list[:] = [ (avd_name.rpartition('/')[2].rstrip('.avd'), None) for avd_name in avds_list ]
        self.emus = dict(avds_list)

    def find_running(self):
        """Finds all running emulators with ps aux, and exits if any are also found in AVD_DIR"""
        running = []
        exit = False
        cmd = 'ps aux | grep emulator'
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        stdout = stdout.split('\n')
        for line in stdout:
            if line.endswith('gpu on'):
                exit = True
                avd_name = line.partition('-avd ')[2].partition(' ')[0]
                if avd_name in self.emus:
                    print 'Please shutdown the AVD, ' + avd_name + ', before launching voodo'
        if exit:
            sys.exit(1)

    def hatch_emu(self, name):
        """
        Creates an Emu[lator] instance.

        Parses the hardware-qemu.ini file in the *.avd directory for all relevant settings, these
        are defined by the class variable ini_vars. These become a dictionary of interesting settings.
        Adds in the AVD's own directory before adding the Emu instance to the emus map, which is: name
        (without .avd) -> emu instance. The settings dictionary is passed to the Emu object init, which
        creates dynamic runtime variables from these settings. You need only add interesting settings
        to the ini_vars list, and they will be created as "self.an_interesting_key" (where periods
        are replaced by underscores).

        Keyword arguments:
        name -- the name (without .avd) of the AVD/Emu object, must be the same as its directory

        """
        avd_dir = os.path.join(self.avds_dir, name + '.avd')
        # Read the android hardware-qemu.ini file for all this avds settings
        with open(os.path.join(avd_dir, 'hardware-qemu.ini') ) as avd_ini:
            opts = { 'avd_dir' : avd_dir }
            for line in avd_ini:
                key, _, value = line.partition(' = ')
                # Make sure this is a setting we care about
                if key in self.ini_vars:
                    value = value.rstrip('\n')
                    key = key.replace('.', '_')
                    if value == 'yes':
                        opts[key] = True
                    elif value == 'no' or value == 'none':
                        opts[key] = False
                    else:
                        opts[key] = value
            self.emus[name] = Emu(opts)

    def parse_arguments(self, line):
        """Accepts the input line from the main module CMD loop, and returns the dictionary of the namespace"""
        # Parser object
        parser = argparse.ArgumentParser()
        # Arguments added to parser
        parser.add_argument('-a', '--apk', default='No APK entered')
        parser.add_argument('-b', '--backup', action='store_true', default=False)
        parser.add_argument('-i', '--input')
        parser.add_argument('-j', '--job', default='No_Job_Name')
        parser.add_argument('-o', '--output')
        parser.add_argument('-p', '--partition', nargs='*', default=['user'])
        parser.add_argument('-r', '--reset', action='store_true', default=False)
        parser.add_argument('-v', '--avd', default='No AVD name entered')
        parser.add_argument('-w', '--wait', type=int, default=30)
        parser.add_argument('-z', '--analyzers', nargs='*', default=None)
        try:
            result = parser.parse_args(line)
            result = vars(result)
        # Argparse doesn't raise exceptions very nicely, so catch the final exit 
        except SystemExit:
            print 'Parsing failed:',line
            result = False
        return result

    def get_avd(self, name):
        """Checks for the existence of an Emu object, returns the object if found

        Keyword Arguments:
        name -- name (without .avd) of the AVD

        """
        result = self.emus.get(name)
        # Is there an AVD by this name?
        if not result:
            print 'Could not find AVD:',name
        return result

    def start(self, args):
        """Starts (optionally resets) an Emu.

        Keyword Arguments:
        args['avd'] -- name (without .avd) passed in from CLI
        args['reset'] -- boolean value, starts emulator with wipe-samples, resetting emu to stock

        """
        emu = self.get_avd(args['avd'])
        if not emu:
            return False
        # Is this AVD already running on an Emu?
        if emu.running:
            print args.get('avd'),'is already marked as running'
            return False
        # Start the emulator
        print 'Hatched An Emu:',emu.avd_name
        emu.launch_emu(args['reset'])

    def stop(self, args):
        """Stops an Emu process, then resets the emu instance

        Keyword Arguments:
        args['avd'] -- name (without .avd) passed in from CLI

        """
        emu = self.get_avd(args['avd'])
        if not emu:
            return False
        # If you have found an emulator
        emu.terminate_emu()
        self.hatch_emu(emu.avd_name)

    def restore(self, args):
        """Restore the Emu to a stock state

        Removes the userdata-qemu.img file; this will cause the emulator to copy over a new
        version of the stock userdata.img on the next start. Same as the emulator -wipe-samples flag.

        Keyword Arguments:
        args['avd'] -- name (without .avd) passed in from CLI
        args['backup'] -- boolean value of whether or not to save existing img files
        args['partition'] -- list of partitions to backup, defined by the emu.img_file_map

        """
        print 'Restoring:',
        emu = self.get_avd(args['avd'])
        if not emu:
            return False
        if emu.running:
            print 'Cannot save running AVD imgs.'
            return False
        print emu.avd_name
        for img_name in args['partition']:
            try:
                if args['backup']:
                    self.backup_img(emu, img_name)
                else:
                    os.remove(emu.img_file_map.get(img_name))
            except (OSError, IOError) as error:
                print 'Restore error:',error
                return False

    def install(self, args):
        """
        Installs an apk file to the specified emulator.

        Takes an AVD name, and an input file path to an APK, and then uses
        the ADB to install the apk. Writes the installed APK to a log file.
        Voodo reads the logs on startup to know what it can run.

        Keyword Arguments:
        args['avd'] -- name (without .avd) of AVD
        args['input'] -- path to an input .apk file

        """
        emu = self.get_avd(args['avd'])
        path = args.get('input')
        install_log_path = os.path.join(emu.avd_dir, 'voodo_installs.csv')
        if not emu or not path:
            return False
        if not os.path.isfile(path):
            print 'Could not find APK file to install:',str(path)
            return False
        apk = Apk(path)
        ret_val = emu.install(apk)
        if not ret_val:
            return False
        with open(install_log_path, 'a') as log_file:
            log_file.write(','.join([apk.friendly_name, apk.src_path, apk.launch_activity]) + '\n')

    def run(self, args):
        """
        Runs an app on the specified AVD.

        Keyword Arguments:
        args['avd'] -- name (without .avd) of the AVD to run app on, from CLI.
        args['apk'] -- name (without .apk) of the app to run. This is NOT the full java style name,
                       but only the filename without .apk
        args['logcat'] -- boolean value, true if logcat should be run on this app

        """
        emu = self.get_avd(args['avd'])
        if not emu:
            return False
        if not emu.running:
            print 'EmuHandler: starting emulator'
            emu.launch_emu(args['reset'])
        job = Job(emu, args['apk'], args['analyzers'], args['job'])
        job.run(args['wait'])

    def compare_hash(self, args):
        """
        Compare the hash signatures of system.img files to check for possible changes.

        The default emu behavior is to create a temp copy of the system.img from the android sdk
        images directory. When an Emu is started a hash signature will be created immediately after
        start; this is the signature that is compared to by this function. If a program were to
        gain root and somehow alter the system partition this method would catch the change. Then
        a backup can be called on the tmp/system.img so it can be analyzed for the exact change.

        Keyword Arguments:
        args['avd'] -- name of the AVD without .avd
        args['partition'] -- name of the partitions to check

        """
        emu = self.get_avd(args['avd'])
        if not emu:
            return False
        if not emu.running and 'system' in args['partition']:
            print 'Cannot check system partition in non-running AVD:',emu.avd_name
            return False
        sys_tmp_hash = emu.compute_sha1('sys_tmp')
        if sys_tmp_hash == emu.system_hash:
            print 'No change'
            return False
        else:
            print 'Image was altered'
            return True

    def backup_img(self, emu, img_name):
        """
        Preserve AVD changes by backing up img files to the LOG_DIR from config module. 
        
        Will not overwrite past backups. This is not intended to be called from the CLI. You can't 
        pass the arguments necessary. 

        """
        print 'Backing up img:',img_name
        index = 65
        stamped_name = img_name + '_' + datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S_')
        src_path = emu.img_file_map.get(img_name)
        backup_path = os.path.join(config.SETTINGS['LOG_DIR'].rstrip('/\\'), emu.avd_name, 'img_files')
        try:
            os.makedirs(backup_path)
        except OSError as error:
            if error.errno == 17:
                pass
            else:
                raise
        backup_path = os.path.join(backup_path, stamped_name)
        while os.path.exists(backup_path + chr(index) + '.img'):
            index += 1
        backup_path += chr(index) + '.img'
        try:
            shutil.move(src_path, backup_path)
        except (OSError, IOError) as error:
            print 'Error creating backup. Image:',img_name,'on AVD:',emu.avd_name
            print '   ',error
            raise
    '''
    def get_adb_devices(self):
        """
        DEAD CODE: lets not put this into use 

        Lists all devices seen by the ADB.

        """
        print 'Getting list of devices from ADB...'
        result = {}
        cmd = 'adb devices'
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        for line in out:
            if line.startswith('emulator'):
                emulator, _, status = line.partition('   ')
                result[emulator] = status
        return result
    '''

class Emu(object):

    def __init__(self, settings):
        # Create local vars from the dictionary, settings
        for key, value in settings.items():
            # Get the dict of this instance of this Emu vars(self)
            # Add to its __dict__ by settings key = value
            vars(self)[key] = value
        # Additional runtime variables not found in the hardware-qemu.ini
        self.busy = True
        self.running = False
        self.process = None
        self.serial = 'emulator-'
        self.system_tmp = ''
        self.adb_port = 0
        self.console_port = 0
        self.system_hash = ''
        self.apks = {}
        self.install_log = ''
        self.get_installed_apps()
        self.img_file_map = {'user': self.disk_dataPartition_path,
                             'system': self.disk_systemPartition_initPath,
                             'cache': self.disk_cachePartition_path,
                             'sys_tmp': self.system_tmp}
        self.tool_cmd_map = {'logcat': 'logcat -f /sdcard/logcat.txt -n 100 -r 1000'}
        self.adb_procs_map = {}
        self.cache_hash = self.compute_sha1('cache')

    def __str__(self):
        """ Retruns the string representation of the Emulator object
        """
        return self.avd_name + ':' + str(vars(self))

    def begin(self, adb_tools):
        for tool in adb_tools:
            cmd = self.tool_cmd_map.get(tool)
            if not cmd:
                return False
            proc, _, _ = self.adb_command(cmd, verbose=True, wait=False)
            self.adb_procs_map[tool] = proc
            
    def end(self, adb_tools=None):
        if not adb_tools:
            adb_tools = self.tool_cmd_map.keys()
        for tool in adb_tools:
            proc = self.adb_procs_map.get(tool)
            if not proc:
                print 'Could not find tool, ' + tool
            proc.terminate()
            proc.communicate()

    def adb_command(self, cmd, verbose=False, wait=True):
        stdout, stderr = (None, None)
        cmd = 'adb -s ' + self.serial + ' ' + cmd
        if verbose:
            print 'CMD:',cmd
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        if wait:
            stdout, stderr = proc.communicate()
            if stdout and verbose:
                print self.serial + '-stdout:',stdout
            if stderr and verbose:
                print self.serial + '-stderr:',stderr
            stdout = stdout.rstrip()
            stderr = stderr.rstrip()
        return proc, stdout, stderr

    def install(self, apk):
        cmd = 'install ' + apk.src_path
        _, stdout, _ = self.adb_command(cmd, verbose=True)
        for line in stdout.split('\n'):
            if line.startswith('Failure'):
                return False
        self.apks[apk.friendly_name] = apk
        return True

    def get_installed_apps(self):
        try:
            log_file = open(os.path.join(self.avd_dir, 'voodo_installs.csv'), 'r')
        except IOError as error:
            if error.errno == 2:
              # File does not exist, probably haven't installed anything to the avd
              pass
            else:
              print 'Raising cane'
              raise error
        else:
            for line in log_file:
                try:
                    name, src, activity = line.split(',')
                except ValueError:
                    print 'Poorly formatted line in install log:', line
                else:
                    self.apks[name] = Apk(src)
            log_file.close()

    def launch_emu(self, reset):
        self.running = True
        # Subprocess prefers lists when not using the shell
        if reset:
            seq = [ 'emulator', '-partition-size', '512', '-avd', self.avd_name, '-gpu', 'on', '-wipe-samples' ]
        else:
            seq = [ 'emulator', '-partition-size', '512', '-avd', self.avd_name, '-gpu', 'on' ]
        self.process = Popen(seq, stdout=PIPE, stderr=PIPE)
        while not self.adb_port or not self.system_tmp:
            self.get_runtime_stats()
        self.check_adb()
        self.wait_for_device()
        self.system_hash = self.compute_sha1('sys_tmp')
        self.create_working_dir()
        self.busy = False

    def create_working_dir(self):
        path = config.SETTINGS.get('ANDROID_WORKING_DIR')
        if not path:
            path = '/samples/voodo'
        cmd = "shell mkdir " + path
        self.adb_command(cmd, verbose=True)

    def check_adb(self):
        cmd = 'devices'
        _, out, err = self.adb_command(cmd)
        for line in out.split('\n'):
            if line.startswith(self.serial):
                return True
        print 'ADB does not appear to detect the new Emu. Attempting restart'
        self.restart_adb()

    def restart_adb(self):
        cmd = 'kill-server'
        self.adb_command(cmd, verbose=True)
        cmd = 'start-server'
        self.adb_command(cmd, verbose=True)

    def wait_for_device(self, cmd='getprop'):
        cmd = 'wait-for-device'
        self.adb_command(cmd)
        cmd = 'shell getprop service.bootanim.exit'
        bootanim = None
        while bootanim != '1':
            time.sleep(2)
            _, bootanim, err = self.adb_command(cmd)
          
    def compute_sha1(self, part_name):
        sha1 = hashlib.sha1()
        chunk_size = 128 * int(sha1.block_size)
        file_path = self.img_file_map.get(part_name)
        with open(file_path, 'rb') as file_desc:
            for chunk in iter(lambda: file_desc.read(chunk_size), b''):
                sha1.update(chunk)
        return sha1.hexdigest()

    def get_apk(self, app_name):
        return self.apks.get(app_name)

    def get_runtime_stats(self):
        cmd = 'lsof -Pp ' + str(self.process.pid) + ' | grep "LISTEN\|/private/tmp/"'
        lsof = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = lsof.communicate()
        if not stdout.startswith('emulator'):
            return False
        stdout = stdout.split('\n')
        for line in stdout:
            if line.endswith('(LISTEN)'):
                self.get_port(line)
            elif '/private/tmp/android' in line:
                self.get_system_tmp(line)

    def get_port(self, line):
        port = line[-13:-9]
        if not self.console_port and int(port) % 2 == 0:
            self.console_port = int(port)
            self.serial += port
        elif not self.adb_port:
            self.adb_port = int(port)

    def get_system_tmp(self, line):
        if not self.system_tmp:
            self.system_tmp = line.partition('/private')[2]
            self.img_file_map['sys_tmp'] = self.system_tmp

    def terminate_emu(self):
        try:
            # Check if the process is running for killing
            self.check_vitals(True)
            # Terminate the process running the emulator
            self.process.terminate()
        except (AttributeError, OSError):
            print self.avd_name,'emu does not have an active process'
        else:
            # Get the Walkers
            self.process.wait()
            # Finalize the termination
            self.check_vitals()

    def check_vitals(self, the_jolly_roger=False):
        # Test if the thread exists by sending signal 0 to PID
        try:
            os.kill(self.process.pid, 0)
        except OSError as error:
            if error.errno == 3:
                # Process does not live, running is therefore false
                self.running = False
                if the_jolly_roger:
                    # Pass the exception on to the terminate emu function
                    raise
        else:
            # If the thread does not clearly exist or not exist, then it is likely a walker
            self.process.poll()

    def run(self, apk_name):
        apk = self.apks.get(apk_name)
        if not apk:
            print 'APK, ' + apk_name + ', not found in Emu running AVD: ' + self.avd_name
            return False
        cmd = 'shell am start ' + apk.launch_activity
        self.adb_command(cmd, verbose=True)
        return True

    def force_stop(self, apk_name):
        apk = self.apks.get(apk_name)
        if not apk:
            print 'APK, ' + apk_name + ', not found in Emu running AVD: ' + self.avd_name
            return False
        cmd = 'shell am force-stop ' + apk.name
        self.adb_command(cmd, verbose=True)


class Apk(object):

    def __init__(self, src_path):
        self.src_path = src_path
        self.friendly_name = self.src_path.rpartition('/')[2].partition('.apk')[0]
        print 'APK Path:',self.src_path
        print 'APK Friendly Name:',self.friendly_name
        self.launch_activity = ''
        self.permissions = []
        self.run_aapt()

    def run_aapt(self):
        cmd = 'aapt dump badging ' + self.src_path
        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if stderr:
            if stderr.startswith('ERROR'):
                print stderr
                return False
        self.parse_aapt_out(stdout)

    def parse_aapt_out(self, stdout):
        stdout = stdout.split('\n')
        for line in stdout:
            if line.startswith('package:'):
                self.get_pkg_details(line)
            elif line.startswith('uses-permission:'):
                self.get_permission(line)
            elif line.startswith('launchable-activity:'):
                self.get_launch_activity(line)

    def get_pkg_details(self, line):
        settings = line[9:].split(' ')
        for setting in settings:
            key, _, value = setting.partition('=')
            vars(self)[key] = value.strip("'")
            print key,':',vars(self)[key]

    def get_permission(self, line):
        self.permissions.append(line.partition(':')[2].strip("'"))
        print self.permissions[-1]

    def get_launch_activity(self, line):
        split = line.partition('name=')[2]
        split = split.partition(' ')[0]
        split = split.strip("'")
        split, _, name = split.rpartition('.')
        self.launch_activity = split + '/.' + name
        print self.launch_activity


class Analyzer(object):
    
    def __init__(self, name, log, emu, app):
        """ Give yourself a name, and pull cmds from config module for name
        """
        self.name = name
        self.log = log
        self.emu = emu
        self.apk = self.emu.get_apk(app)
        self.proc = None
        self.cmds = config.ANALYZER_CMDS.get(name)
        print 'Getting all cmds:',config.ANALYZER_CMDS
        print 'Getting specific:',self.cmds

    def before(self):
        """Start the analyzer's main function
        """
        if self.cmds[0]:
            self.handle_command(self.cmds[0])

    def after(self):
        """Complete the analyzer's main function
        """
        if self.cmds[1]:
            if self.cmds[1].startswith("$KILL"):
                print 'Terminating analyzer process'
                self.proc.kill()
                self.proc.wait()
            else:
                self.handle_command(self.cmds[1])
            
    def cleanup(self):
        """Perform any cleanup functions necessary
        """
        if self.cmds[2]:
            self.handle_command(self.cmds[2])

    def handle_command(self, cmd_str):
        '''Organize the command execution via script or single cmd
        '''
        if cmd_str.startswith('$SCRIPT'):
            print 'Job Run Script Cleanup:',cmd_str
            return self.run_script(cmd_str)
        else:
            print 'Job Run Command Cleanup:',cmd_str
            return self.run_command(cmd_str)

    def run_command(self, cmd_str):
        ''' This is the meat and potatoes of run. All the commands pass through
        here. Even scripts are iterated over with this method
        '''
        try:
            cmd = cmd_str.replace('$LOG_FILE', self.log.full_path)
            cmd = cmd.replace('$AWD', config.SETTINGS.get('ANDROID_WORKING_DIR'))
            cmd = cmd.replace('$APK', self.apk.name)
            print 'Job Run Command:',cmd
        except AttributeError as err:
            print 'Job Run Command: AttributeError', err
            return False
        if cmd.startswith('$ADB '):
            print 'Job Run Command: ADB Command transfer'
            proc, out, err = self.emu.adb_command(cmd[5:], verbose=True, wait=False)
        else:
            print 'Job Run Command: Executing process'
            self.handle_popen(cmd, verbose=True, wait=False)
        return True
    
    def run_script(self, path):
        '''This is called when a $SCRIPT is spec'ed in the config.py module
        '''
        filepath = path.partition(' ')[2]
        if not filepath:
            print 'Error in analyzer $SCRIPT command format: ' + self.cmds[0]
            return False
        if not os.path.exists(filepath):
            print '$SCRIPT file can not be found'
            return False
        with open(filepath, 'r') as f:
            for line in f:
                print 'Job Run Script: Executing',line.rstrip()
                if not self.run_command(line.rstrip()):
                    print 'Error during script execution'
                    print '$SCRIPT:',filepath
                    print 'Line:',line
                    return False

    def handle_popen(self, cmd, myshell=True, verbose=False, wait=False):
        """Takes care of the subprocess.Popen function with params
        """
        if verbose:
            print cmd
        self.proc = Popen(cmd, shell=myshell, stdout=PIPE, stderr=PIPE)
        if wait:
            out,err = self.proc.communicate()
            if verbose and out:
                print 'Analyzer (' + self.name + ') stdout:',out
            if verbose and err:
                print 'Analyzer (' + self.name + ') stderr:',err


class Job(object):

    def __init__(self, emulator, application, analyzers, job_name="untitled_job"):
        """ Creates a job associated with a program, analysis, and emulator
        """
        self.emu = emulator
        self.app = application
        self.name = job_name
        self.lyzer_map = {} 
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        time = datetime.datetime.now().strftime('%H-%M')
        log_path = self.name
        for lyzer in analyzers:
            log = Log(log_path)
            log.set_file_name("_".join( [date + '_at_' + time, self.emu.avd_name, self.name, self.app, lyzer] ))
            self.lyzer_map[lyzer] = Analyzer(lyzer, log, self.emu, self.app)

    def run(self, exec_time):
        """ Executes this job; calls associated functions
        """
        for lyzer in self.lyzer_map.values():
            lyzer.before()
        if self.emu.run(self.app):
            time.sleep(exec_time)
            self.emu.force_stop(self.app)
            for lyzer in self.lyzer_map.values():
                lyzer.after()
                lyzer.cleanup()
            return True
        else:
            return False

class Log(object):
    
    def __init__(self, sub_path):
        self.base_path = config.SETTINGS['LOG_DIR'].rstrip('\\/')
        self.full_dir = os.path.join(self.base_path, sub_path)
        self.make_log_dir()
        self.file_name = ''
        self.full_path = ''

    def make_log_dir(self):
        try:
            os.makedirs(self.full_dir)
        except OSError as error:
            if error.errno == 17:
                pass
            else:
                raise error

    def set_file_name(self, file_name):
        if isinstance(file_name, basestring):
            self.file_name = file_name
            self.full_path = os.path.join(self.full_dir, self.file_name)
        else:
            print 'Incorrect value for log file name'
