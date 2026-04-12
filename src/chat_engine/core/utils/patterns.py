from threading import RLock

from chat_engine.core.config.logging import logger


class Singleton(type):
    _type_instances = {}
    _lock = RLock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            try:
                if cls not in cls._type_instances:
                    instance = super(Singleton, cls).__call__(*args, **kwargs)
                    cls._type_instances[cls] = instance
            except Exception as err:  # pylint: disable=broad-except
                logger.error(f"Error occurred while creating singleton instance for {cls.__name__}: {err}")

        if cls in cls._type_instances:
            return cls._type_instances[cls]

        # This should not happen, but we add this as a safeguard to ensure that the method always returns an instance.
        error_template = "Failed to create singleton instance for {}. Current singletons: {}"
        raise RuntimeError(error_template.format(cls.__name__, list(cls._type_instances.keys())))
