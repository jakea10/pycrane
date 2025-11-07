import docker
import json
import typer
import os
from dataclasses import dataclass, asdict
from collections import namedtuple
from typing_extensions import Annotated, List
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


app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
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
            help="The password for login to the target registry.",
        ),
    ] = None,
):
    err_console = Console(stderr=True)
    error_prefix = "[bold red]ERROR:[/]"
    info_prefix = "[bold blue]INFO:[/]"

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
            print(f"{info_prefix} Parsing container image data...")
            images: List[ContainerImage] = []
            # images = [ContainerImage(**image_data) for image_data in json.load(f)]
            for image_data in json.load(f):
                try:
                    images.append(ContainerImage(**image_data))
                except TypeError as e:
                    err_console.print(
                        f"{error_prefix} Failed parsing container image data: received error: {e} while parsing image data: {image_data}"
                    )
                    raise typer.Exit(code=1)
            print(f"{info_prefix} Successfully parsed container image data.")
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

    # --- Docker logins --- #
    client = (
        docker.from_env()
    )  # If using Docker Desktop, you must allow the default Docker socket to be used

    RegistryLogin = namedtuple("RegistryLogin", ["username", "password", "registry"])
    logins = []

    if source_registry and source_username and source_password:
        logins.append(RegistryLogin(source_username, source_password, source_registry))

    if target_registry and target_username and target_password:
        logins.append(RegistryLogin(target_username, target_password, target_registry))

    for login in logins:
        try:
            response = client.login(
                login.username, login.password, registry=login.registry
            )
            if response["Status"] == "Login Succeeded":
                print(f'{info_prefix} Login Succeeded to "{login.registry}"')
        except docker.errors.APIError as e:
            err_console.print(f"{error_prefix} {e}")
            raise typer.Exit(code=1)

    # --- Transfer images --- #
    for image in images:
        source = f"{image.source_repo}:{image.tag}"
        target = f"{image.target_repo}:{image.tag}"

        # Check if image already exists in target repo
        exit_code = os.system(f"docker manifest inspect {target} > /dev/null 2>&1")
        if exit_code == 0:
            print(f'{info_prefix} Target image "{target}" already exists. Skipping...')
            continue

        # Pull the source image
        print(f'{info_prefix} Pulling image "{source}"...')
        try:
            pulled = client.images.pull(repository=image.source_repo, tag=image.tag)
        except docker.errors.APIError as e:
            err_console.print(f"{error_prefix} {e}")
            raise typer.Exit(code=1)
        print(f'{info_prefix} Successfully pulled image "{source}".')

        # Re-tag
        try:
            pulled.tag(repository=image.target_repo, tag=image.tag)
        except docker.errors.APIError as e:
            err_console.print(f"{error_prefix} {e}")
            raise typer.Exit(code=1)
        print(f'{info_prefix} Re-tagged "{source}" as "{target}".')

        # Push
        print(f'{info_prefix} Pushing image "{target}"...')
        try:
            resp = client.images.push(repository=image.target_repo, tag=image.tag)
            # Verify push
            exit_code = os.system(f"docker manifest inspect {target} > /dev/null 2>&1")
            if exit_code:
                print(
                    f'{error_prefix} Push failed for "{target}". Remote response: {resp}'
                )
                raise typer.Exit(code=1)
        except docker.errors.APIError as e:
            err_console.print(f"{error_prefix} {e}")
            raise typer.Exit(code=1)
        print(f'{info_prefix} Successfully pushed image "{target}".')


if __name__ == "__main__":
    app()
