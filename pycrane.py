import docker
import json
import typer
from dataclasses import dataclass, asdict
from typing_extensions import Annotated
from rich import print
from rich.console import Console
from rich.table import Table


@dataclass
class ContainerImage:
    name: str
    tag: str
    source_repo: str
    target_repo: str

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
    source_registry: Annotated[
        str | None,
        typer.Option(
            envvar="PYCRANE_SOURCE_REGISTRY",
            help="The source registry to pull container images from.",
        ),
    ] = None,
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
    target_registry: Annotated[
        str | None,
        typer.Option(
            envvar="PYCRANE_TARGET_REGISTRY",
            help="The target registry to push container images to.",
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
    err_console = Console(stderr=True)
    error_prefix = "[bold red]Error:[/]"

    if (source_username or source_password) and not source_registry:
        err_console.print(
            f"{error_prefix} --source-registry is required when --source-username and --source-password are provided."
        )
        raise typer.Exit(code=1)

    if (target_username or target_password) and not target_registry:
        err_console.print(
            f"{error_prefix} --target-registry is required when --target-username and --target-password are provided."
        )
        raise typer.Exit(code=1)

    # --- Parse container image data --- #
    try:
        with open(image_file, mode="r") as f:
            print("[bold blue]INFO: Parsing container image data...")
            images = []
            # images = [ContainerImage(**image_data) for image_data in json.load(f)]
            for image_data in json.load(f):
                try:
                     images.append(ContainerImage(**image_data))
                except TypeError as e:
                    err_console.print(f"{error_prefix} Failed parsing container image data: received error: {e} while parsing image data: {image_data}")
                    raise typer.Exit(code=1)
            print("[bold blue]INFO: Successfully parsed container image data.")
    except FileNotFoundError:
        err_console.print(f"{error_prefix} Image file not found: '{image_file}'")
        raise typer.Exit(code=1)

    if not force:
        # Display parsed images and prompt user to continue
        console = Console()
        table = Table("REPOSITORY", "TAG", "SOURCE", "TARGET", title="Images")
        for image in images:
            table.add_row(*asdict(image).values())
        console.print(table)
        user_continue = typer.confirm("Continue?", abort=True)
        print("Alrighty, let's go! :rocket:")

    # --- Docker operations --- #
    # If using Docker Desktop, you must allow the default Docker socket to be used
    client = docker.from_env()

    if source_registry and source_username and source_password:
        try:
            client.login(source_username, source_password, registry=source_registry)
        except docker.errors.APIError as e:
            err_console.print(e)
            raise typer.Exit(code=1)

    if target_registry and target_username and target_password:
        try:
            client.login(target_username, target_password, registry=target_registry)
        except docker.errors.APIError as e:
            err_console.print(e)
            raise typer.Exit(code=1)

    # docker_logins = []
    # if source_registry and source_username and source_password:
    #     docker_logins.append(
    #         f"docker login -u {source_username} -p {source_password} {source_registry}"
    #     )
    # if target_registry and target_username and target_password:
    #     docker_logins.append(
    #         f"docker login -u {target_username} -p {target_password} {target_registry}"
    #     )
    # if docker_logins:
    #     print("[bold blue]INFO: Executing registry logins...")
    #     # for login in docker_logins:
    #     #     subprocess.run(login)


if __name__ == "__main__":
    typer.run(main)
