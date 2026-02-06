"""配置管理模块 - 管理API配置和系统设置."""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from ytb_dual_subtitles.core.settings import get_settings
from ytb_dual_subtitles.exceptions.config_errors import ConfigError, ConfigValidationError


class ConfigManager:
    """配置管理器 - 负责读取、验证和管理系统配置."""

    def __init__(self, config_dir: Optional[Path] = None):
        """初始化配置管理器.

        Args:
            config_dir: 配置目录路径，默认为 ~/ytb/config/
        """
        if config_dir is None:
            self.config_dir = Path.home() / "ytb" / "config"
        else:
            self.config_dir = Path(config_dir)

        self.api_config_file = self.config_dir / "api_config.yaml"
        self.system_config_file = self.config_dir / "system_config.yaml"

        # 确保配置目录存在
        self._ensure_config_directory()

    def _ensure_config_directory(self) -> None:
        """确保配置目录存在."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigError(f"Failed to create config directory: {e}") from e

    def initialize_default_configs(self) -> None:
        """初始化默认配置文件."""
        # 创建API配置模板
        if not self.api_config_file.exists():
            self._create_api_config_template()

        # 创建系统配置模板
        if not self.system_config_file.exists():
            self._create_system_config_template()

    def _create_api_config_template(self) -> None:
        """创建API配置模板文件."""
        template_config = {
            'translation': {
                'baidu': {
                    'app_id': 'YOUR_BAIDU_APP_ID_HERE',
                    'secret_key': 'YOUR_BAIDU_SECRET_KEY_HERE',
                    'enabled': False,
                    'description': '百度翻译API配置，请在https://fanyi-api.baidu.com/申请'
                },
                'google': {
                    'api_key': 'YOUR_GOOGLE_API_KEY_HERE',
                    'enabled': False,
                    'description': 'Google翻译API配置（备选方案）'
                }
            },
            'youtube': {
                'api_key': 'YOUR_YOUTUBE_API_KEY_HERE',
                'enabled': False,
                'description': 'YouTube API密钥，用于获取视频信息'
            },
            'version': '1.0',
            'created_at': '2026-02-03',
            'notes': [
                '这是API配置文件，请根据需要填入相应的API密钥',
                '将enabled设置为true以启用对应的服务',
                '请妥善保管此文件，避免泄露API密钥'
            ]
        }

        try:
            with open(self.api_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        except IOError as e:
            raise ConfigError(f"Failed to create API config template: {e}") from e

    def _create_system_config_template(self) -> None:
        """创建系统配置模板文件，从 Settings 读取默认值."""
        settings = get_settings()

        template_config = {
            'download': {
                'path': str(settings.download_path),
                'max_concurrent': settings.max_concurrent_downloads,
                'quality': '1080p',
                'format': settings.yt_dlp_merge_output_format
            },
            'subtitles': {
                'default_languages': settings.yt_dlp_subtitle_languages.split(','),
                'sync_tolerance': 0.1,
                'cache_enabled': True,
                'cache_ttl_days': 7
            },
            'server': {
                'host': settings.host,
                'port': settings.port,
                'debug': settings.debug
            },
            'logging': {
                'level': settings.log_level,
                'file_enabled': True,
                'file_path': str(settings.data_path / 'logs' / 'app.log')
            },
            'version': '1.0',
            'last_updated': '2026-02-06'
        }

        try:
            with open(self.system_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        except IOError as e:
            raise ConfigError(f"Failed to create system config template: {e}") from e

    def load_api_config(self) -> Dict[str, Any]:
        """加载API配置.

        Returns:
            API配置字典

        Raises:
            ConfigError: 配置加载失败
        """
        if not self.api_config_file.exists():
            raise ConfigError(f"API config file not found: {self.api_config_file}")

        try:
            with open(self.api_config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ConfigError("Invalid API config format")

            return config
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse API config: {e}") from e
        except IOError as e:
            raise ConfigError(f"Failed to read API config: {e}") from e

    def load_system_config(self) -> Dict[str, Any]:
        """加载系统配置.

        Returns:
            系统配置字典

        Raises:
            ConfigError: 配置加载失败
        """
        if not self.system_config_file.exists():
            raise ConfigError(f"System config file not found: {self.system_config_file}")

        try:
            with open(self.system_config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ConfigError("Invalid system config format")

            return config
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse system config: {e}") from e
        except IOError as e:
            raise ConfigError(f"Failed to read system config: {e}") from e

    def get_translation_config(self, service: str) -> Dict[str, Any]:
        """获取特定翻译服务的配置.

        Args:
            service: 翻译服务名称 ('baidu', 'google')

        Returns:
            翻译服务配置

        Raises:
            ConfigError: 配置不存在或无效
        """
        api_config = self.load_api_config()
        translation_config = api_config.get('translation', {})

        if service not in translation_config:
            raise ConfigError(f"Translation service '{service}' not configured")

        service_config = translation_config[service]
        if not isinstance(service_config, dict):
            raise ConfigError(f"Invalid config for translation service '{service}'")

        return service_config

    def is_service_enabled(self, service_type: str, service_name: str) -> bool:
        """检查服务是否启用.

        Args:
            service_type: 服务类型 ('translation', 'youtube')
            service_name: 服务名称

        Returns:
            服务是否启用
        """
        try:
            api_config = self.load_api_config()
            service_config = api_config.get(service_type, {}).get(service_name, {})
            return service_config.get('enabled', False)
        except ConfigError:
            return False

    def validate_api_config(self) -> Dict[str, Any]:
        """验证API配置的有效性.

        Returns:
            验证结果字典
        """
        try:
            config = self.load_api_config()
            issues = []
            valid_services = []

            # 验证翻译服务配置
            translation_config = config.get('translation', {})
            for service, service_config in translation_config.items():
                if not isinstance(service_config, dict):
                    issues.append(f"Invalid config format for translation service: {service}")
                    continue

                if service_config.get('enabled', False):
                    # 检查必需的配置项
                    if service == 'baidu':
                        required_fields = ['app_id', 'secret_key']
                        for field in required_fields:
                            value = service_config.get(field, '')
                            if not value or value.startswith('YOUR_'):
                                issues.append(f"Baidu translation: {field} not configured")
                            else:
                                valid_services.append(f"baidu_translation")

                    elif service == 'google':
                        api_key = service_config.get('api_key', '')
                        if not api_key or api_key.startswith('YOUR_'):
                            issues.append("Google translation: api_key not configured")
                        else:
                            valid_services.append("google_translation")

            # 验证YouTube API配置
            youtube_config = config.get('youtube', {})
            if youtube_config.get('enabled', False):
                api_key = youtube_config.get('api_key', '')
                if not api_key or api_key.startswith('YOUR_'):
                    issues.append("YouTube API: api_key not configured")
                else:
                    valid_services.append("youtube_api")

            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'valid_services': valid_services,
                'total_services': len(valid_services),
                'config_file': str(self.api_config_file)
            }

        except ConfigError as e:
            return {
                'valid': False,
                'issues': [str(e)],
                'valid_services': [],
                'total_services': 0,
                'config_file': str(self.api_config_file)
            }

    def update_service_status(self, service_type: str, service_name: str, enabled: bool) -> None:
        """更新服务启用状态.

        Args:
            service_type: 服务类型
            service_name: 服务名称
            enabled: 是否启用

        Raises:
            ConfigError: 更新失败
        """
        try:
            config = self.load_api_config()

            if service_type not in config:
                config[service_type] = {}

            if service_name not in config[service_type]:
                raise ConfigError(f"Service {service_type}.{service_name} not found in config")

            config[service_type][service_name]['enabled'] = enabled

            # 保存更新后的配置
            with open(self.api_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)

        except (IOError, yaml.YAMLError) as e:
            raise ConfigError(f"Failed to update service status: {e}") from e

    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态信息.

        Returns:
            配置状态字典
        """
        return {
            'config_directory': str(self.config_dir),
            'config_directory_exists': self.config_dir.exists(),
            'api_config_exists': self.api_config_file.exists(),
            'system_config_exists': self.system_config_file.exists(),
            'api_config_file': str(self.api_config_file),
            'system_config_file': str(self.system_config_file),
            'validation': self.validate_api_config()
        }