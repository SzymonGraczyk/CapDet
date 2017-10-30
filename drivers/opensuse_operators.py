from linux_operators import LinuxOperators, log, execute

class OpenSUSEOperators(LinuxOperators):
    def __init__(self):
        super(OpenSUSEOperators, self).__init__()

    def is_installed(self, pkg):
        cmd = 'rpm -q %s' % pkg
        _, rc = execute(cmd)

        return rc == 0

    def install(self, pkgs, force=False):
        if not pkgs:
            log.warning('No packages to install')
            return

        if type(pkgs) != list:
            pkgs = [pkgs]

        log.msg("Installing packages: '%s'" % ' '.join(pkgs))

        cmd = "sudo zypper install -y %s%s" % ('-f ' if force else '', ' '.join(pkgs))
        res, rc = execute(cmd)
        if rc != 0:
            log.error("Error installing packages: '%s'" % res)
            return
            
        log.msg("Packages installed: '%s'" % ' '.join(pkgs))

    def reinstall(self, pkgs):
        self.install(pkgs, True)

    def uninstall(self, pkgs):
        if not pkgs:
            log.warning('No packages to uninstall')
            return

        if type(pkgs) != list:
            pkgs = [pkgs]

        log.msg("Uninstalling packages: '%s'" % ' '.join(pkgs))

        cmd = "sudo zypper remove -y %s" % ' '.join(pkgs)
        res, rc = execute(cmd)
        if rc != 0:
            log.error("Error uninstalling packages: '%s'" % res)
            return
            
        log.msg("Packages uninstalled: '%s'" % ' '.join(pkgs))

