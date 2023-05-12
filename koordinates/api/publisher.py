from typing import (
    Dict,
    Optional
)


class PublisherTheme:
    """
    Represents a publisher theme
    """
    def __init__(self, details: Dict):
        self.details = details

    def background_color(self) -> Optional[str]:
        """
        Returns the background color
        """
        return self.details.get('background_color')

    def logo(self) -> Optional[str]:
        """
        Returns the publisher's logo
        """
        return self.details.get('logo')


class PublisherSite:
    """
    Represents a publisher site
    """

    def __init__(self, details: Dict):
        self.details = details

    def name(self) -> Optional[str]:
        """
        Returns the site name
        """
        return self.details.get("name")


class Publisher:
    """
    Represents a publisher
    """

    def __init__(self, details: Dict):
        self.details = details
        self.site = PublisherSite(self.details['site']) \
            if self.details.get('site') else None
        self.theme = PublisherTheme(self.details['theme']) \
            if self.details.get('theme') else None

    def name(self) -> Optional[str]:
        """
        Returns the publisher's name
        """
        return self.details.get("name")

    def dataset_count(self) -> int:
        """
        Returns the dataset count
        """
        return int(self.details.get("dataset_count", 0))
