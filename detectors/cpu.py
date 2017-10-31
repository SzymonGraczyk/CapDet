from detector_interface import *

class CPUDetector(DetectorInterface):
    def detect(self):
        self['arch']         = ''
        self['core_count']   = ''
        self['cpu_count']    = ''
        self['model']        = ''
        self['thread_count'] = ''

        if self.__has_lscpu():
            self._get_from_lscpu()

    def _get_from_lscpu(self):
        path = self.__get_lscpu()
        res, rc = execute(path)
        if rc != 0:
            print "[ERROR] Error executing lscpu: '%s'" % res
            return

        lines = res.strip().splitlines()
        self['arch']         = self.__find_param(lines, 'Architecture')
        self['core_count']   = self.__find_param(lines, 'Core(s) per socket')
        self['cpu_count']    = self.__find_param(lines, 'Socket(s)')
        self['model']        = self.__find_param(lines, 'Model name')
        self['thread_count'] = self.__find_param(lines, 'CPU(s)')

    def __has_lscpu(self):
        return not self.which('lscpu') is None

    def __get_lscpu(self):
        return self.which('lscpu')

    def __find_param(self, lines, param):
        for l in lines:
            if l.startswith(param):
                return l.split(':')[1].strip()

        return ''
