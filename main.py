from src.artifact import System
from src.check_peers import Check

from sys import argv
from pathlib import Path

if argv[1] == "generate":
    System().generate()

if argv[1] == "check":
    print(Check(Path(argv[2])).check())
