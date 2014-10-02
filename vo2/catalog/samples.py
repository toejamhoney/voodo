from vlibs import magic


class Sample(object):

    EXE = 0
    PDF = 1
    DLL = 2
    DOS = 3

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.filetype = intern('Unknown')
        self.type = 0
        self.set_type(path)

    def set_type(self, path):
        if path:
            self.filetype = magic.from_file(path)
            if 'PDF' in self.filetype:
                self.type = Sample.PDF
            elif 'PE32' in self.filetype:
                if 'DLL' in self.filetype:
                    self.type = Sample.DLL
                else:
                    self.type = Sample.EXE
            elif 'MS-DOS' in self.filetype:
                self.type = Sample.DOS
