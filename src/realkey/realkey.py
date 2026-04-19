from build123d import *
from ocp_vscode import *

from realkey.Common import key
from realkey.Paclock import Paclock


def main():
    for key_name, key_class in key.Key._list.items():
        print("Key: " + key_name)

if __name__ == "__main__":
    main()
