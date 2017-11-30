import shutil
import sys
import os

from git import Repo, GitCommandError

from logger.capdet_logger import CapDetLogger

log = CapDetLogger()

class GitOps(object):
    def __init__(self):
        pass

    @staticmethod
    def clone(url, dst, branch=None, force=False):
        if force:
            for f in os.listdir(dst):
                file_path = os.path.join(dst, f)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path): 
                        shutil.rmtree(file_path)
                except Exception as e:
                    log.error("Exception occurred while cleaning folder content: '%s'" % dst)
                    return

        if not os.path.exists(dst) or \
           not os.path.isdir(dst):
            log.error("Invalid destination dir")
            return

        if len(os.listdir(dst)) > 0:
            log.error("Destination dir is not empty")
            return
            
        try:
            if not branch:
                res = Repo.clone_from(url, dst)
            else:
                res = Repo.clone_from(url, dst, branch=branch)
        except GitCommandError as e:
            log.error("Exception occurred in git clone: %s" % e)
            return
        except:
            log.error("Unexpected error: %s" % sys.exc_info()[0])
            raise

    @staticmethod
    def _get_project_name(path):
        return os.path.basename(path)
