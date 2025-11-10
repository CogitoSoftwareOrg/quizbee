from ....domain.out import SearcherProvider, Searcher
from ....domain.models import SearchType

from .meili_material_query_searcher import MeiliMaterialQuerySearcher
from .meili_material_distribution_searcher import MeiliMaterialDistributionSearcher
from .meili_all_searcher import MeiliMaterialAllSearcher


class MaterialSearcherProvider(SearcherProvider):
    """
    Provider для получения нужного Searcher в зависимости от типа поиска.

    Поддерживает два типа поиска:
    - QUERY: Поиск по запросу пользователя (MeiliMaterialQuerySearcher)
    - DISTRIBUTION: Равномерное распределение чанков по материалам (MeiliMaterialDistributionSearcher)
    """

    def __init__(
        self,
        query_searcher: MeiliMaterialQuerySearcher,
        distribution_searcher: MeiliMaterialDistributionSearcher,
        all_searcher: MeiliMaterialAllSearcher,
    ):
        self._query_searcher = query_searcher
        self._distribution_searcher = distribution_searcher
        self._all_searcher = all_searcher

    def get(self, search_type: SearchType) -> Searcher:
        """
        Возвращает соответствующий Searcher для указанного типа поиска.

        Args:
            search_type: Тип поиска (QUERY или DISTRIBUTION)

        Returns:
            Searcher: Соответствующая реализация Searcher

        Raises:
            ValueError: Если передан неподдерживаемый тип поиска
        """
        match search_type:
            case SearchType.QUERY:
                return self._query_searcher
            case SearchType.DISTRIBUTION:
                return self._distribution_searcher
            case SearchType.ALL:
                return self._all_searcher
            case _:
                raise ValueError(f"Unknown search type: {search_type}")
