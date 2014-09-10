import os


def run(name, path):
    print('Run: %s\n' % os.path.join(path, name))
    return name


def callback(arg):
    print('Callback: %s' % arg)
