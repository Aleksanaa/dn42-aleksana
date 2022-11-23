from configparser import ConfigParser
from src.tools import fill_config, save_config
from os import makedirs, listdir


class Instance:
    def __init__(self, name: str, asn: str) -> None:
        self.name = name
        self.asn = asn
        self.gen_path = f"artifacts/{name}"
        parser = ConfigParser()
        try:
            parser.read(f"config/nodes/{name}.conf")
            if "address" in parser["main"].keys():
                self.address = parser["main"]["address"]
            else:
                self.address = None
            self.link_local = parser["main"]["link_local"]
            self.pubkey = parser["main"]["pubkey"]
            self.digit = parser["main"]["digit"]
        except:
            raise Exception(f"config for {name} not correct")
        try:
            parser.read(f"generated/nodes/{name}.conf")
            self.ipv4 = parser["main"]["my_ipv4"]
            self.ipv6 = parser["main"]["my_ipv6"]
        except:
            raise Exception(f"generated config for {name} not correct")

    def add_mesh(self, peer):
        if peer != self and (peer.address or self.address):
            wg_conf = {
                "my_port": str(10000 + int(peer.digit)) if self.address else None,
                "peer_pubkey": peer.pubkey,
                "my_link_local": self.link_local,
                "my_ipv4": self.ipv4,
                "peer_link": peer.address,
                "peer_port": str(10000 + int(self.digit)) if peer.address else None,
            }
            save_config(
                f"{self.gen_path}/etc/wireguard/{peer.name}.own.conf",
                fill_config("wg-mesh", wg_conf),
            )
        bgp_conf = {
            "peer_abbr": peer.name,
            "peer_ipv6": peer.ipv6,
            "my_asn": self.asn,
        }
        save_config(
            f"{self.gen_path}/etc/bird/own/{peer.name}.conf",
            fill_config("bird-ibgp", bgp_conf),
        )

    def add_peer(self, peer_dict: dict[str, str]):
        if peer_dict["address"] and self.address:
            if peer_dict["asn"].startswith("424242"):
                my_port = f"2{peer_dict['asn'][-4:]}"
            elif peer_dict["asn"].startswith("420127"):
                my_port = f"3{peer_dict['asn'][-4:]}"
            wg_conf = {
                "my_port": my_port if not self.address else None,
                "my_link_local": self.link_local,
                "my_ipv4": self.ipv4,
                "my_ipv6": self.ipv6,
                "peer_ipv4": peer_dict["ipv4"]
                if "ipv4" in peer_dict and "link_local" not in peer_dict
                else None,
                "peer_ipv6": peer_dict["ipv6"]
                if "ipv6" in peer_dict and "link_local" not in peer_dict
                else None,
                "peer_pubkey": peer_dict["pubkey"],
                "peer_link": peer_dict["address"] if "address" in peer_dict else None,
                "peer_port": peer_dict["port"]
                if "port" in peer_dict
                else f"2{self.asn[-4:]}",
            }
            save_config(
                f"{self.gen_path}/etc/wireguard/{peer_dict['name']}.conf",
                fill_config("wg-peer", wg_conf),
            )
            if "link_local" in peer_dict:
                bgp_conf = {
                    "peer_name": peer_dict["name"],
                    "peer_link_local": peer_dict["link_local"],
                    "peer_asn": peer_dict["asn"],
                    "my_link_local": self.link_local,
                }
                config_content = fill_config("bird-peer-ll", bgp_conf)
            else:
                bgp_conf = {
                    "peer_name": peer_dict["name"],
                    "peer_ipv4": peer_dict["ipv4"] if "ipv4" in peer_dict else None,
                    "peer_ipv6": peer_dict["ipv6"] if "ipv6" in peer_dict else None,
                    "peer_asn": peer_dict["asn"],
                }
                config_content = ""
                if "ipv4" in peer_dict:
                    config_content += fill_config("bird-peer-v4", bgp_conf)
                if "ipv6" in peer_dict:
                    config_content += fill_config("bird-peer-v6", bgp_conf)
            save_config(
                f"{self.gen_path}/etc/bird/peers/{peer_dict['name']}.conf",
                config_content,
            )


class System:
    def __init__(self) -> None:
        instance_names = [
            path.rstrip(".conf")
            for path in listdir("generated/nodes")
            if path.endswith(".conf")
        ]
        self.instances = {}
        self.asn = open("config/my_asn").read().strip()
        for name in instance_names:
            self.instances[name] = Instance(name, self.asn)

    def full_mesh(self):
        for instance in self.instances.values():
            for other in self.instances.values():
                instance.add_mesh(other)

    def add_peer(self):
        peer_names = [
            path.rstrip(".conf")
            for path in listdir("config/peers")
            if path.endswith(".conf")
        ]
        for peer_name in peer_names:
            parser = ConfigParser()
            parser.read(f"config/peers/{peer_name}.conf")
            for node in [
                node for node in parser.keys() if node in self.instances.keys()
            ]:
                node_dict = {**parser["shared"], **parser[node]}
                for key in node_dict.keys():
                    if node_dict[key] == "none":
                        node_dict.pop(key)
                node_dict["name"] = peer_name
                self.instances[node].add_peer(node_dict)

    def generate(self):
        self.add_peer()
        self.full_mesh()
