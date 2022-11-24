from ipaddress import ip_network, ip_address
from itertools import islice
from re import sub as resub
from os import path, makedirs


def read_file_list(file_path: str) -> list:
    with open(file_path) as file:
        file_list = [item.strip() for item in file.readlines()]
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


def fill_config(filename: str, pair: dict[str, str]) -> str:
    with open(f"template/{filename}") as file:
        content = file.read()
        for (key, value) in pair.items():
            if type(value) is str:
                content = content.replace(f"!{key.upper()}!", value.strip('"'))
            elif value == None:
                content = resub(f".*!{key.upper()}!.*\n", "", content)
            else:
                raise Exception("Invalid value!")
    return content


def save_config(pathname: str, content: str):
    makedirs(path.dirname(pathname), exist_ok=True)
    with open(pathname, "w") as config:
        config.write(content)
        config.close()


print(new_ipv6())
