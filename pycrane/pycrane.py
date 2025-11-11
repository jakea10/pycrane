from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class ContainerImage:
    """
    This class represents a container image to be transferred from `source_repo` to `target_repo`.
    """

    name: str
    tag: str
    source_repo: str
    target_repo: str

    @classmethod
    def from_dict(cls, d: dict):
        container_image = cls(d["name"], d["tag"], d["source_repo"], d["target_repo"])
        return container_image


class RegistryLogin(NamedTuple):
    """
    This class represents a container registry and its login credentials.
    """

    username: str
    password: str
    registry: str
