import os
import sys
import json
import argparse


class ContainerImage:
    name: str
    tag: str
    source_repo: str
    target_repo: str

    def __init__(self, name: str, tag: str, source_repo: str, target_repo: str):
        self.name = name
        self.tag = tag
        self.source_repo = source_repo
        self.target_repo = target_repo

    def __str__(self):
        return f"{self.name}:{self.tag}"
    
    def __repr__(self):
        cls = self.__class__.__name__
        return f"{cls}.{str(self)}"
    
    def __eq__(self, other):
        if self is other: # Same object in memory
            return True
        if type(self) is not type(other):
            return False
        return [self.name, self.tag, self.source_repo, self.target_repo] == [other.name, other.tag, other.source_repo, other.target_repo]
    
    @classmethod
    def from_dict(cls, d: dict):
        container_image = cls(
            d['name'],
            d['tag'],
            d['source_repo'],
            d['target_repo']
        )
        return container_image


def get_config(image_file: str | None = None) -> dict:
    config = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--image_file", dest="image_file", help="The JSON file defining the images to be transferred.")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactively enter configuration for image source and targetination.")
    parser.add_argument("--no-auth-source", action="store_false", dest="source_auth", help="Disable authentication to the source registry.")
    parser.add_argument("--no-auth-target", action="store_false", dest="target_auth", help="Disable authentication to the target registry.")
    args = parser.parse_args()

    if image_file:
        print(args.image_file)
        args.image_file = image_file
    elif args.image_file is None:
        args.image_file = input("Please enter the image data file: ").strip()

    if not (os.path.exists(args.image_file) and os.path.isfile(args.image_file)):
        print(f"ERROR - Invalid image data file: '{args.image_file}'.")
        sys.exit(1)

    if args.source_auth:
        config["SOURCE_REGISTRY_URL"] = None
        config["SOURCE_REGISTRY_USER"] = None
        config["SOURCE_REGISTRY_KEY"] = None

    if args.target_auth:
        config["TARGET_REGISTRY_URL"] = None
        config["TARGET_REGISTRY_USER"] = None
        config["TARGET_REGISTRY_KEY"] = None

    # Grab config values from env or user input
    for key, val in config.items():
        if val is None:
            if args.interactive:
                config[key] = input(f"{key}: ").strip()
                continue
            try:
                config[key] = os.environ[key]
            except KeyError:
                print(f"ERROR - '{key}' environment variable not set.")
                sys.exit(1)

    # Parse container image data
    with open(args.image_file, 'r') as f:
        config["IMAGES"] = [
            ContainerImage(
                image['name'],
                image['tag'],
                image['source_repo'],
                image['target_repo']
            )
            for image in json.load(f)
        ]

    return config
    


def main():
    print("Hello from Pycrane!")
    config = get_config()
    print(config)


if __name__ == "__main__":
    main()

    # import tempfile

    # sample_image_data = [
    #     {
    #         "name": "my-image",
    #         "tag": "latest",
    #         "source_repo": "registry.source.com/my-image",
    #         "target_repo": "registry.target.com/my-image"
    #     },
    #     {
    #         "name": "another-image",
    #         "tag": "1.2.3",
    #         "source_repo": "registry.source.com/another-image",
    #         "target_repo": "registry.target.com/another-image"
    #     }
    # ]

    # os.environ["SOURCE_REGISTRY_URL"] = "registry.source.com"
    # os.environ["SOURCE_REGISTRY_USER"] = "sourceUser"
    # os.environ["SOURCE_REGISTRY_KEY"] = "sourceKey"

    # os.environ["TARGET_REGISTRY_URL"] = "registry.target.com"
    # os.environ["TARGET_REGISTRY_USER"] = "targetUser"
    # os.environ["TARGET_REGISTRY_KEY"] = "targetKey"

    # # with tempfile.NamedTemporaryFile(delete_on_close=False, mode='w+') as f:
    # #     json.dump(sample_image_data, f)
    # #     f.flush()
    # #     config = get_config(f.name)

    # config = get_config()
