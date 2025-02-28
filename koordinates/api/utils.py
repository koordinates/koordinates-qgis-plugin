from typing import Dict, Set
import binascii

from qgis.PyQt.QtCore import QUrlQuery

from qgis.core import (
    QgsGeometry,
    QgsWkbTypes
)

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
    def geometry_type_from_dataset_response(dataset: dict) \
            -> QgsWkbTypes.GeometryType:
        """
        Extracts geometry type from a dataset response
        """
        if dataset.get('data', {}).get('geometry_type') in (
                'polygon', 'multipolygon'):
            return QgsWkbTypes.PolygonGeometry
        elif dataset.get('data', {}).get('geometry_type') in (
                'point', 'multipoint'):
            return QgsWkbTypes.PointGeometry
        elif dataset.get('data', {}).get('geometry_type') in (
                'linestring', 'multilinestring'):
            return QgsWkbTypes.LineGeometry

        return QgsWkbTypes.UnknownGeometry

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

        if datatype == DataType.Repositories:
            repo_user_capabilities = dataset.get("user_capabilities", [])
            if "can-clone" not in repo_user_capabilities:
                capabilities.remove(Capability.Clone)
            if "can-request-clone" in repo_user_capabilities:
                capabilities.add(Capability.RequestClone)

        elif not dataset.get("repository"):
            capabilities.remove(Capability.Clone)

        else:
            repo = dataset["repository"]
            if repo and not isinstance(repo, dict):
                from .client import KoordinatesClient

                repo = KoordinatesClient.instance().get_json(repo)
            repo_user_capabilities = repo.get("user_capabilities", [])
            if "can-clone" not in repo_user_capabilities:
                capabilities.remove(Capability.Clone)
            if "can-request-clone" in repo_user_capabilities:
                capabilities.add(Capability.RequestClone)

        return capabilities

    @staticmethod
    def geometry_from_hexewkb(hexewkb: str) -> QgsGeometry:
        """
        Converts a HEXEWKB string to a QgsGeometry
        """
        ewkb = binascii.unhexlify(hexewkb)
        # skip over ewkb bits
        wkb = ewkb[0:4] + ewkb[8:]
        g = QgsGeometry()
        g.fromWkb(wkb)
        return g

    @staticmethod
    def geometry_from_hexwkb(hexwkb: str) -> QgsGeometry:
        """
        Converts a HEXWKB string to a QgsGeometry
        """
        wkb = binascii.unhexlify(hexwkb)
        g = QgsGeometry()
        g.fromWkb(wkb)
        return g
