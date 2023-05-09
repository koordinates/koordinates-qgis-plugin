from typing import (
    Dict,
    Optional
)


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

    def clone_url(self) -> str:
        """
        Returns the clone URL for the repository
        """
        return self.definition.get('clone_location_https')
