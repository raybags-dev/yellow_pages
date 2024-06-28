import fileinput
import sys


def update_requirements(remove_version=True):
    with fileinput.FileInput("requirements.txt", inplace=True, backup=".bak") as file:
        for line in file:
            if line.strip().startswith("urllib3"):
                if remove_version:
                    print("urllib3")
                else:
                    print("urllib3==2.2.1")
            else:
                print(line, end="")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python modify_requirements.py <remove|restore>")
        sys.exit(1)
    if sys.argv[1] == "remove":
        update_requirements(remove_version=True)
    elif sys.argv[1] == "restore":
        update_requirements(remove_version=False)
    else:
        print("Invalid argument. Use 'remove' or 'restore'.")
        sys.exit(1)
