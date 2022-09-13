from typing import Dict
from qgis.PyQt.QtCore import QUrlQuery


class ApiUtils:
    """
    API handling utility functions
    """

    @staticmethod
    def to_url_query(parameters: Dict[str, object]) -> QUrlQuery:
        """
        Converts query parameters to a URL query
        """
        query = QUrlQuery()
        for name, value in parameters.items():
            if isinstance(value, (list, tuple)):
                for v in value:
                    query.addQueryItem(name, str(v))
            else:
                query.addQueryItem(name, str(value))
        return query
