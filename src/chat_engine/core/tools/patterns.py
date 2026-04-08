import logging
from threading import Lock

logger = logging.getLogger(__name__)


class Singleton(type):
    _type_instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            try:
                if cls not in cls._type_instances:
                    instance = super(Singleton, cls).__call__(*args, **kwargs)
                    cls._type_instances[cls] = instance
            except Exception as err:  # pylint: disable=broad-except
                logger.error(f"Error occurred while creating singleton instance for {cls.__name__}: {err}")

        return cls._type_instances[cls]
