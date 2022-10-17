from typing import Dict

from qgis.PyQt.QtCore import QUrlQuery

from .enums import DataType


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

    @staticmethod
    def data_type_from_dataset_response(dataset: dict) -> DataType:
        """
        Extracts data type from a dataset response
        """
        if dataset.get('type') == 'layer':
            if dataset.get('kind') == 'vector':
                return DataType.Vectors
            elif dataset.get('kind') == 'raster':
                return DataType.Rasters
            elif dataset.get('kind') == 'grid':
                return DataType.Grids
        elif dataset.get('type') == 'table':
            return DataType.Tables
        elif dataset.get('type') == 'document':
            return DataType.Documents
        elif dataset.get('type') == 'set':
            return DataType.Sets
        elif dataset.get('type') == 'repo':
            return DataType.Repositories
