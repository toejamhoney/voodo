import os
from vlibs import magic


class SampleSet(object):

    def __init__(self):
        pass


class Sample(object):

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.type = magic.from_file(os.path.join(path, name))
