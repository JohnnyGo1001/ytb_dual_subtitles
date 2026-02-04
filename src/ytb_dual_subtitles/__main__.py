"""YouTube 双语字幕系统包入口点.

当使用 `python -m ytb_dual_subtitles` 运行包时执行此文件。
"""

from __future__ import annotations


def main() -> None:
    """启动 YouTube 双语字幕系统.

    配置并启动 FastAPI 应用服务器。
    """
    import uvicorn

    # 启动 FastAPI 应用
    uvicorn.run(
        "ytb_dual_subtitles.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()