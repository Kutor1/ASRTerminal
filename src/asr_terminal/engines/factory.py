"""
Engine factory for creating and managing speech recognition engines.
"""
from typing import Dict, Type, Optional
from ..exceptions import EngineNotFoundError
from .base import ASREngine, EngineConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EngineFactory:
    """
    Factory class for creating and managing speech recognition engines.

    Uses the factory pattern to provide a unified interface for engine creation.
    """

    # Registry of available engines
    _engines: Dict[str, Type[ASREngine]] = {}
    _configs: Dict[str, Type[EngineConfig]] = {}
    _instances: Dict[str, ASREngine] = {}

    @classmethod
    def register_engine(
        cls,
        name: str,
        engine_class: Type[ASREngine],
        config_class: Type[EngineConfig]
    ) -> None:
        """
        Register a new engine.

        This allows for extending the system with custom engines.

        Args:
            name: Engine name
            engine_class: Engine class (must inherit from ASREngine)
            config_class: Config class (must inherit from EngineConfig)

        Example:
            >>> class MyEngine(ASREngine):
            ...     pass
            >>> EngineFactory.register_engine("my_engine", MyEngine, MyConfig)
        """
        cls._engines[name] = engine_class
        cls._configs[name] = config_class
        logger.info(f"Registered engine: {name}")

    @classmethod
    async def create_engine(
        cls,
        name: str,
        config: Optional[Dict] = None
    ) -> ASREngine:
        """
        Create an engine instance.

        Args:
            name: Engine name
            config: Configuration dictionary

        Returns:
            Initialized engine instance

        Raises:
            EngineNotFoundError: If engine is not registered
        """
        if name not in cls._engines:
            raise EngineNotFoundError(name, cls.list_engines())

        # Create configuration object
        config_class = cls._configs[name]
        engine_config = config_class(**(config or {}))

        # Create engine instance
        engine_class = cls._engines[name]
        engine = engine_class(engine_config)

        # Initialize engine
        logger.info(f"Initializing engine: {name}")
        await engine.initialize()

        # Cache instance
        cls._instances[name] = engine

        logger.info(f"Engine created successfully: {name}")
        return engine

    @classmethod
    def get_engine(cls, name: str) -> Optional[ASREngine]:
        """
        Get an existing engine instance.

        Args:
            name: Engine name

        Returns:
            Engine instance or None if not found
        """
        return cls._instances.get(name)

    @classmethod
    async def get_or_create_engine(
        cls,
        name: str,
        config: Optional[Dict] = None
    ) -> ASREngine:
        """
        Get existing or create new engine instance.

        Args:
            name: Engine name
            config: Configuration dictionary (used only if creating new)

        Returns:
            Engine instance
        """
        engine = cls.get_engine(name)
        if engine is None:
            engine = await cls.create_engine(name, config)
        return engine

    @classmethod
    def list_engines(cls) -> list[str]:
        """
        List all registered engines.

        Returns:
            List of engine names
        """
        return list(cls._engines.keys())

    @classmethod
    async def cleanup_engine(cls, name: str) -> None:
        """
        Clean up a specific engine.

        Args:
            name: Engine name
        """
        engine = cls._instances.get(name)
        if engine:
            await engine.cleanup()
            del cls._instances[name]
            logger.info(f"Engine cleaned up: {name}")

    @classmethod
    async def cleanup_all(cls) -> None:
        """Clean up all engine instances."""
        for name in list(cls._instances.keys()):
            await cls.cleanup_engine(name)
        logger.info("All engines cleaned up")
