#!/usr/bin/python
import Queue
from cmd import Cmd
from contextlib import contextmanager
import inspect
import json
import logging
import logging.handlers
import os
import pprint
import sys
import threading
import time
import traceback

sys.dont_write_bytecode = True

import db_mgmt
import catalog
import config
import proxy
import scheduler
import vbox
import emu

######################################################################
# ## Command Module Class

class VoodoCLI(Cmd):
    def __init__(self, stdin=None):
        # Initialize the command loop and take care of its settings.
        # If the stdin parameter is not the default, None, then clear the prompt
        # and redirect stdin to the file, do not use rawinput (keyboard entry)
        # this provides support for script files
        Cmd.__init__(self, stdin=None)

        # Fancy entry banner. ooooo!
        self.intro = '\n\n'
        self.intro += '-------------------------------------\n'
        self.intro += ' _   __             __       ____  __\n'
        self.intro += '| | / /__  ___  ___/ /__  __/ / /_/ /\n'
        self.intro += '| |/ / _ \/ _ \/ _  / _ \/_  . __/_/\n'
        self.intro += '|___/\___/\___/\_,_/\___/_    __(_)\n'
        self.intro += '     Version: 10e-8      /_/_/\n'
        self.intro += '-------------------------------------\n'

        # If a file has been specified use the file rather than stdin, no prompt
        if stdin is not None:
            self.use_rawinput = False
            self.stdin = stdin
            self.prompt = ''
        else:
            self.prompt = 'voodo!# '

        # Initialize the VirtualBox manager
        self.vm_driver = vbox.VBoxDriver()
        # Initialize the Android Emulator mgr
        #self.emu_herder = emu.EmuHandler()
        self.emu_herder = None
        # Create queues used in forking
        self.job_queue = Queue.PriorityQueue()
        self.vm_queue = Queue.Queue()
        # List of VMs in queue to prevent duplicates, dict > set
        self.vm_pool = {}
        self.vm_pool_size = 0
        # List of processes
        self.children = []
        # List of jobs
        self.jobs = []
        # Pretty Printer for debugging
        self.printer = pprint.PrettyPrinter(indent=4)
        # STDOUT lock
        self.stdout_lock = threading.Lock()
        # self.job_server = servers.Voodo_Server( ('127.0.0.1', 4829), servers.JobRequestHandler)
        # child = multiprocessing.Process(target=self.job_server.serve_forever)
        # child.start()

        # IN DEV 
        # PERSISTENCE
        self.db_gateway = db_mgmt.DBGateway()
        # RPC PROXIES
        self.rpc_proxy = proxy.RPCProxy('jobber')
        # LIBRARY
        self.cat = catalog.Catalog()
        # TASK SCHEDULER ENGINE
        self.scheduler = scheduler.Scheduler(self.db_gateway, self.vm_driver.get_vm_map(), self.rpc_proxy)

    ############################################################################        
    # Framework methods for calling anything else. Default handles every cmd

    # Start method for all cli. Gets first argument == class/obj/method to call
    def default(self, line):
        obj_name, _, cmd_line = line.partition(' ')

        try:
            obj = getattr(self, obj_name)

        except AttributeError:

            if self.rpc_proxy.is_proxy(obj_name):
                method_name, _, line_remainder = cmd_line.partition(' ')
                rpc_server = self.rpc_proxy.get_proxy(obj_name)
                rpc_method = rpc_server.get_method(method_name)
                result = rpc_method(line_remainder)
                print result

            else:
                print obj_name + ' not found'

        else:
            try:
                obj(cmd_line)
            except TypeError as e:
                print 'Invalid command. No arguments found',repr(e)

    # Parses cmd line input to pull out the method 
    def get_method(self, method_class, line):
        method_name, _, line_remainder = line.partition(' ')
        try:
            method = getattr(method_class, method_name)
        except AttributeError:
            print method_name + ' method: not found'
        else:
            return method, line_remainder

    # Parses the remainder of the cmd line after get_method to get args 
    def get_arguments(self, method_class, line):
        try:
            arguments = method_class.parse_arguments(line.split(' '))
        except SystemExit:
            return None
        else:
            return arguments

    # Takes a reference to the method and the args dictionary, calls
    # method from obj 
    def call_method(self, method_ptr, args=None):
        try:
            if args:
                method_ptr(args)
            else:
                method_ptr()
        except SystemExit:
            return
        except Exception:
            traceback.print_exc()

    ##################################################################
    # TODO: VBox and Android methods are basically the same except for the
    # class that does the parsing. Need to combine these
    ##################################################################
    # ## Android Emulator Methods:

    def android(self, line):
        try:
            method, line_remainder = self.get_method(self.emu_herder, line)
        except TypeError:
            return
        arguments = self.get_arguments(self.emu_herder, line_remainder)
        self.call_method(method, arguments)


    ##################################################################
    # ## VirtualBox Methods:

    def vbox(self, line):
        try:
            method, line_remainder = self.get_method(self.vm_driver, line)
        except TypeError:
            return
        arguments = self.get_arguments(self.vm_driver, line_remainder)
        self.call_method(method, arguments)


    ##################################################################
    # Proxy Methods:

    def proxy(self, line):
        cmd, _, remainder = line.partition(' ')
        if cmd == 'add':
            self.rpc_proxy.register_server(remainder)

    ##################################################################
    # Library Methods:

    def catalog(self, line):
        method, line_remainder = self.get_method(self.cat, line)
        if line_remainder:
            arguments = line_remainder.split(' ')
            self.call_method(method, arguments)
        else:
            self.call_method(method)


    def sched(self, line):
        if line == 'start':
            self.scheduler.start()
        if line == 'stop':
            self.scheduler.stop()

    ##################################################################
    # ## Tool Methods:

    def tool(self, line):
        job_dict = self.parse_tool_line(line)
        if not job_dict:
            print 'Empty jobs. Exiting'
            return
        self._do_job(job_dict)

    ##################################################################
    # ## Forked Methods:

    # Forks the specified function to each member of the vm list, given
    # one line of data from specified input file to each
    def fork(self, line):
        job_dict = self.parse_tool_line(line)
        if not job_dict:
            print 'Empty jobs. Exiting'
            return
        module_name = job_dict.get('module_name')
        function = job_dict.get('function')
        # With = if you can successfully import module and function then...
        with self.imported(module_name, function) as module:
            try:
                print 'Found module. Parsing job file...'
                job_args = self.read_job_file(job_dict.get('input'))
                if not job_args:
                    print 'Ending before we begin, failed to read job file'
                    return
                print 'Filling job queue...'
                self.fill_job_queue(job_args, job_dict)
                print 'Filling vm queue...'
                self.fill_vm_queue(job_dict)
                while True:
                    loop_counter = self.job_queue.qsize()
                    self.plock('Remaining Jobs:' + str(loop_counter) + '\n')

                    self.children = [thread for thread in self.children if thread.is_alive()]

                    # Setup job dictionary with new job from queue
                    flag, value = self.get_a_job()
                    if not flag or not value:
                        # If job queue is empty, end the loop
                        break
                    job_dict[flag] = value
                    self.plock('   ' + str(loop_counter) + ': Job Dict [' + str(flag) + '] =' + str(value) + '\n')

                    # Setup a VM for the job, blocking for result
                    vm_name = self.get_a_vm()
                    while not vm_name:
                        vm_name = self.get_a_vm()
                        time.sleep(3)

                    job_dict['dest_vm'] = vm_name
                    job_dict['vms'] = [vm_name, ]
                    self.plock('   ' + str(loop_counter) + ': Job Dict [ dest_vm ] =' + str(job_dict['dest_vm']) + '\n')

                    # Thread this job
                    job_dict['fork'] = True
                    self.jobs.append(job_dict.copy())
                    child_proc = threading.Thread(target=self.job_handle, args=(self.jobs[-1],))
                    self.children.append(child_proc)
                    child_proc.start()
                    self.plock('   ' + str(loop_counter) + ': Started' + str(child_proc) + '\n')

                    # Reset the job dictionary for the next job
                    job_dict.pop('dest_vm')
                    job_dict.pop(flag)

                # Collect all your zombies at the end of loop. (They're not
                # actually zombies)
                self.plock('Waiting for threads to finish...');
                for child in self.children:
                    child.join()
                    self.plock('Child collected:' + str(child) + ', ')
                self.plock(' Done.\n')

            except KeyboardInterrupt:
                return

    def job_handle(self, job_dict):
        job_thread = threading.Thread(target=self._do_job, args=(job_dict,))
        job_thread.start()
        job_thread.join(180)
        if job_thread.is_alive():
            self.reset_vm(job_dict.get('dest_vm'))
        self.plock('Returning ' + job_dict.get('dest_vm') + ' to the VM queue...\n')
        self.vm_queue.put(job_dict.get('dest_vm'))
        if job_dict.get('dest_vm') not in self.vm_pool:
            self.vm_pool[job_dict.get('dest_vm')] = True

    def plock(self, string):
        self.stdout_lock.acquire()
        print string,
        self.stdout_lock.release()

    def _do_job(self, job_dict):
        module = __import__(job_dict.get('module_name'), globals(), locals(), [job_dict.get('function')], 0)
        try:
            module.__dict__[job_dict.get('function')](job_dict)
        # You can import anything to do anything so catching anything
        except SystemExit:
            return None
        except Exception as error:
            self.plock('Error in job:' + str(error) + '\n')
            self.plock('Job Dump:')
            self.printer.pprint(job_dict)
        finally:
            if job_dict.get('fork') and job_dict.get('reset'):
                self.reset_vm(job_dict.get('dest_vm'))
                # self.vm_queue.put(job_dict.get('dest_vm'))
                # if job_dict.get('dest_vm') not in self.vm_pool:
                # self.vm_pool[job_dict.get('dest_vm')] = True


    ##################################################################
    # ## Support Methods:

    def reset_vm(self, vm):
        # self.plock('Resetting ' + str(vm))
        try:
            self.vm_driver.kill({'machines': [vm, ]})
        except Exception as error:
            print 'EXCEPTION KILLING MACHINE:', repr(error)
            pass
        # self.plock('Restoring' + str(vm))
        self.vm_driver.restore({'machines': [vm, ]})
        # self.plock('Starting' + str(vm))
        self.vm_driver.start({'machines': [vm, ]})

    def get_a_vm(self):
        try:
            vm_name = self.vm_queue.get(False)
            self.plock('    Found VM:' + vm_name + '\n')
            return vm_name
        except Queue.Empty:
            return None

    def get_a_job(self):
        try:
            priority, args_tuple = self.job_queue.get(False)
            self.plock('    Found job:' + str(args_tuple[0]) + '=' + str(args_tuple[1]) + '\n')
            return args_tuple[0], args_tuple[1]
        except Queue.Empty:
            return None, None

    def fill_vm_queue(self, job_dict):
        for vm in job_dict.get('vms'):
            # Prevent dupes in queue without popping/pushing everything
            if vm not in self.vm_pool:
                print 'Adding vm to pool:', vm
                self.vm_queue.put(vm)
                self.vm_pool[vm] = True

    def fill_job_queue(self, job_args, job_dict):
        priority = job_dict.get('priority')
        for arg in job_args:
            self.job_queue.put((priority, arg))

    def read_job_file(self, file_name):
        result = []
        try:
            a_file = open(file_name)
        except IOError as error:
            print 'Error opening ' + file_name + ':', repr(error)
            return False
        else:
            with a_file:
                for line_num, a_line in enumerate(a_file):
                    if a_line.startswith('#'):
                        continue
                    flag, _, arg = a_line.partition(' ')
                    if flag and arg:
                        result.append((flag.rstrip(), arg.rstrip()))
                    else:
                        print 'Incorrect formatting in ' + os.path.abspath(file_name) + ' @ line ' + str(
                            line_num) + ':', a_line
                        return False
            return result

    def parse_tool_line(self, line):
        split_line = line.split(" ")
        if len(split_line) < 2:
            print "Incomplete command"
            return None, None, None
        module_name, function = split_line[0].split(".")
        module_name = 'tools.' + module_name
        job_dict = tool_admin.create_job_dict(split_line[1:])
        job_dict['module_name'] = module_name
        job_dict['function'] = function
        if job_dict.get('log'):
            tool_admin.create_log_dirs(job_dict)
        return job_dict

    # Uses the inspect module to get the parameters of method
    def get_required_args(self, method):
        args, varargs, keywords, defaults = inspect.getargspec(method)
        if defaults:
            result = [args, defaults]
        else:
            # Must return an empty dict or len() call will fail on None type
            result = [args, {}]
        return result

    # Checks that the correct amount of parameters for a method call were given
    def verify_arguments(self, arg_list, method):
        result = False
        input_count = len(arg_list)
        method_args, defaults = self.get_required_args(method)
        minimum_arg_count = len(method_args) - len(defaults)
        if minimum_arg_count <= input_count <= len(method_args):
            result = True
        return result

    # Reads the config module for 'non-hidden' objects, and then writes them
    # to reloadable files in /conf so we can update values during run-time
    def parse_config(self):
        for element in config.__dict__:
            # Technically no element in a module is private, however, to be pythonic
            # we should ignore anything starting with an underscore
            if element.startswith('_'):
                continue
            else:
                with open('conf/' + element + '.py', 'w') as json_out_file:
                    # Pretty printing JSON dump to file of current config
                    json.dump(config.__dict__[element], json_out_file, indent=4)

    # Generator style mgr for all the 'with ...' statements
    @contextmanager
    def imported(self, module_name, function):
        module = __import__(module_name, globals(), locals(), [function], 0)
        try:
            yield module
        except ImportError as error:
            print "Tool module import error:", error


    ##################################################################
    # ## Static Methods: exit success at cmds quit and exit, or end of scripts

    def emptyline(self):
        """
        Blank lines are NOPs
        """
        pass

    @staticmethod
    def do_eof(self):
        return True

    @staticmethod
    def do_exit(self):
        return True

    @staticmethod
    def do_quit(self):
        return True


##################################################################
# ## Ye Olde Boilerplate

if __name__ == '__main__':
    # Parse cmd line args
    from v_parser import VoodoParser

    main_parser = VoodoParser()
    args = main_parser.parse_args(sys.argv[1:])

    # Initialize logging
    try:
        debug_level = getattr(logging, args.get('debug').upper())
    except AttributeError:
        print 'Invalid debug level: ' + args.get('debug')
        print 'Options: critical, error, warning, or info'
        sys.exit(1)

    # Create the base logger, and set it to handle all record levels
    logger = logging.getLogger("voodo.main")
    logger.setLevel(logging.DEBUG)

    # File handler will capture all log messages
    log_name = os.path.join(config.SETTINGS.get('LOG_DIR'), "voodo.log")
    file_logger = logging.handlers.RotatingFileHandler(log_name, maxBytes=100000, backupCount=100)
    file_logger.setLevel(logging.DEBUG)
    fileFormat = logging.Formatter(fmt='%(asctime)s:%(name)s:%(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    file_logger.setFormatter(fileFormat)
    logger.addHandler(file_logger)

    # StdErr will only get the user specified level, info by default
    console_logger = logging.StreamHandler()
    console_logger.setLevel(debug_level)
    consoleFormat = logging.Formatter(fmt='%(name)s %(levelname)s: %(message)s')
    console_logger.setFormatter(consoleFormat)
    logger.addHandler(console_logger)

    # Run the program from a script file
    if args.get('input'):
        try:
            inpt = open(args.get('input'), 'rt')
        except:
            print "File not found: ", args.get('input')
        else:
            try:
                VoodoCLI(stdin=inpt).cmdloop()
            except KeyboardInterrupt:
                inpt.close()
                exit()
            finally:
                inpt.close()

    # Run the interactive command loop
    else:
        try:
            VoodoCLI().cmdloop()
        except KeyboardInterrupt:
            exit()
