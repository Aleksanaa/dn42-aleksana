from configparser import ConfigParser
from os import listdir
from collections import defaultdict


class Peer:
    def __init__(self, name: str) -> None:
        parser = ConfigParser()
        parser.read(f"config/peers/{name}.conf")
        self.checklist = {"error": [], "warning": [], "note": []}
        self.raw_config = dict(parser.items())
        self.config = {
            key: dict(val) for key, val in self.raw_config.items() if key != "DEFAULT"
        }
        if "shared" in self.config.keys():
            self.config = {
                key: {**val, **self.config["shared"]}
                for key, val in self.config.items()
                if key != "shared"
            }
        self.nodes = [node.rstrip(".conf") for node in listdir("config/nodes")]

    def check_names(self):
        absent_names = [name for name in self.config.keys() if name not in self.nodes]
        if absent_names:
            self.checklist["warning"].append(
                f"nodes {', '.join(absent_names)} do not currently exist in my network. Their configs will be ignored."
            )
            self.config = {
                key: val for (key, val) in self.config.keys() if key not in absent_names
            }

    def check_attributes(self):
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
        message = ""
        for node, obj in self.config.items():
            for attribute in obj.keys():
                if attribute not in allowed_attributes:
                    message += ", ".join(attribute)
            if message:
                message += f" in {node}, "
        if message:
            self.checklist["error"].append(
                f"attributes {message.strip(', ')} are not valid."
            )

    def check_necessary(self):
        report = defaultdict(list)
        for node in self.config.keys():
            for attr in {"asn", "pubkey"}:
                if attr not in node.keys():
                    report[attr].append(node)
        if "asn" in report:
            self.checklist["asn"].append(f"attributes ")
    
    def check_all(self):
        pass
