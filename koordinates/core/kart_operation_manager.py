from typing import Optional

from qgis.PyQt.QtCore import (
    QObject
)


class KartOperationManager(QObject):
    """
    Keeps track of ongoing kart operations
    """

    def __init__(self):
        super().__init__()

    _instance: Optional['KartOperationManager'] = None

    @classmethod
    def instance(cls) -> 'KartOperationManager':
        """
        Returns the operation manager instance
        """
        return KartOperationManager._instance
