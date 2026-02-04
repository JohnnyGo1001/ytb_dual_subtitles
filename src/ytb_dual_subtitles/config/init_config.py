#!/usr/bin/env python3
"""配置初始化脚本 - 创建默认配置文件和目录结构."""

import sys
from pathlib import Path

# 添加src到路径以便导入模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ytb_dual_subtitles.config.config_manager import ConfigManager
from ytb_dual_subtitles.exceptions.config_errors import ConfigError


def main():
    """初始化配置的主函数."""
    print("🚀 YouTube双语字幕系统 - 配置初始化")
    print("=" * 50)

    try:
        # 创建配置管理器
        config_manager = ConfigManager()

        # 检查当前状态
        status = config_manager.get_config_status()
        print(f"📁 配置目录: {status['config_directory']}")

        if status['config_directory_exists']:
            print("✅ 配置目录已存在")
        else:
            print("📂 创建配置目录...")

        # 初始化默认配置
        config_manager.initialize_default_configs()

        # 检查配置状态
        print("\n📋 配置文件状态:")
        if status['api_config_exists']:
            print("✅ API配置文件已存在")
        else:
            print("📝 创建API配置模板")

        if status['system_config_exists']:
            print("✅ 系统配置文件已存在")
        else:
            print("📝 创建系统配置模板")

        # 验证配置
        print("\n🔍 配置验证:")
        validation = config_manager.validate_api_config()

        if validation['valid']:
            print("✅ 配置验证通过")
            print(f"✅ 有效服务数: {validation['total_services']}")
        else:
            print("⚠️  配置需要进一步设置:")
            for issue in validation['issues']:
                print(f"   - {issue}")

        # 显示下一步指导
        print("\n📚 下一步操作指南:")
        print(f"1. 编辑API配置文件: {config_manager.api_config_file}")
        print("2. 配置百度翻译API:")
        print("   - 访问 https://fanyi-api.baidu.com/")
        print("   - 申请APP ID和密钥")
        print("   - 将信息填入配置文件并设置enabled: true")
        print("3. (可选) 配置其他API服务")
        print("4. 重新运行此脚本验证配置")

        print("\n🎉 配置初始化完成!")
        return True

    except ConfigError as e:
        print(f"❌ 配置初始化失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)