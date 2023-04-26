from typing import Dict, Set

from qgis.PyQt.QtCore import QUrlQuery

from .enums import (
    DataType,
    PublicAccessType,
    Capability
)


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
            elif dataset.get('kind') == 'pointcloud':
                return DataType.PointClouds
        elif dataset.get('type') == 'table':
            return DataType.Tables
        elif dataset.get('type') == 'document':
            return DataType.Documents
        elif dataset.get('type') == 'set':
            return DataType.Sets
        elif dataset.get('type') == 'repo':
            return DataType.Repositories

    @staticmethod
    def access_from_dataset_response(dataset: dict) -> PublicAccessType:
        """
        Returns the public access type for a dataset
        """
        if dataset.get('public_access') is None:
            return PublicAccessType.none

        return PublicAccessType.Download

    @staticmethod
    def capabilities_from_dataset_response(dataset: dict) -> Set[Capability]:
        """
        Returns capabilities for a dataset
        """
        datatype = ApiUtils.data_type_from_dataset_response(dataset)
        capabilities = DataType.capabilities(datatype)

        if not dataset.get("repository"):
            capabilities.remove(Capability.Clone)

        return capabilities
