from configparser import ConfigParser
from pathlib import Path
from src.tools import fill_config


class instance:
    def __init__(self, name: str) -> None:
        self.name = name
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
        except:
            raise Exception(f"config for {name} not correct")
        try:
            parser.read(f"generated/nodes/{name}.conf")
            self.ipv4 = parser["main"]["my_ipv4"]
            self.ipv6 = parser["main"]["my_ipv6"]
        except:
            raise Exception(f"generated config for {name} not correct")

    def add_mesh():
        pass

    def add_peer():
        pass

class system:
    def __init__(self) -> None:
        path_list = Path("generated/nodes").rglob("*.conf")
        instance_names = [str(path) for path in path_list]
        self.instances = {}
        for name in instance_names:
            self.instances[name] = instance(name)

    def full_mesh(self):
        for (name, instance) in self.instances:
            pass
