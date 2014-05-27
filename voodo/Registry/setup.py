from distutils.core import setup

import py2exe


t1 = dict(script="reg_read.py",
          dest_base="reg_read",
          uac_info="requireAdministrator")
 
console = [t1]

windows = [{'script': 'reg_read.py',
            'uac_info': 'requireAdministrator',
            },]

setup(
    version = "1.0.0",
    description = "executable with privileges",
    name = "py2exe executable",
    windows = windows,
    console = console,
    )
