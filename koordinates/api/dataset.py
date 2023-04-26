from typing import (
    Dict,
    Optional
)

from .enums import DataType
from .utils import ApiUtils
from .client import KoordinatesClient
from .repo import Repo


class Dataset:
    """
    Represents a dataset
    """

    def __init__(self, details: Dict):
        self.details = details
        self.id = details['id']
        self.datatype = ApiUtils.data_type_from_dataset_response(self.details)
        self.capabilities = ApiUtils.capabilities_from_dataset_response(
            self.details
        )
        self.repository: Optional[Repo] = None

    def title(self) -> str:
        """
        Returns the dataset's title
        """
        return self.details.get("title", 'Layer')

    def clone_url(self) -> Optional[str]:
        """
        Returns the clone URL for the dataset
        """
        if self.repository is not None:
            return self.repository.clone_url()

        if isinstance(self.details.get("repository"), dict):
            url = self.details["repository"].get("clone_location_https")
            if url:
                return url

        repo_detail_url = self.details.get('repository')
        if repo_detail_url:
            self.repository = KoordinatesClient.instance().retrieve_repository(
                repo_detail_url
            )
        if self.repository:
            return self.repository.clone_url()

        return None
