import os
import sys
from ConfigParser import SafeConfigParser


DEFAULT_CFG = './conf/myfirstconf.cfg'
SECTIONS = ['general', 'database', 'network', 'guests']
VMS = ['xp00', 'xp01', 'xp02', 'xp03', 'xp04']

class Config(object):

    def __init__(self, path='', name=''):
        if name:
            cfg_file = os.path.join(path, name)
        else:
            cfg_file = os.path.join(path, DEFAULT_CFG)
        self.parser = SafeConfigParser()
        if not self.parser.read(cfg_file):
            print 'No configuration file found:', cfg_file
            self.new_cfg()

    def new_cfg(self):
        for section in SECTIONS:
            setup = getattr(self, 's_%s' % section)
            setup()
        with open(DEFAULT_CFG, 'w') as new_cfg:
            print 'Creating new config file in CWD:', DEFAULT_CFG
            print 'Please double check the default values before running again:'
            print self
            self.parser.write(new_cfg)
        sys.exit(0)

    def s_general(self):
        sec = 'general'
        self.parser.add_section(sec)

    def s_database(self):
        sec = 'database'
        self.parser.add_section(sec)
        self.parser.set(sec, 'path', os.getcwd())
        self.parser.set(sec, 'user', '')
        self.parser.set(sec, 'pw', '')
        self.parser.set(sec, 'job', 'vo2_jobs.sqlite')
        self.parser.set(sec, 'catalog', 'vo2_catalog.sqlite')
        self.parser.set(sec, 'result', 'vo2_results.sqlite')

    def s_network(self):
        sec = 'network'
        self.parser.add_section('network')
        self.parser.set(sec, 'port', '4828')

    def s_guests(self):
        sec = 'guests'
        self.parser.add_section(sec)
        self.parser.set(sec, 'vms', ','.join(VMS))
        for vm in VMS:
            self.parser.set(sec, '%s_os' % vm, 'win_xp_sp3')
            self.parser.set(sec, '%s_ipv4' % vm, '10.0.0.0')
            self.parser.set(sec, '%s_port' % vm, '4828')

    def setting(self, section='', option=''):
        if not section:
            for s in self.parser.sections():
                if self.parser.has_option(s, option):
                    return self.parser.get(s, option)
        elif self.parser.has_option(section, option):
            return self.parser.get(section, option)
        else:
            return None

    def __str__(self):
        rv = ''
        for sect in self.parser.sections():
            rv += 'Section: %s\n' % sect
            for opt in self.parser.options(sect):
                rv += '\t%s\t=\t%s\n' % (opt, self.parser.get(sect, opt))
        return rv


if __name__ == '__main__':
    cfg = Config()
    print(cfg)
    print('-'*80)
    print(cfg.setting(sys.argv[1], sys.argv[2]))
