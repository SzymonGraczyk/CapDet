class OSInterface(object):
    def __init__(self):
        pass

    def is_installed(self, pkg):
        raise NotImplemented('is_installed method not implemented')

    def install(self, pkgs, force=False):
        raise NotImplemented('install method not implemented')

    def reinstall(self, pkgs):
        raise NotImplemented('reinstall method not implemented')

    def uninstall(self, pkgs):
        raise NotImplemented('uninstall method not implemented')

    def reboot(self):
        raise NotImplemented('reboot method not implemented')

    def shutdown(self):
        raise NotImplemented('shutdown method not implemented')
