from catalog.samples import Sample


class Task(object):

    def __init__(self, vm_mgr, name, path, cfg):
        """
        :type cfg: vo2.vcfg.Config
        :type vm_mgr: vo2.guests.gman.GuestManager
        :param cfg:
        :return:
        """
        self.sample = Sample(name, path)
        self.cfg = cfg
        self.mgr = vm_mgr

    def init(self):
        pass

    def complete(self):
        pass
