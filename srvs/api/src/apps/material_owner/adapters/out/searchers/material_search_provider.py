from ....domain.out import SearcherProvider, Searcher
from ....domain.models import SearchType

from .meili_material_query_searcher import MeiliMaterialQuerySearcher
from .meili_material_distribution_searcher import MeiliMaterialDistributionSearcher
from .meili_all_searcher import MeiliMaterialAllSearcher
from .meili_material_vector_searcher import MeiliMaterialVectorSearcher


class MaterialSearcherProvider(SearcherProvider):
    """
    Provider для получения нужного Searcher в зависимости от типа поиска.

    Поддерживает типы поиска:
    - QUERY: Поиск по запросу пользователя (MeiliMaterialQuerySearcher)
    - DISTRIBUTION: Равномерное распределение чанков по материалам (MeiliMaterialDistributionSearcher)
    - ALL: Получение всех чанков (MeiliMaterialAllSearcher)
    - VECTOR: Поиск по векторам (MeiliMaterialVectorSearcher)
    """

    def __init__(
        self,
        query_searcher: MeiliMaterialQuerySearcher,
        distribution_searcher: MeiliMaterialDistributionSearcher,
        all_searcher: MeiliMaterialAllSearcher,
        vector_searcher: MeiliMaterialVectorSearcher,
    ):
        self._query_searcher = query_searcher
        self._distribution_searcher = distribution_searcher
        self._all_searcher = all_searcher
        self._vector_searcher = vector_searcher

    def get(self, search_type: SearchType) -> Searcher:
        """
        Возвращает соответствующий Searcher для указанного типа поиска.

        Args:
            search_type: Тип поиска (QUERY, DISTRIBUTION, ALL или VECTOR)

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
            case SearchType.VECTOR:
                return self._vector_searcher
            case _:
                raise ValueError(f"Unknown search type: {search_type}")
