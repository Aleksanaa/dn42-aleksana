from src.tools import Config, Namelook
from src.artifact import System
from pathlib import Path
from collections import defaultdict
from ipaddress import (
    IPv4Address,
    IPv6Address,
    AddressValueError,
    ip_network,
    ip_address,
)
from re import match as rematch

allowed_attributes = [
    "asn",
    "link_local",
    "ipv4",
    "ipv6",
    "address",
    "port",
    "pubkey",
    "pskey",
]

dn42_ipv4 = [
    "172.20.0.0/14",
    "172.21.0.0/24",
    "172.22.0.0/24",
    "172.23.0.0/24",
    "10.127.0.0/16",
]

dn42_ipv6 = ["fd00::/8", "fd42:d42:d42::/48"]


class Check:
    def __init__(self, file: Path) -> None:
        self.config = Config(file).content
        self.log = defaultdict(lambda: defaultdict(list))
        self.system = System()
        self.filename = file.stem

    def is_valid_filename(self):
        filename_regex = "^[a-z0-9_]{4,11}$"
        if not rematch(filename_regex, self.filename):
            self.log["error"]["invalid_filename"].append(self.filename)

    def only_valid_section(self):
        for section in self.config:
            if section not in self.system.instances.keys():
                self.log["error"]["no_instance"].append(section)
                del self.config[section]

    def only_valid_attr(self):
        for section in self.config.values():
            for key in section:
                if key not in allowed_attributes:
                    self.log["error"]["invalid_attr"].append(key)

    def missing_and_dup(self):
        for name, section in self.config.items():
            if "asn" not in section:
                self.log["error"]["missing_asn"].append(name)
            if "pubkey" not in section:
                self.log["erorr"]["missing_pubkey"].append(name)
            if "link_local" in section and ("ipv4" in section or "ipv6" in section):
                self.log["warning"]["ignoring_dn42_ip"].append(name)
            if "port" in section and "address" not in section:
                self.log["error"]["alone_port"].append(name)
            if (
                "link_local" in section
                and "asn" in section
                and section["link_local"] == f"fe80::{section['asn'][-4:].lstrip('0')}"
            ):
                self.log["note"]["link_local_can_ignore"].append(section["link_local"])
            if "port" in section and section["port"] == str(
                20000 + int(self.system.asn[-4:])
            ):
                self.log["note"]["port_can_ignore"].append(section["port"])
            if "asn" in section and "address" in section and "port" not in section:
                self.log["note"]["alone_address"].append(name)
            if (
                "asn" in section
                and "link_local" not in section
                and "ipv4" not in section
                and "ipv6" not in section
            ):
                self.log["note"]["default_link_local"].append(name)
            if "port" not in section and "address" not in section:
                self.log["note"]["passive_connect"].append(name)
            if "pskey" in section:
                self.log["warning"]["pskey_not_recommended"].append(name)

    def is_valid_dn42_ipv4(self, ipv4: str):
        dn42_net4 = [ip_network(ip) for ip in dn42_ipv4]
        try:
            is_valid = False
            for net in dn42_net4:
                if IPv4Address(ipv4) in net:
                    is_valid = True
            if not is_valid:
                self.log["error"]["invalid_dn42_ipv4"].append(ipv4)
        except AddressValueError:
            self.log["error"]["invalid_dn42_ipv4"].append(ipv4)

    def is_valid_dn42_ipv6(self, ipv6: str):
        dn42_net6 = [ip_network(ip) for ip in dn42_ipv4]
        try:
            is_valid = False
            for net in dn42_net6:
                if IPv4Address(ipv6) in net:
                    is_valid = True
            if not is_valid:
                self.log["error"]["invalid_dn42_ipv6"].append(ipv6)
        except AddressValueError:
            self.log["error"]["invalid_dn42_ipv6"].append(ipv6)

    def is_valid_link_local(self, ip: str):
        link_local = "fe80::/16"
        try:
            if IPv6Address(ip) not in ip_network(link_local):
                self.log["error"]["invalid_link_local"].append(ip)
        except AddressValueError:
            self.log["error"]["invalid_link_local"].append(ip)

    def is_valid_asn(self, asn: str):
        dn42_regex = "^((424242)|(420127))[0-9]{4}$"
        if not rematch(dn42_regex, asn):
            self.log["error"]["invalid_dn42_asn"].append(asn)

    def is_valid_port(self, port: str):
        try:
            if not (int(port) > 0 and int(port) < 65535):
                self.log["error"]["invalid_port"].append(port)
        except:
            self.log["error"]["invalid_port"].append(port)

    def is_valid_key(self, key: str):
        wg_key = "^[A-Za-z0-9+/]{43}="
        if not rematch(wg_key, key):
            self.log["error"]["invalid_wg_key"].append(key)

    def is_valid_address(self):
        for name, section in self.config.items():
            for key, address in section.items():
                if key == "address":
                    instance = self.system.instances[name]
                    try:
                        if not (
                            (
                                type(ip_address(address)) == IPv4Address
                                and instance.address4
                            )
                            or (
                                type(ip_address(address)) == IPv6Address
                                and instance.address6
                            )
                        ):
                            self.log["error"]["invalid_address"].append(key)
                    except ValueError:
                        try:
                            namelook = Namelook(address)
                            if not (
                                (namelook.ipv4 and instance.address4)
                                or (namelook.ipv6 and instance.address6)
                            ):
                                self.log["error"]["invalid_address"].append(key)
                        except:
                            self.log["error"]["invalid_address"].append(key)

    def check_all_error(self):
        self.is_valid_filename()
        self.only_valid_section()
        self.only_valid_attr()
        validates = {
            "asn": self.is_valid_asn,
            "ipv4": self.is_valid_dn42_ipv4,
            "ipv6": self.is_valid_dn42_ipv6,
            "link_local": self.is_valid_link_local,
            "port": self.is_valid_port,
            "pubkey": self.is_valid_key,
            "pskey": self.is_valid_key,
        }
        for attr, function in validates.items():
            for section in self.config.values():
                for key in section:
                    if key == attr:
                        function(section[key])
        self.is_valid_address()
        self.missing_and_dup()

    def form_message(self, log_type: str, message: str, obj_list: list[str]) -> str:
        result = ""
        if log_type == "error":
            result += "🌚"
        elif log_type == "warning":
            result += "🤔"
        elif log_type == "note":
            result += "😋"
        result += " "
        result += message % str(obj_list).strip("[]")
        return result

    def check(self) -> str:
        try:
            self.check_all_error()
        except Exception as e:
            self.log["error"]["unexpected_error"].append(str(e))
        result = ""
        for log_type in ["error", "warning", "note"]:
            for key, val_list in self.log[log_type].items():
                result += self.form_message(log_type, self.messages[key], val_list)
                result += "\n\n"
        return result

    messages = {
        "invalid_filename": "Filename for %s invalid. Check README for naming rules.",
        "no_instance": "Nodes %s do not appear to be my nodes. Check config/nodes anyway.",
        "invalid_attr": "Attributes %s are not valid. Check README for all valid attributes.",
        "missing_asn": "Config for nodes %s do not include ASNs.",
        "missing_pubkey": "Config for nodes %s do not include WireGuard public keys.",
        "alone_port": "Port specified in %s but address doesn't. Consider removing it or adding address.",
        "invalid_dn42_ipv4": "IPv4 addresses %s don't seem to be valid DN42 or NeoNetwork IPv4 addresses.",
        "invalid_dn42_ipv6": "IPv6 addresses %s don't seem to be valid DN42 or NeoNetwork IPv6 addresses.",
        "invalid_link_local": "Link-local addresses %s don't seem to be valid.",
        "invalid_dn42_asn": "ASNs %s don't seem to be valid DN42 or NeoNetwork ASNs.",
        "invalid_port": "Ports %s don't seem to be valid port numbers.",
        "invalid_wg_key": "Wireguard keys %s don't seem to be valid.",
        "invalid_address": "Address %s invalid. This may be because the IP or domain you provide mismatch with my node's. Check README for more information.",
        "unexpected_error": "An error %s happened unexpectedly.",
        "ignoring_dn42_ip": "IP addresses in section %s will be ignored in favor of link-local address. Please remove them if this is intended.",
        "pskey_not_recommended": "The preshared key has been used for %s. It is not recommended to use here as meant to be private.",
        "link_local_can_ignore": "link-local address %s can be ignored because they are in the same format often provided by dn42 users.",
        "port_can_ignore": "ports %s can be ignored because they are in the same format often provided by dn42 users.",
        "alone_address": "Port doesn't specified in %s. Will pick default port. (see README)",
        "default_link_local": "Link-local address not specified in %s. Will pick default one. (see README)",
        "passive_connect": "Config for nodes %s do not include addresses. I'll not configure endpoint for this node.",
    }
