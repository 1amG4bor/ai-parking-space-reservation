from threading import RLock

from chat_engine.core.config.logging import logger


class Singleton(type):
    _type_instances = {}
    _lock = RLock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._type_instances:
                logger.info(f"Creating new singleton instance for {cls.__name__}")
                try:
                    instance = super(Singleton, cls).__call__(*args, **kwargs)
                    cls._type_instances[cls] = instance
                except Exception:  # pylint: disable=broad-except
                    # Keep the original exception and traceback to expose the real root cause.
                    logger.exception(f"Error occurred while creating singleton instance for {cls.__name__}")
                    raise

        return cls._type_instances[cls]
