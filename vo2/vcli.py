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

import vcfg
from guests import gman

# #####################################################################
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
        self.intro += '     Version: 10e-7      /_/_/\n'
        self.intro += '-------------------------------------\n'

        # If a file has been specified use the file rather than stdin, no prompt
        if stdin is not None:
            self.use_rawinput = False
            self.stdin = stdin
            self.prompt = ''
        else:
            self.prompt = 'voodo!# '

        self.cfg = vcfg.Config()

        # Guest Manager, gman, will handle all interactions with the guests
        self.gman = gman.GuestManager(self.cfg)

        # Jobber, maintains and accesses a priority queue of jobs for the scheduler

        # Scheduler, handles the runtime analysis job distribution

        # Pretty Printer for debugging
        self.printer = pprint.PrettyPrinter(indent=4)


    # ###########################################################################
    # Framework methods for calling anything else. Default handles every cmd

    # Start method for all cli. Gets first argument == class/obj/method to call
    def default(self, line):
        obj_name, _, cmd_line = line.partition(' ')
        try:
            obj = getattr(self, obj_name)
        except AttributeError as e:
            sys.stderr.write("%s\n" % e)
        else:
            try:
                obj(cmd_line)
            except TypeError as e:
                print 'Invalid command. No arguments found', repr(e)

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


    @staticmethod
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


# #################################################################
# ## Ye Olde Boilerplate

def main(input_=None):
    try:
        VoodoCLI(stdin=input_).cmdloop()
    except KeyboardInterrupt:
        input_.close()
        exit(0)


if __name__ == '__main__':
    # Parse cmd line args
    from v_parser import VoodoParser

    main_parser = VoodoParser()
    args = main_parser.parse_args(sys.argv[1:])

    # Initialize logging
    try:
        debug_level = getattr(logging, args.get('debug').upper())
    except AttributeError:
        sys.stderr.write('Invalid debug level: %s\nValid options: critical, error, warning, info\n' % args.get('debug'))
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
    try:
        input_ = open(args.get('input'), 'rt')
    except IOError:
        sys.stderr.write("No valid script file found. Running interactive\n")
        input_ = None
    finally:
        main(input_)
