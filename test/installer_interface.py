class InstallerInterface(object):
    products = None

    def __init__(self, products):
        self.products = products

    def install(self):
        raise NotImplementedError("install not implemented")

    def uninstall(self):
        raise NotImplementedError("uninstall not implemented")
