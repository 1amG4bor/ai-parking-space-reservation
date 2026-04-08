import logging
from threading import Lock

logger = logging.getLogger(__name__)


class Singleton(type):
    _type_instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        cls._lock.acquire()
        try:
            if cls not in cls._type_instances:
                instance = super(Singleton, cls).__call__(*args, **kwargs)
                cls._type_instances[cls] = instance
        except Exception as err:
            logger.error(f"Error occurred while creating singleton instance for {cls.__name__}: {err}")
        finally:
            cls._lock.release()

        return cls._type_instances[cls]
