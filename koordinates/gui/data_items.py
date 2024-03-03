from pathlib import Path

from qgis.core import (
    Qgis,
    QgsDataProvider,
    QgsDataItemProvider,
    QgsDataCollectionItem,
    QgsDirectoryItem,
    QgsDataItem
)

from ..core import KartUtils
from .gui_utils import GuiUtils


class KartRepositoryItem(QgsDirectoryItem):
    """
    Represents a Kart repository
    """

    def __init__(self,
                 parent: QgsDataItem,
                 repo: 'Repository'):  # NOQA
        path = repo.path
        title = repo.title()
        if not title:
            title = Path(path).stem

        super().__init__(parent, title, path)


class KoordinatesRootItem(QgsDataCollectionItem):
    """
    Root item for Koordinates browser entries
    """

    def __init__(self):
        super().__init__(None, 'Koordinates', '', 'koordinates')
        self.setCapabilitiesV2(
            Qgis.BrowserItemCapabilities(
                Qgis.BrowserItemCapability.Fast |
                Qgis.BrowserItemCapability.Fertile
            )
        )

        self.setIcon(GuiUtils.get_icon('browser_icon.svg'))
        self.populate()

        try:
            from kart.core import RepoManager
            manager = RepoManager.instance()
            manager.repo_added.connect(self.refresh)
            manager.repo_removed.connect(self.refresh)

        except ImportError:
            pass

    def createChildren(self):
        res = []

        for repo in KartUtils.get_kart_repos():
            res.append(
                KartRepositoryItem(self, repo)
            )

        return res


class KoordinatesDataItemProvider(QgsDataItemProvider):
    """
    Data item provider for Koordinates items in the QGIS browser
    """

    def __init__(self):
        super().__init__()

    def name(self):
        return 'koordinates'

    def dataProviderKey(self):
        return 'koordinates'

    def capabilities(self):
        return QgsDataProvider.Dir

    def createDataItem(self, path, parentItem):
        if not path:
            return KoordinatesRootItem()

        return None
