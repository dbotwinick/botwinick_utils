# author: Drew Botwinick, Botwinick Innovations
# title: miscellaneous path utilities for python 2/3
# license: 3-clause BSD

import codecs
import errno
from hashlib import sha1
from os import environ, listdir, makedirs as _makedirs, path as osp, unlink, utime

try:
    from os import symlink as _symlink
except ImportError:  # TODO: evaluate how we want to handle Windows compatibility for symlinks
    # noinspection PyUnusedLocal
    def _symlink(*args, **kwargs):
        raise OSError()


def path_to_package(path_name):
    return osp.normpath(path_name).replace(osp.sep, '.')


def package_to_path(package_name):
    return osp.normpath(package_name.replace('.', osp.sep))


# noinspection PyDefaultArgument
def _path_split(p, rest=list()):
    h, t = osp.split(p)
    if len(h) < 1:
        return [t] + rest
    if len(t) < 1:
        return [h] + rest
    return _path_split(h, [t] + rest)


# noinspection PyDefaultArgument
def _common_path(l1, l2, common=list()):
    if len(l1) == 0 or len(l2) == 0:  # we ran out of path parts in either l1 or l2
        return common, l1, l2
    if l1[0] != l2[0]:  # we must be done because the first parts of either path don't match
        return common, l1, l2
    return _common_path(l1[1:], l2[1:], common + [l1[0]])  # we've found a common element, recursive call minus common


def relative_path(p1, p2):
    """
    Return the string that should be prepended to files in p1 such that they would be located in p2? I find
    this stuff confusing. Realistically, just try it both ways and find out... One way will be right...

    :param p1: path #1
    :type p1: str | unicode
    :param p2: path #2
    :type p2: str | unicode
    :return: 'path difference' in the form of a string formatted to prepend to a path
    :rtype: str
    """
    common, l1, l2 = _common_path(_path_split(p1), _path_split(p2))
    path_parts = []
    effective_length = len(l1) - l1.count(osp.curdir) - l1.count('')
    # create a list of '../' * number of directories to traverse + left over path components
    if effective_length > 0:
        path_parts += [(osp.pardir + osp.sep) * effective_length]
    if len(l2) > 0:
        path_parts += l2
    return osp.join(*path_parts) if path_parts else ''  # TODO: evaluate path parts empty check...


def symlink(src, target, force=True, relative=True):
    """
    Make a symlink (for operating systems that support it). The default options will remove an existing file if it is in
    the way and will create a relative symlink rather than an absolute symlink.

    :param src: the source file
    :param target:  the destination/target file
    :param force: whether to unlink/remove the target if it already exists. Default is True.
    :param relative: whether to generate a relative to absolute link. Default is True.
    :return: boolean; true if symlink created. false if not. False should only occur due to lack of OS support. Note
    that the function will also return True if the src and target files are the same file.
    """
    # check that the source and target aren't already the same file
    if osp.realpath(src) == osp.realpath(target):
        return True  # return True if the link is already in place / the same inode/entity is read for both files right now

    path_parts = osp.split(src)
    init_path = path_parts[0] if not relative else relative_path(osp.dirname(target), path_parts[0])

    effective_src = osp.join(init_path, path_parts[1])

    if force:
        try:
            unlink(target)
        except OSError:
            pass

    try:
        _symlink(effective_src, target)
    except OSError:
        return False

    return True


def cascade_search(origin_dir, file_target, env_target=None):
    """
    Search for file recursively upwards and returns the contents of the file.
    If the file cannot be found, returns the contents of the given environment variable,
    otherwise returns None

    :param origin_dir: starting directory to walk upwards from
    :param file_target: the file to search for
    :param env_target: the environment variable to fall back on
    """
    # TODO: convert to use os.walk? instead of being recursive?
    for f in listdir(origin_dir):
        if f == file_target:
            with open(osp.abspath(osp.join(origin_dir, file_target))) as d:
                return d.readline().strip(), origin_dir
    parent_dir = osp.abspath(osp.join(origin_dir, osp.pardir))
    if parent_dir != origin_dir:
        return cascade_search(parent_dir, file_target, env_target)
    return (environ[env_target], None) if env_target is not None and env_target in environ else (None, None)


def touch(path, truncate=False, create_directories=False):
    # path = osp.abspath(path)
    if create_directories:
        base_dir = osp.dirname(path)
        if not osp.exists(base_dir):
            makedirs(base_dir)
    with open(path, 'a' if not truncate else 'w'):
        utime(path, None)
    return path


def write(path, content, encoding='utf8'):
    with codecs.open(path, 'w', encoding) as f:
        f.write(content)


def append(path, content, encoding='utf8'):
    with codecs.open(path, 'a', encoding) as f:
        f.write(content)


def hash_file_sha1(file_target, buffer_size=262144):
    hash_alg = sha1()
    with open(file_target, 'rb') as f:
        buf = f.read(buffer_size)
        while len(buf) > 0:
            hash_alg.update(buf)
            buf = f.read(buffer_size)
    return hash_alg.hexdigest()


def makedirs(path):
    try:
        _makedirs(osp.normpath(path))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
