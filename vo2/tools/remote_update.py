from glob import glob

DIRECTORY = '/Users/honey/src/Voodo/vo2/remote/servers'

FILES = glob(DIRECTORY + '*.py')

for file in FILES:
