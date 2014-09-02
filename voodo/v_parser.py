'''
If started in testing mode (ie python parser.py)
then you won't be able to import config.
'''

import argparse
from datetime import datetime
import sys
import os


try:
    import config
except ImportError:
    class config:
        SETTINGS = {'LOG_USER': 'logger'}


class BaseParser(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser()

    def pre_parse(self, line):
        if not isinstance(line, list):
            line = line.split(' ')
        return line

    def post_parse(self, dic):
        return dic

    def parse_args(self, line):
        line = self.pre_parse(line)
        try:
            result = self.parser.parse_args(line)
            result = vars(result)
        except SystemExit:
            if '-h' in line or '--help' in line:
                return ''
            print 'Parsing failed:', line
            sys.exit(1)
        else:
            result = self.post_parse(result)
            return result

    def sanitize_path(self, path_str):
        try:
            path_str = os.path.expanduser(path_str)
            path_str = os.path.expandvars(path_str)
            path_str = os.path.normpath(path_str)
            path_str = os.path.abspath(path_str)
        except (AttributeError, TypeError):
            print 'Err sanitizing "--input" path'
            path_str = None
        finally:
            return path_str


class VoodoParser(BaseParser):
    def __init__(self):
        super(VoodoParser, self).__init__()
        self.parser.add_argument('-i', '--input', nargs='*', default='', help='Input file to replace stdin')
        self.parser.add_argument('-d', '--debug', default='INFO',
                                 help='Indicates debug level. CRITICAL, ERROR, WARNING (default), INFO, or DEBUG')

    def post_parse(self, dic):
        file_in = dic.get('input')
        if file_in:
            dic['input'] = self.sanitize_path(' '.join(file_in))
        return dic


class VBoxParser(BaseParser):
    def __init__(self):
        super(VBoxParser, self).__init__()
        self.parser.add_argument('-d', '--desc', default='none', help='TODO')
        self.parser.add_argument('--delete', action='store_true', default=False, help='TODO')
        self.parser.add_argument('-n', '--name', nargs=1, default='no_name', help='TODO')
        self.parser.add_argument('-r', '--restore', default=False, action='store_true', help='TODO')
        self.parser.add_argument('-v', '--machines', default=[], nargs='*', help='TODO')
        self.parser.add_argument('-i', '--input', nargs='*', help='TODO')

    def post_parse(self, dic):
        if isinstance(dic['input'], list):
            dic['input'] = ' '.join(dic['input'])
        if isinstance(dic['name'], list):
            dic['name'] = ' '.join(dic['name'])
        return dic




''' 
For testing 
'''
if __name__ == '__main__':
    parser = VBoxParser()
    while True:
        print 'Test VBoxParser input (q to quit):',
        args = raw_input().split(' ')
        if args[0] == 'q':
            break
        print 'VBOXPARSER:', parser.parse_args(args)

    parser2 = JobParser()
    while True:
        print 'Test JobParser input (q to quit):',
        args = raw_input().split(' ')
        if args[0] == 'q':
            break
        print 'JOBPARSER:', parser2.parse_args(args)
