from src.tools import Artifact, Config
from pathlib import Path


class Instance:
    def __init__(self, name: str, asn: str) -> None:
        self.name = name
        self.asn = asn
        try:
            config = Config(f"config/nodes/{name}.conf").content["main"]
            self.address4 = config["address4"] if "address4" in config else None
            self.address6 = config["address6"] if "address6" in config else None
            self.link_local = config["link_local"]
            self.pubkey = config["pubkey"]
            self.digit = config["digit"]
        except:
            raise Exception(f"config for {name} not correct")
        try:
            generated = Config(f"generated/nodes/{name}.conf").content["main"]
            self.ipv4 = generated["my_ipv4"]
            self.ipv6 = generated["my_ipv6"]
        except:
            raise Exception(f"generated config for {name} not correct")

    def save(self, template: str, pathname: str, pair: dict[str, str]):
        artifact = Artifact(pathname, self.name)
        artifact.fill(template, pair)
        artifact.save()

    def add_mesh(self, peer):
        if peer != self:
            if (peer.address4 and self.address4) or (peer.address6 and self.address6):
                wg_conf = {
                    "my_port": str(10000 + int(peer.digit))
                    if self.address4 or self.address6
                    else None,
                    "peer_pubkey": peer.pubkey,
                    "my_link_local": self.link_local,
                    "my_ipv4": self.ipv4,
                    "peer_link": (peer.address4 if peer.address4 != "private" else None)
                    if self.address4
                    else (peer.address6 if peer.address6 != "private" else None),
                    "peer_port": str(10000 + int(self.digit))
                    if peer.address4 or peer.address6
                    else None,
                }
                self.save("wg-mesh", f"/etc/wireguard/{peer.name}.own.conf", wg_conf)
            bgp_conf = {
                "peer_abbr": peer.name,
                "peer_ipv6": peer.ipv6,
                "my_asn": self.asn,
            }
            self.save("bird-ibgp", f"/etc/bird/own/{peer.name}.conf", bgp_conf)

    def add_peer(self, peer_dict: dict[str, str]):
        if peer_dict["address"] or self.address4 or self.address6:
            if peer_dict["asn"].startswith("424242"):
                my_port = f"2{peer_dict['asn'][-4:]}"
            elif peer_dict["asn"].startswith("420127"):
                my_port = f"3{peer_dict['asn'][-4:]}"
            wg_conf = {
                "my_port": my_port if (self.address4 or self.address6) else None,
                "my_link_local": self.link_local,
                "my_ipv4": self.ipv4.rstrip("/32"),
                "my_ipv6": self.ipv6.rstrip("/64"),
                "peer_ipv4": peer_dict["ipv4"]
                if "ipv4" in peer_dict and "link_local" not in peer_dict
                else None,
                "peer_ipv6": peer_dict["ipv6"]
                if "ipv6" in peer_dict and "link_local" not in peer_dict
                else None,
                "peer_pubkey": peer_dict["pubkey"],
                "peer_pskey": peer_dict["pskey"] if "pskey" in peer_dict else None,
                "peer_link": peer_dict["address"] if "address" in peer_dict else None,
                "peer_port": peer_dict["port"]
                if "port" in peer_dict
                else f"2{self.asn[-4:]}",
            }
            self.save("wg-peer", f"/etc/wireguard/{peer_dict['name']}.conf", wg_conf)
            if "link_local" in peer_dict or (
                "ipv4" not in peer_dict and "ipv6" not in peer_dict
            ):
                bgp_conf = {
                    "peer_name": peer_dict["name"],
                    "peer_link_local": peer_dict["link_local"]
                    if "link_local" in peer_dict
                    else f"fe80::{peer_dict['asn'][-4:]}",
                    "peer_asn": peer_dict["asn"],
                    "my_link_local": self.link_local,
                }
                self.save(
                    "bird-peer-ll",
                    f"/etc/bird/peers/{peer_dict['name']}.conf",
                    bgp_conf,
                )
            else:
                artifact = Artifact(
                    f"/etc/bird/peers/{peer_dict['name']}.conf", self.name
                )
                bgp_conf = {
                    "peer_name": peer_dict["name"],
                    "peer_ipv4": peer_dict["ipv4"] if "ipv4" in peer_dict else None,
                    "peer_ipv6": peer_dict["ipv6"] if "ipv6" in peer_dict else None,
                    "peer_asn": peer_dict["asn"],
                }
                config_content = ""
                if "ipv4" in peer_dict:
                    config_content += artifact.fill("bird-peer-v4", bgp_conf)
                if "ipv6" in peer_dict:
                    config_content += artifact.fill("bird-peer-v6", bgp_conf)
                artifact.save()


class System:
    def __init__(self) -> None:
        instance_names = [path.stem for path in Path("generated/nodes").glob("*.conf")]
        self.instances = {}
        self.asn = open("config/my_asn").read().strip()
        for name in instance_names:
            self.instances[name] = Instance(name, self.asn)

    def full_mesh(self):
        for instance in self.instances.values():
            for other in self.instances.values():
                instance.add_mesh(other)

    def add_peer(self):
        for peer_file in Path("config/peers").glob("*.conf"):
            for node, node_dict in Config(peer_file).content.items():
                node_dict["name"] = peer_file.stem
                self.instances[node].add_peer(node_dict)

    def generate(self):
        self.add_peer()
        self.full_mesh()
