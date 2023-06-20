from typing import (
    Dict,
    Optional,
    Set
)

from .enums import UserDatasetCapability


class Repo:
    """
    Represents a repository
    """

    def __init__(self, definition: Dict):
        self.definition = definition
        self.id = definition['id']

    def title(self) -> Optional[str]:
        """
        Returns the repository title
        """
        return self.definition.get('title')

    def user_capabilities(self) -> Set[UserDatasetCapability]:
        """
        Returns user capabilities for the dataset
        """
        res = set()

        for capability_string, capability_flag in {
            'can-star': UserDatasetCapability.Star,
            'can-clone': UserDatasetCapability.Clone
        }.items():
            if capability_string in self.definition.get(
                    'user_capabilities', []
            ):
                res.add(capability_flag)

        return res

    def clone_url(self) -> str:
        """
        Returns the clone URL for the repository
        """
        return self.definition.get('clone_location_https')
