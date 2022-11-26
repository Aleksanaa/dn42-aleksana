from ipaddress import ip_address, ip_network, IPv4Address, IPv6Network
from pathlib import Path
from itertools import islice
from configparser import ConfigParser


class Ipool4:
    def __init__(self) -> None:
        self.ip_all_file = Path("config/ipv4_blocks")
        self.ip_used_file = Path("generated/used_ipv4")
        self.ip_pool = [
            ip_network(ip.strip()) for ip in self.ip_all_file.open().readlines() if ip
        ]
        self.used_pool = [
            ip_address(ip.strip()) for ip in self.ip_used_file.open().readlines() if ip
        ]

    def pick(self) -> str:
        for net in self.ip_pool:
            for ip in net:
                if ip not in [net[0], net[-1]] and ip not in self.ip_pool:
                    self.mark_used(ip)
                    return str(ip)

    def mark_used(self, ip: IPv4Address):
        self.used_pool.append(ip)
        self.ip_used_file.write_text(str(ip))


class Ipool6:
    def __init__(self) -> None:
        self.ip_all_file = Path("config/ipv6_blocks")
        self.ip_used_file = Path("generated/used_ipv6")
        self.ip_pool = [
            ip_network(ip.strip()) for ip in self.ip_all_file.open().readlines() if ip
        ]
        self.used_pool = [
            ip_network(ip.strip()) for ip in self.ip_used_file.open().readlines() if ip
        ]

    def pick(self) -> str:
        for net in self.ip_pool:
            for subnet in islice(net.subnets(new_prefix=64), 1, None):
                if subnet not in self.used_pool:
                    self.mark_used(subnet)
                    return str(subnet)

    def mark_used(self, ip: IPv6Network):
        self.used_pool.append(ip)
        self.ip_used_file.write_text(str(ip))


def assign(node: str):
    if node not in Path("generated/nodes").stem:
        config = ConfigParser()
        config["main"] = {"my_ipv4": Ipool4.pick(), "my_ipv6": Ipool6.pick()}
        with Path(f"generated/nodes/{node}.conf").open() as config_file:
            config.write(config_file)
            config_file.close()
