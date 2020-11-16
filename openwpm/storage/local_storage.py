from .arrow_storage import ArrowProvider
from .storage_providers import UnstructuredStorageProvider


class LocalArrowProvider(ArrowProvider):
    ...


class LocalGzipProvider(UnstructuredStorageProvider):
    ...
