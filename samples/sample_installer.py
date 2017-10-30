from test.installer_interface import InstallerInterface

class SampleInstaller(InstallerInterface):
    def __init__(self, products):
        super(SampleInstaller, self).__init__(products)

    def install(self):
        for product in self.products:
            print 'install product: %s' % product

        return True

    def uninstall(self):
        for product in self.products:
            print 'uninstall product: %s' % product

        return True
