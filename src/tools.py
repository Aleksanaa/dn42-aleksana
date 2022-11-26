from ipaddress import ip_network, ip_address, IPv4Address, IPv6Address
from itertools import islice
from re import sub as resub
from socket import getaddrinfo
from copy import deepcopy
from re import compile, Pattern
from configparser import ConfigParser
from pathlib import Path


def read_file_list(file_path: str) -> list:
    with open(file_path) as file:
        file_list = [item.strip() for item in file.readlines() if item]
    return file_list


def is_valid_nets(cidrs: list[str]) -> bool:
    for cidr in cidrs:
        try:
            ip_network(cidr)
        except:
            return False
    return True


def is_valid_ips(ips: list[str]) -> bool:
    for ip in ips:
        try:
            ip_address(ip)
        except:
            return False
    return True


def new_ipv4() -> str:
    used_ips = read_file_list("generated/used_ipv4")
    for cidr in read_file_list("config/ipv4_blocks"):
        net = ip_network(cidr)
        for ip in net:
            if ip not in [net[0], net[-1]] and str(ip) not in used_ips:
                return str(ip)
    raise Exception("No ipv4 address available!")


def new_ipv6() -> str:
    used_subnets = read_file_list("generated/used_ipv6")
    for cidr in read_file_list("config/ipv6_blocks"):
        net = ip_network(cidr)
        for subnet in islice(net.subnets(new_prefix=64), 1, None):
            if str(subnet) not in used_subnets:
                return str(subnet)
    raise Exception("No ipv6 address available!")


class Namelook:
    def __init__(self, domain: str) -> None:
        self.ipv4 = None
        self.ipv6 = None
        for result in getaddrinfo(domain, "0"):
            try:
                ip = ip_address(result[4][0])
                if type(ip) is IPv4Address and not self.ipv4:
                    self.ipv4 = ip
                elif type(ip) is IPv6Address and not self.ipv6:
                    self.ipv6 = ip
            except ValueError:
                pass


class Config:
    def __init__(self, file: Path, shared: str = "shared") -> None:
        parser = ConfigParser()
        parser.read(file)
        raw_config = dict(parser.items())
        config = {key: dict(val) for key, val in raw_config.items() if key != "DEFAULT"}
        for val in config.values():
            val = {k: v for k, v in val.items() if v != "none"}
        if shared and shared in config.keys():
            config = {
                key: {**val, **config[shared]}
                for key, val in config.items()
                if key != shared
            }
        self.content = config

    def read_section(
        self,
        section: str,
        included: list[str] = [],
        excluded: list[str] = [],
        convert_ip: list[str] = [],
        filter: dict[str:Pattern] = {},
    ) -> dict[str, str]:
        prepared = {
            key: val
            for key, val in deepcopy(self.content[section]).items()
            if (included and key in included)
            and key not in excluded
            and (filter[key].match(val) if key in filter else True)
        }
        if convert_ip:
            prepared = {
                key: (ip_address(val) if val in convert_ip.items() else val)
                for key, val in prepared
            }
        return prepared


class Artifact:
    def __init__(self, destination: str, node_name: str) -> None:
        self.destination = Path(f"artifacts/{node_name}{destination}")
        self.cache = ""

    def fill(self, template_name: str, pair: dict[str, str]):
        content = Path(f"template/{template_name}").read_text()
        for (key, value) in pair.items():
            if type(value) is str:
                content = content.replace(f"!{key.upper()}!", value.strip('"'))
            elif value == None:
                content = resub(f".*!{key.upper()}!.*\n", "", content)
            else:
                raise Exception("Invalid value!")
        self.cache += content

    def save(self):
        self.destination.parent.mkdir(exist_ok=True, parents=True)
        self.destination.write_text(self.cache)
