"""配置相关异常类."""


class ConfigError(Exception):
    """配置管理基础异常."""
    pass


class ConfigValidationError(ConfigError):
    """配置验证失败异常."""
    pass


class ConfigNotFoundError(ConfigError):
    """配置文件未找到异常."""
    pass


class ConfigPermissionError(ConfigError):
    """配置文件权限异常."""
    pass