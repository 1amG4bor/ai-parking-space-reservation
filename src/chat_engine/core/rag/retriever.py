import weaviate
from weaviate.classes.generate import GenerativeConfig

from chat_engine.core.config.config import ConfigManager
from chat_engine.core.config.logging import logger

class ParkingInfoRetriever:

    def __init__(self, top_k: int = 5):
        cfg_manager = ConfigManager()
        self._top_k = top_k or cfg_manager.get_config("RETRIEVAL_TOP_K", 5)
        self._generative_config = GenerativeConfig.ollama(
            api_endpoint=cfg_manager.get_config("RETRIEVAL_API_ENDPOINT"),
            model=cfg_manager.get_config("RETRIEVAL_MODEL"),
        )

    def retrieve(self, query):
        with weaviate.connect_to_local() as client:
            parking_lot_info = client.collections.use("ParkingLotInfo")

            response = parking_lot_info.query.near_text(
                query=query, limit=self._top_k
            )

            
            results = [item.properties for item in response.objects]
            logger.info(f"Retrieved {len(results)} parking information.")
            logger.debug(f"Retrieved parking information ids: {[str(item.uuid) for item in response.objects]}")
            return results
