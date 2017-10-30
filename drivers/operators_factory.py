import platform

from opensuse_operators import OpenSUSEOperators
from os_interface import OSInterface
from singleton import Singleton

class OperatorsFactory(object):
    __metaclass__ = Singleton

    _operators = None

    def __init__(self):
        super(OperatorsFactory, self).__init__()

    def __get_os(self):
        os = platform.system().strip()
        if os == 'Linux':
            distro = platform.linux_distribution()[0].strip().lower()

            if distro == 'opensuse':
                self._operators = OpenSUSEOperators()
            elif distro == 'rhel':
                self._operators = RHELOperators()
            elif distro == 'ubuntu':
                self._operators = UbuntuOperators()

    def operators(self):
        if not self._operators:
            self.__get_os()

        return self._operators
