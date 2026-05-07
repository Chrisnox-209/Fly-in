import os
import sys


def txt_files() -> bool:
    count: int = 0

    for file in os.listdir("./maps"):
        if file.endswith(".txt"):
            count += 1

    if count < 1:
        print("[Error]: map file not found")
        return False
    elif count > 1:
        print("[Error]: Please upload only one map file.")
        return False
    else:
        return True


def main() -> None:
    if txt_files():
        print("okk !!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
