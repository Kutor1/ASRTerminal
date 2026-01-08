"""
Configuration management.
"""
import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)


# Default configuration
DEFAULT_CONFIG = {
    'app': {
        'name': 'ASR Terminal',
        'version': '1.0.0',
        'debug': False,
        'log_level': 'INFO'
    },
    'engine': {
        'default': 'whisper',
        'priority': ['whisper', 'qwen', 'azure'],
        'fallback': {
            'enabled': True,
            'max_retries': 3,
            'retry_delay': 1.0
        }
    },
    'audio': {
        'sample_rate': 16000,
        'channels': 1,
        'realtime': {
            'chunk_size': 1024,
            'chunk_duration': 0.0625,
            'vad_enabled': True,
            'vad_aggressiveness': 2,
            'silence_threshold': 2.0
        },
        'batch': {
            'normalize': True,
            'split_on_silence': False,
            'min_silence_len': 500
        },
        'preprocessing': ['resample', 'convert_to_mono', 'normalize']
    },
    'output': {
        'console': {
            'enabled': True,
            'show_timestamps': True,
            'show_confidence': False
        },
        'export': {
            'formats': ['txt', 'srt', 'json'],
            'directory': './output'
        }
    },
    'performance': {
        'cache': {
            'enabled': True,
            'directory': './models',
            'max_size_gb': 10
        },
        'batch': {
            'max_workers': 4
        }
    }
}


class ConfigManager:
    """
    Configuration manager.

    Handles loading, merging, and accessing configuration from files and environment variables.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to main configuration file
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._engine_configs: Dict[str, Any] = {}
        self._env_prefix = "ASR_"

        self._load_all_configs()

    def _load_all_configs(self) -> None:
        """Load all configuration files."""
        # Load main config
        self._config = self._load_config_file(self.config_path, DEFAULT_CONFIG)

        # Load engine configs
        engines_config_path = Path("config/engines.yaml")
        if engines_config_path.exists():
            with open(engines_config_path, 'r', encoding='utf-8') as f:
                self._engine_configs = yaml.safe_load(f) or {}

        # Load environment variables
        self._load_env_vars()

        logger.info(f"Configuration loaded from {self.config_path}")

    def _load_config_file(
        self,
        config_path: str,
        default_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            config_path: Path to configuration file
            default_config: Default configuration dictionary

        Returns:
            Merged configuration
        """
        config_file = Path(config_path)

        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}, using defaults")
            return default_config.copy()

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)

            # Merge with defaults
            merged = self._merge_config(default_config, user_config or {})

            logger.info(f"Loaded config from {config_file}")
            return merged

        except Exception as e:
            logger.error(f"Failed to load config {config_path}: {e}")
            return default_config.copy()

    def _load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                config_key = key[len(self._env_prefix):].lower()
                self._set_nested_value(self._config, config_key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., 'audio.sample_rate')
            default: Default value if key not found

        Returns:
            Configuration value

        Examples:
            >>> config.get('audio.sample_rate')
            16000
            >>> config.get('engine.default')
            'whisper'
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-separated key.

        Args:
            key: Dot-separated key
            value: Value to set
        """
        self._set_nested_value(self._config, key, value)

    def _set_nested_value(
        self,
        config: Dict[str, Any],
        key: str,
        value: Any
    ) -> None:
        """
        Set nested configuration value.

        Args:
            config: Configuration dictionary
            key: Dot-separated key
            value: Value to set
        """
        keys = key.split('.')

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_engine_config(self, engine_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific engine.

        Args:
            engine_name: Name of the engine

        Returns:
            Engine configuration dictionary

        Raises:
            ValueError: If engine is not enabled or not found
        """
        if engine_name not in self._engine_configs:
            raise ValueError(
                f"Engine '{engine_name}' not found in configuration. "
                f"Available engines: {list(self._engine_configs.keys())}"
            )

        engine_config = self._engine_configs[engine_name].copy()

        # Check if enabled
        if not engine_config.get('enabled', True):
            raise ValueError(f"Engine '{engine_name}' is disabled in configuration")

        # Substitute environment variables
        engine_config = self._substitute_env_vars(engine_config)

        return engine_config

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.

        Args:
            config: Configuration value (dict, list, or string)

        Returns:
            Configuration with substituted values
        """
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}

        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]

        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            # Extract environment variable name
            env_var = config[2:-1]
            return os.environ.get(env_var, config)

        return config

    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            path: Optional file path (defaults to original config path)
        """
        save_path = path or self.config_path

        config_file = Path(save_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"Configuration saved to {save_path}")

    @staticmethod
    def _merge_config(
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively merge configuration dictionaries.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._merge_config(result[key], value)
            else:
                result[key] = value

        return result
