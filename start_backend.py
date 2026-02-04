#!/usr/bin/env python3
"""启动后端API服务器."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    import uvicorn
    from ytb_dual_subtitles.api.app import app

    print("🚀 启动 YouTube双语字幕系统 API服务器")
    print("="*50)

    # 确保配置已初始化
    try:
        from ytb_dual_subtitles.config.config_service import config_service
        config_service.ensure_config_exists()
        print("✅ 配置系统已初始化")
    except Exception as e:
        print(f"⚠️  配置初始化警告: {e}")

    # 获取服务器配置
    try:
        server_config = config_service.get_server_config()
        host = server_config.get('host', '127.0.0.1')
        port = server_config.get('port', 8000)
        debug = server_config.get('debug', True)  # 开发环境默认启用debug
    except:
        host = '127.0.0.1'
        port = 8000
        debug = True

    print(f"🌐 服务器地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'启用' if debug else '禁用'}")
    print(f"📁 API文档: http://{host}:{port}/docs")

    # 启动服务器
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,  # 开发模式下启用热重载
        log_level="info"
    )