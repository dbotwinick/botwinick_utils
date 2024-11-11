from __future__ import annotations

import pathlib
import importlib.util


def read_pkg_version(pkg_name, pkg_path: str | pathlib.Path, file='__init__.py'):
    """
    Read version information from importable module/package

    :param pkg_name: name of package/module
    :param pkg_path: path (directory) to package/module
    :param file: specific file to load (defaults to __init__.py)
    :return: version information or raises
    """
    spec = importlib.util.spec_from_file_location(pkg_name, pathlib.Path(pkg_path) / file)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except FileNotFoundError:
        raise ValueError(f'no version info for {pkg_name}')
    if not hasattr(m, '__version__'):
        raise ValueError(f'no version info for {pkg_name}')

    version = m.__version__
    return version
