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


try:
    # TODO: Borrowed from pyrra code--finish separating out code from util/support code from pyrra and make that its own library

    # noinspection PyCompatibility
    from ipaddress import (ip_network, IPv4Network, IPv6Network, IPv4Interface, IPv6Interface, ip_interface,
                           collapse_addresses)


    class SubnetGroup(object):
        _nets = None
        _exclude_ipv4_dot1 = True  # exclude xx.xx.xx.1 IPv4 addresses

        def __init__(self, *args):
            """
            Utility on top of python std lib ipaddress interfaces to combine/split subnet

            :param args: networks (either SubnetGroups, strings of CIDR blocks, or IPNetwork instances)
            """
            self._nets = []
            for net in args:
                self.add(net)

        def copy(self):
            return SubnetGroup(*self.children)

        def add(self, new_net: str, allow_hosts=True):
            nets = self._nets
            if isinstance(new_net, (IPv4Network, IPv6Network)):
                pass
            elif isinstance(new_net, SubnetGroup):
                for net in new_net.children:
                    self.add(net)
                return self
            else:
                new_net = ip_network(new_net, strict=not allow_hosts)  # type: IPv4Network

            self._nets = list(collapse_addresses(nets + [new_net]))
            return self

        # noinspection PyCompatibility
        def remove(self, exclude_net, allow_hosts=True):
            nets = self._nets
            if isinstance(exclude_net, (IPv4Network, IPv6Network)):
                pass
            elif isinstance(exclude_net, SubnetGroup):
                for net in exclude_net.children:
                    self.remove(net)
                return self
            else:
                exclude_net = ip_network(exclude_net, strict=not allow_hosts)  # type: IPv4Network

            result = []
            for i, net in enumerate(nets):
                if net.overlaps(exclude_net):
                    if net == exclude_net:
                        continue
                    if exclude_net.subnet_of(net):
                        result.extend(net.address_exclude(exclude_net))
                        continue
                    # manage partial overlap with brute-force (for now), list all addresses and exclude as needed...
                    result.extend(pn := ip_network(addr, strict=False) for addr in net if pn not in exclude_net)
                    pass
                else:
                    result.append(net)

            self._nets = list(collapse_addresses(result))
            return self

        @property
        def children(self):
            return self._nets

        @property
        def children_str(self):
            return [s.compressed for s in self._nets]

        def __contains__(self, item):
            if isinstance(item, str):
                # TODO: create interface and then selectively use address/network depending on prefix len
                item = ip_network(item, strict=False)
            if not isinstance(item, (IPv4Network, IPv6Network)):
                return False
            if (self._exclude_ipv4_dot1 and isinstance(item, IPv4Network) and
                    item.prefixlen == 32 and item.network_address.compressed.split('.')[-1] == '1'):
                return False

            for n in self._nets:
                # this ensures we only compare IP v4 with v4 and v6 with v6
                if type(n) == type(item) and item.subnet_of(n):
                    return True
            return False

        pass


    PRIVATE_LANS = SubnetGroup('10.0.0.0/8', '172.16.0.0/12')
    ALL_PRIVATE_LANS = SubnetGroup('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')
except ImportError:
    pass

try:
    # TODO: Borrowed from pyrra code--finish separating out code from util/support code from pyrra and make that its own library

    import netifaces
    # noinspection PyCompatibility
    from ipaddress import (ip_network, IPv4Network, IPv6Network, IPv4Interface, IPv6Interface, ip_interface,
                           collapse_addresses)


    def system_ip_interfaces(excluded_adapters=('lo',), ipv4=True, ipv6=False, target_adapters=()):
        """
        Return system ip interfaces

        NOTE: requires netifaces package and python 3.3+

        :param excluded_adapters:
        :param ipv4:
        :param ipv6:
        :param target_adapters:
        :return:
        """
        result = []
        interfaces = netifaces.interfaces()
        for iface in interfaces:
            if target_adapters and iface not in target_adapters:
                continue
            elif iface in excluded_adapters:
                continue
            data = netifaces.ifaddresses(iface)
            if ipv4 and netifaces.AF_INET in data:
                for a in data[netifaces.AF_INET]:
                    result.append(IPv4Interface((a['addr'], a['netmask'])))
            if ipv6 and netifaces.AF_INET6 in data:
                for a in data[netifaces.AF_INET6]:
                    result.append(IPv6Interface((a['addr'], a['netmask'])))

        return result


    def get_default_gateway(ipv4=True):
        """
        Return system ip interfaces

        NOTE: requires netifaces package and python 3.3+

        :param ipv4:
        :return: gw_adapter_name, gw_ip
        """
        gw = netifaces.gateways()
        gw_ip, gw_adapter = gw['default'][netifaces.AF_INET if ipv4 else netifaces.AF_INET6]
        return gw_adapter, gw_ip
except ImportError:
    pass
