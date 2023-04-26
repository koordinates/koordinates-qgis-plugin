from typing import Dict


class Repo:
    """
    Represents a repository
    """

    def __init__(self, definition: Dict):
        self.definition = definition
        self.id = definition['id']

    def clone_url(self) -> str:
        """
        Returns the clone URL for the repository
        """
        return self.definition.get('clone_location_https')
