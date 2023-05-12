from typing import (
    Dict,
    Optional
)

from .enums import PublisherType


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
        if not self.details.get('background_color'):
            return None

        return '#' + self.details['background_color']

    def logo(self) -> Optional[str]:
        """
        Returns the publisher's logo
        """
        _logo = self.details.get('logo')
        if _logo:
            if not _logo[:6] == 'https:':
                return 'https:' + _logo
            return _logo

        return None


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

    def __init__(self, publisher_type: PublisherType, details: Dict):
        self.details = details
        self.publisher_type = publisher_type
        self.site = PublisherSite(self.details['site']) \
            if self.details.get('site') else None
        self.theme = PublisherTheme(self.details['theme']) \
            if self.details.get('theme') else None

    def id(self) -> Optional[str]:
        """
        Returns the publisher's ID
        """
        return self.details.get("id")

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
