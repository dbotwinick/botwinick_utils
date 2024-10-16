# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD

from getpass import getuser as _getuser
from os import path as osp, cpu_count
from platform import system as _system


def user_name():
    return _getuser()


def user_home_dir(user=''):
    # TODO: make sure this works, have a fall-back if it doesn't, etc.
    return osp.expanduser('~%s' % user)


def operating_system():
    try:
        return _system().lower()  # note that this only works when there are file descriptors attached for stdout????
    except IOError:
        try:
            from win32process import DETACHED_PROCESS as _
            return 'windows'
        except ImportError:  # TODO: specific support for OSX?
            _ = None
            return 'linux'


# stub for backwards compatibility
available_cpu_count = cpu_count
