"""
Configuration Loader
Loads symbol-specific YAML configurations and provides merged settings.
"""

import os
import yaml
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and merge configuration files for different trading symbols."""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize config loader.

        Args:
            config_dir: Path to configuration directory (default: 'config')
        """
        self.config_dir = config_dir
        self.default_config = None
        self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default configuration as fallback."""
        default_path = os.path.join(self.config_dir, "default.yaml")
        if os.path.exists(default_path):
            with open(default_path, "r") as f:
                self.default_config = yaml.safe_load(f)

    def get_symbol_from_config(self, symbol: str) -> Optional[str]:
        """
        Extract symbol name for config file lookup.

        Examples:
            'capital.com:EURUSD' -> 'eurusd'
            'EURUSD' -> 'eurusd'
        """
        if ":" in symbol:
            return symbol.split(":")[1].lower()
        return symbol.lower()

    def load_config(self, symbol: str) -> Dict[str, Any]:
        """
        Load configuration for a specific symbol.

        Tries to load symbol-specific config first, falls back to default.

        Args:
            symbol: Trading symbol (e.g., 'capital.com:EURUSD' or 'EURUSD')

        Returns:
            Merged configuration dictionary
        """
        symbol_key = self.get_symbol_from_config(symbol)
        config_path = os.path.join(self.config_dir, f"{symbol_key}.yaml")

        # Load symbol-specific config if available
        symbol_config = None
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                symbol_config = yaml.safe_load(f)

        # Merge with default config
        if symbol_config:
            return self._merge_configs(self.default_config or {}, symbol_config)
        else:
            # Return default or empty config
            return self.default_config or {}

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge override config into base config.

        Args:
            base: Base configuration dictionary
            override: Configuration overrides

        Returns:
            Merged configuration
        """
        merged = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def get_strategy_config(self, symbol: str) -> Dict[str, Any]:
        """
        Get strategy configuration for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Strategy configuration dictionary
        """
        config = self.load_config(symbol)
        return config.get("strategy", {})

    def get_filter_config(self, symbol: str) -> Dict[str, Any]:
        """
        Get filter configuration for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Filter configuration dictionary
        """
        config = self.load_config(symbol)
        return config.get("filters", {})

    def get_full_config(self, symbol: str) -> Dict[str, Any]:
        """
        Get full configuration for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Complete configuration dictionary
        """
        return self.load_config(symbol)


if __name__ == "__main__":
    # Example usage
    loader = ConfigLoader()

    print("=" * 80)
    print("Configuration Loader Demo")
    print("=" * 80)

    symbols = ["capital.com:EURUSD", "capital.com:AUDUSD", "GBPUSD"]

    for symbol in symbols:
        print(f"\n[{symbol}]")
        config = loader.get_full_config(symbol)

        if config:
            print(f"  Description: {config.get('description', 'N/A')}")
            filters = config.get("filters", {})
            print(f"  Sweep Filter: {filters.get('use_sweep_filter', 'N/A')}")
            print(f"  H4 Filter: {filters.get('use_h4_filter', 'N/A')}")
            print(f"  H4 Mode: {filters.get('h4_filter_mode', 'N/A')}")

            expectations = config.get("expectations", {})
            print(f"  Expected Expectancy: {expectations.get('expectancy', 'N/A')}")
            print(f"  Expected Win Rate: {expectations.get('win_rate', 'N/A')}")
        else:
            print("  No configuration found")

    print("\n" + "=" * 80)
