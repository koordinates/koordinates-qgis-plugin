from enum import (
    Enum,
    auto
)


class TabStyle(Enum):
    Flat = auto()
    Rounded = auto()


class FilterWidgetAppearance(Enum):
    Horizontal = auto()
    Vertical = auto()


class StandardExploreModes:
    """
    Standard explore modes.

    Any string can be accepted as an explore mode, but these are current
    well known ones...
    """
    Popular = 'popular'
    Recent = 'recent'
    Browse = 'browse'
    Publishers = 'publishers'
