from src.artifact import System
from src.check_peers import Peer

from sys import argv

if argv[1] == "generate":
    System().generate()

if argv[1] == "check":
    Peer(argv[2]).check_all()