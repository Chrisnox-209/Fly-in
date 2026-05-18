import os
import sys
from typing import Literal
from parser import parse
from game import GameApp


def txt_files() -> str | Literal[False]:
    count: int = 0
    for file in os.listdir("."):
        if file.endswith(".txt"):
            file_map: str = file
            count += 1
    if count < 1:
        print("[Error]: map file not found")
        return False
    elif count > 1:
        print("[Error]: Please upload only one map file.")
        return False
    else:
        return file_map


def main() -> None:
    if txt_files() is not False:
        file_map: str | Literal[False] = txt_files()
    else:
        sys.exit(1)
    parse(file_map)


if __name__ == "__main__":
    main()
    # app = GameApp()
    # app.run()
