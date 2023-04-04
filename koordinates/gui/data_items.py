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


class KartRepositoryItem(QgsDirectoryItem):
    """
    Represents a Kart repository
    """

    def __init__(self,
                 parent: QgsDataItem,
                 repo: 'Repository'):
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

        # self.setIcon('')
        self.populate()

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
        print('created')

    def __del__(self):
        print('deleted')

    def name(self):
        return 'koordinates'

    def dataProviderKey(self):
        return 'koordinates'

    def capabilities(self):
        return int(QgsDataProvider.Dir)

    def createDataItem(self, path, parentItem):
        if not path:
            return KoordinatesRootItem()

        return None
