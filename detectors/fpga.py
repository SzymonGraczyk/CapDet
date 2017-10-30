from detector_interface import *

class FPGADetector(DetectorInterface):
    def detect(self):
        self['fpga_count'] = 0
        self['fpga_buses'] = ''

        if self.__has_lspci():
            self.__get_from_lspci()

    def __get_from_lspci(self):
        path = self.__get_lspci()
        res, rc = execute('%s | grep bcc0' % path)
        if rc != 0:
            print "[ERROR] Error executing lspci: '%s'" % res
            return

        res = res.strip().splitlines()
        self['fpga_count'] = len(res)

        buses = []
        for l in res:
            bus = int(l[:2], 16)
            buses.append('0x%x' % bus)
        self['fpga_buses'] = ','.join(buses)
        
    def __has_lspci(self):
        return not self.which('lspci') is None

    def __get_lspci(self):
        return self.which('lspci')
