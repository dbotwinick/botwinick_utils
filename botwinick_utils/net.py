# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD

from socket import (AF_INET as _INET4, SOCK_DGRAM as _DGRAM, create_connection as _create_connection, error as _socket_error,
                    getfqdn as get_fqdn, socket as _socket)
from uuid import NAMESPACE_DNS as _UUID_NS_DNS, uuid4 as _uuid4, uuid5 as _uuid5


def fqdn_to_host(fqdn):
    if fqdn is None:
        return None
    marker = fqdn.find('.')
    return fqdn[:marker] if marker != -1 else fqdn


def generate_system_uid(force_random=False):
    """
    Generate a UUID hex string either using the FQDN of the host or a randomly generated one.

    This function relies on functionality in the python standard libraries for python 2.5+. So technically,
    this function isn't really necessary, it's just a convenience--i.e. fewer programmer managed imports etc.

    :param force_random: whether to use a random UUID; if false (default), the FQDN of the host will be used
    :type force_random: bool
    :return: 32 character hexadecimal string of the UUID
    :rtype: str
    """
    if force_random:
        return str(_uuid4())
    return str(_uuid5(_UUID_NS_DNS, get_fqdn()))


def get_ipv4(target_host='8.8.8.8', target_port=53):
    s = _socket(_INET4, _DGRAM)
    s.connect((target_host, target_port))
    result = s.getsockname()[0]
    s.close()
    return result


def get_interface_ip(target_host='8.8.8.8', target_port=53):
    s = None
    try:
        s = _create_connection((target_host, target_port))
        result = s.getsockname()[0]
    except _socket_error as _e:
        # fall back to IPv4 version because it doesn't require reachable target, so we'll assume that'll work...
        result = get_ipv4(target_host, target_port)
    finally:
        if s is not None:
            s.close()
    return result
