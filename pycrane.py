import json
import typer
from typing_extensions import Annotated
from rich import print
from rich.console import Console
from rich.table import Table


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
        if self is other:  # Same object in memory
            return True
        if type(self) is not type(other):
            return False
        return [self.name, self.tag, self.source_repo, self.target_repo] == [
            other.name,
            other.tag,
            other.source_repo,
            other.target_repo,
        ]

    @classmethod
    def from_dict(cls, d: dict):
        container_image = cls(d["name"], d["tag"], d["source_repo"], d["target_repo"])
        return container_image


def main(
    image_file: Annotated[
        str,
        typer.Argument(
            envvar="PYCRANE_IMAGE_FILE",
            help="The file defining container images to be transferred.",
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            envvar="SKIP_CONFIRMATION", help="Skip confirmation of parsed images"
        ),
    ] = False,
    source_username: Annotated[
        str | None,
        typer.Option(
            envvar="PYCRANE_SOURCE_USERNAME",
            help="The username for login to the source registry.",
        ),
    ] = None,
    source_password: Annotated[
        str | None,
        typer.Option(
            envvar="PYCRANE_SOURCE_PASSWORD",
            help="The password for login to the source registry.",
        ),
    ] = None,
    target_username: Annotated[
        str | None,
        typer.Option(
            envvar="PYCRANE_TARGET_USERNAME",
            help="The username for login to the target registry.",
        ),
    ] = None,
    target_password: Annotated[
        str | None,
        typer.Option(
            envvar="PYCRANE_TARGET_PASSWORD",
            help="The password for login to the soutargetrce registry.",
        ),
    ] = None,
):
    config = {}

    try:
        # Parse container image data
        with open(image_file, mode="r") as f:
            print("[bold blue]Parsing container image data...")
            config["images"] = [
                ContainerImage(
                    image["name"],
                    image["tag"],
                    image["source_repo"],
                    image["target_repo"],
                )
                for image in json.load(f)
            ]
    except FileNotFoundError:
        console = Console(stderr=True)
        console.print(f"Image file not found: '{image_file}'...")
        raise typer.Exit(code=1)

    if not force:
        # Display parsed images and prompt user to continue
        console = Console()
        table = Table("REPOSITORY", "TAG", "SOURCE", "TARGET", title="Images")
        for image in config["images"]:
            table.add_row(image.name, image.tag, image.source_repo, image.target_repo)
        console.print(table)
        user_continue = typer.confirm("Continue?", abort=True)
        print("Alrighty, let's go! :rocket:")

    print(source_username, source_password)
    print(target_username, target_password)


if __name__ == "__main__":
    typer.run(main)
