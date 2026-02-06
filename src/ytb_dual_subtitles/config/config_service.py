"""配置服务 - 为系统其他模块提供配置访问接口."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional

from ytb_dual_subtitles.config.config_manager import ConfigManager
from ytb_dual_subtitles.core.settings import get_settings
from ytb_dual_subtitles.exceptions.config_errors import ConfigError


class ConfigService:
    """配置服务 - 提供全局配置访问接口."""

    _instance: Optional['ConfigService'] = None

    def __new__(cls) -> 'ConfigService':
        """单例模式实现."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化配置服务."""
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._config_manager = ConfigManager()
        self._api_config_cache: Optional[Dict[str, Any]] = None
        self._system_config_cache: Optional[Dict[str, Any]] = None
        self._initialized = True

    def ensure_config_exists(self) -> None:
        """确保配置文件存在，如不存在则创建默认配置."""
        try:
            self._config_manager.initialize_default_configs()
        except ConfigError:
            # 如果创建失败，继续使用内存中的默认配置
            pass

    @lru_cache(maxsize=1)
    def get_api_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """获取API配置，带缓存.

        Args:
            force_reload: 是否强制重新加载

        Returns:
            API配置字典
        """
        if force_reload:
            self.get_api_config.cache_clear()
            self._api_config_cache = None

        if self._api_config_cache is None:
            try:
                self._api_config_cache = self._config_manager.load_api_config()
            except ConfigError:
                # 返回默认配置
                self._api_config_cache = self._get_default_api_config()

        return self._api_config_cache

    def _get_default_api_config(self) -> Dict[str, Any]:
        """获取默认API配置."""
        return {
            'translation': {
                'baidu': {
                    'app_id': '',
                    'secret_key': '',
                    'enabled': False
                },
                'google': {
                    'api_key': '',
                    'enabled': False
                }
            },
            'youtube': {
                'api_key': '',
                'enabled': False
            }
        }

    @lru_cache(maxsize=1)
    def get_system_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """获取系统配置，带缓存.

        Args:
            force_reload: 是否强制重新加载

        Returns:
            系统配置字典
        """
        if force_reload:
            self.get_system_config.cache_clear()
            self._system_config_cache = None

        if self._system_config_cache is None:
            try:
                self._system_config_cache = self._config_manager.load_system_config()
            except ConfigError:
                # 返回默认配置
                self._system_config_cache = self._get_default_system_config()

        return self._system_config_cache

    def _get_default_system_config(self) -> Dict[str, Any]:
        """获取默认系统配置."""
        return {
            'download': {
                'path': '~/ytb/videos/',
                'max_concurrent': 3,
                'quality': '1080p',
                'format': 'mp4'
            },
            'subtitles': {
                'default_languages': get_settings().yt_dlp_subtitle_languages.split(','),
                'sync_tolerance': 0.1,
                'cache_enabled': True,
                'cache_ttl_days': 7
            },
            'server': {
                'host': get_settings().host,
                'port': get_settings().port,
                'debug': get_settings().debug
            },
            'logging': {
                'level': get_settings().log_level,
                'file_enabled': True,
                'file_path': str(get_settings().data_path / 'logs' / 'app.log')
            }
        }

    def get_translation_config(self, service: str) -> Optional[Dict[str, Any]]:
        """获取翻译服务配置.

        Args:
            service: 翻译服务名称

        Returns:
            翻译服务配置，如果不存在或未启用返回None
        """
        api_config = self.get_api_config()
        translation_config = api_config.get('translation', {})
        service_config = translation_config.get(service, {})

        if service_config.get('enabled', False):
            return service_config

        return None

    def get_baidu_translation_config(self) -> Optional[Dict[str, Any]]:
        """获取百度翻译配置."""
        return self.get_translation_config('baidu')

    def get_google_translation_config(self) -> Optional[Dict[str, Any]]:
        """获取Google翻译配置."""
        return self.get_translation_config('google')

    def is_translation_service_available(self) -> bool:
        """检查是否有可用的翻译服务."""
        return (
            self.get_baidu_translation_config() is not None or
            self.get_google_translation_config() is not None
        )

    def get_download_config(self) -> Dict[str, Any]:
        """获取下载配置."""
        system_config = self.get_system_config()
        return system_config.get('download', self._get_default_system_config()['download'])

    def get_subtitle_config(self) -> Dict[str, Any]:
        """获取字幕配置."""
        system_config = self.get_system_config()
        return system_config.get('subtitles', self._get_default_system_config()['subtitles'])

    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置."""
        system_config = self.get_system_config()
        return system_config.get('server', self._get_default_system_config()['server'])

    def get_expanded_download_path(self) -> str:
        """获取展开的下载路径."""
        download_config = self.get_download_config()
        path = download_config.get('path', '~/ytb/videos/')
        return os.path.expanduser(path)

    def validate_configuration(self) -> Dict[str, Any]:
        """验证当前配置的有效性."""
        return self._config_manager.validate_api_config()

    def reload_config(self) -> None:
        """重新加载配置."""
        self.get_api_config(force_reload=True)
        self.get_system_config(force_reload=True)


# 创建全局配置服务实例
config_service = ConfigService()