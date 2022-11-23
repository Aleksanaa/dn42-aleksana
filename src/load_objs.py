from configparser import ConfigParser
from src.tools import fill_config
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
            bgp_conf = {
                "peer_abbr": peer.name,
                "peer_ipv6": peer.ipv6,
                "my_asn": self.asn,
            }
            makedirs(f"{self.gen_path}/etc/wireguard/", exist_ok=True)
            with open(
                f"{self.gen_path}/etc/wireguard/{peer.name}.own.conf", "w"
            ) as config:
                config.write(fill_config("wg-mesh", wg_conf))
                config.close()
            makedirs(f"{self.gen_path}/etc/bird/own/", exist_ok=True)
            with open(f"{self.gen_path}/etc/bird/own/{peer.name}.conf", "w") as config:
                config.write(fill_config("bird-ibgp", bgp_conf))
                config.close

    def add_peer():
        pass


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
