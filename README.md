# YouTube 双语字幕系统

一个支持 YouTube 视频下载和双语字幕播放的现代化 Web 应用。

## 功能特性

- 🎥 YouTube 视频下载和管理
- 🔄 实时下载进度显示
- 🎬 视频播放和双语字幕同步显示
- 🌐 现代化的 React Web 用户界面
- 📁 本地视频文件管理
- 🌍 多语言翻译支持
- ⚡ 异步处理和 WebSocket 实时通信
- 🔒 完善的错误处理和异常管理

## 项目结构

```
ytb-dual-subtitles/
├── .github/                          # GitHub 配置文件
├── .idea/                            # PyCharm IDE 配置
├── config/                           # 配置文件目录
├── scripts/                          # 脚本工具
├── static/                           # 静态资源
├── main.py                           # 主程序入口
├── pyproject.toml                    # Python 项目配置
├── uv.lock                           # UV 依赖锁定文件
├── pyrightconfig.json                # Pyright 类型检查配置
├── README.md                         # 项目说明文档
├── PROJECT_OVERVIEW.md               # 项目概览文档
│
├── src/ytb_dual_subtitles/          # 主要源代码
│   ├── __init__.py                   # 包初始化文件
│   ├── __main__.py                   # 模块主入口
│   │
│   ├── api/                         # REST API 接口层
│   │   ├── __init__.py
│   │   ├── app.py                   # FastAPI 应用入口
│   │   └── routes/                  # API 路由模块
│   │       ├── __init__.py
│   │       ├── downloads.py         # 下载相关路由
│   │       ├── files.py             # 文件操作路由
│   │       └── player.py            # 播放器相关路由
│   │
│   ├── core/                        # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── database.py              # 数据库管理
│   │   ├── download_manager.py      # 下载管理器
│   │   ├── error_handling.py        # 错误处理
│   │   ├── player.py                # 视频播放器核心
│   │   ├── settings.py              # 配置管理
│   │   └── subtitle_generator.py    # 字幕生成器
│   │
│   ├── services/                    # 业务服务层
│   │   ├── __init__.py
│   │   ├── file_service.py          # 文件服务
│   │   ├── metadata_service.py      # 元数据服务
│   │   ├── storage_management.py    # 存储管理
│   │   ├── storage_service.py       # 存储服务
│   │   ├── subtitle_data_service.py # 字幕数据服务
│   │   ├── subtitle_service.py      # 字幕服务
│   │   ├── translation_service.py   # 翻译服务
│   │   └── youtube_service.py       # YouTube 服务
│   │
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   └── video.py                 # 视频数据模型
│   │
│   ├── utils/                       # 工具函数
│   │   ├── __init__.py
│   │   └── subtitle_utils.py        # 字幕工具函数
│   │
│   ├── exceptions/                  # 自定义异常
│   │   ├── __init__.py
│   │   ├── download_errors.py       # 下载异常
│   │   ├── file_errors.py          # 文件异常
│   │   └── subtitle_errors.py      # 字幕异常
│   │
│   └── web/                         # WebSocket 和 Web 服务
│       ├── __init__.py
│       └── websocket.py             # WebSocket 连接管理
│
└── frontend/                        # React 前端应用
    ├── package.json                 # Node.js 依赖配置
    ├── package-lock.json            # npm 锁定文件
    ├── tsconfig.json                # TypeScript 配置
    ├── tsconfig.node.json           # Node.js TypeScript 配置
    ├── vite.config.ts               # Vite 构建配置
    └── src/                         # React 源代码
        ├── main.tsx                 # 应用入口
        ├── App.tsx                  # 主应用组件
        ├── components/              # React 组件
        │   ├── common/              # 通用组件
        │   ├── download/            # 下载相关组件
        │   ├── layout/              # 布局组件
        │   ├── player/              # 播放器组件
        │   └── video/               # 视频相关组件
        ├── contexts/                # React 上下文
        ├── hooks/                   # 自定义 Hooks
        ├── pages/                   # 页面组件
        ├── services/                # 前端服务
        ├── types/                   # TypeScript 类型定义
        ├── utils/                   # 前端工具函数
        └── styles/                  # 样式文件
```

### 架构说明

#### 后端架构
- **API 层**: FastAPI 基础的 REST API
- **核心层**: 业务逻辑和核心功能
- **服务层**: 具体业务服务实现
- **模型层**: 数据模型定义
- **工具层**: 通用工具函数
- **异常层**: 自定义异常处理

#### 前端架构
- **组件化**: React 组件化开发
- **状态管理**: Context API 状态管理
- **类型安全**: TypeScript 类型检查
- **构建工具**: Vite 快速构建

#### 开发特性
- **类型检查**: Python 类型提示 + TypeScript
- **代码质量**: Ruff + ESLint 代码检查
- **自动化**: Pre-commit hooks 自动检查

## 技术栈

- **后端**: Python 3.11+, FastAPI, uvicorn
- **前端**: React, TypeScript, Vite
- **视频处理**: yt-dlp
- **数据存储**: SQLite (生产环境可使用 PostgreSQL)
- **异步处理**: asyncio, aiofiles
- **实时通信**: WebSockets
- **翻译服务**: Google Translate API
- **开发工具**: uv, ruff, mypy

## 快速开始

### 环境要求

- Python 3.11 或更高版本
- Node.js 16+ (用于前端开发)

### 项目设置

#### 1. 克隆项目
```bash
git clone <repository-url>
cd ytb-dual-subtitles
```

#### 2. 安装依赖

```bash
# 使用 uv 安装 Python 依赖（推荐）
uv sync

# 安装开发依赖
uv sync --extra dev

# 或使用 pip
pip install -e .

# 安装前端依赖
cd frontend
npm install
```

#### 3. 设置开发环境
```bash
# 设置 pre-commit 钩子（可选）
uv run pre-commit install
```

### 开发环境启动

1. **启动后端服务**:
```bash
# 使用 uv 运行（推荐）
uv run python -m ytb_dual_subtitles
```

2. **启动前端开发服务器**:
```bash
cd frontend
npm run dev
```

### 生产环境部署

```bash
# 构建前端
cd frontend
npm run build

# 启动生产服务器
uv run ytb-subtitles
```

### 访问应用

- **开发环境**:
  - 后端 API: http://localhost:8000
  - 前端应用: http://localhost:5173
- **生产环境**: http://localhost:8000

## API 接口

### 统一响应格式

所有 API 接口都返回统一的响应格式：

```json
{
  "success": true,         // 操作是否成功
  "data": {...},          // 实际返回的数据
  "error_code": null,     // 错误码（仅在失败时）
  "error_msg": null       // 错误信息（仅在失败时）
}
```

### 主要端点

**下载管理**:
- `POST /api/downloads` - 创建下载任务
- `GET /api/downloads/{task_id}` - 获取下载任务状态
- `GET /api/list/downloads` - 获取所有下载任务列表
- `DELETE /api/downloads/{task_id}` - 取消下载任务
- `GET /api/status` - 获取所有任务状态（用于轮询）
- `GET /api/status/{task_id}` - 获取特定任务状态

**文件管理**:
- `GET /api/videos` - 获取视频列表（支持搜索、分页、筛选）
- `DELETE /api/videos/{video_id}` - 删除视频及相关文件

**系统信息**:
- `GET /` - 系统健康检查
- `GET /health` - 详细健康状态

### 错误码

常用错误码定义：

- `INVALID_URL` - 无效的 YouTube URL
- `DOWNLOAD_FAILED` - 下载失败
- `TASK_NOT_FOUND` - 任务未找到
- `FILE_NOT_FOUND` - 文件未找到
- `VALIDATION_ERROR` - 请求参数验证错误
- `INTERNAL_ERROR` - 内部服务器错误

**文档资源**:
- 交互式 API 文档: http://localhost:8000/docs
- API 使用示例: [API_EXAMPLES.md](./API_EXAMPLES.md)
- Redoc 文档: http://localhost:8000/redoc

## 文件存储

系统会自动创建以下目录结构来存储下载的视频、字幕和相关文件：

### 默认存储路径

```
~/ytb/                              # 用户主目录下的 ytb 文件夹
├── videos/                         # 视频文件存储目录
│   ├── [视频标题].mp4              # 下载的视频文件
│   ├── [视频标题].webm             # 或其他格式的视频文件
│   └── ...
│
├── subtitles/                      # 字幕文件存储目录
│   ├── [视频标题]/                 # 按视频分组的字幕文件夹
│   │   ├── [视频标题].en.vtt       # 英文字幕文件
│   │   ├── [视频标题].zh-CN.vtt    # 中文简体字幕文件
│   │   ├── [视频标题].zh-TW.vtt    # 中文繁体字幕文件
│   │   └── [视频标题].[lang].vtt   # 其他语言字幕文件
│   └── ...
│
└── data/                           # 应用数据目录
    ├── ytb.db                      # SQLite 数据库文件
    ├── thumbnails/                 # 视频缩略图
    └── metadata/                   # 视频元数据
```

### 支持的文件格式

#### 视频格式
- **MP4** (推荐): 兼容性最佳，支持所有现代浏览器
- **WebM**: Google 开发的开放格式
- **MKV**: 高质量视频格式
- **AVI**: 传统视频格式
- **MOV**: QuickTime 视频格式

#### 字幕格式
- **VTT** (推荐): Web 标准字幕格式，支持样式和定位
- **SRT**: 通用字幕格式，简单易用
- **ASS/SSA**: 高级字幕格式，支持复杂样式

#### 支持的字幕语言
- **en**: 英语
- **zh-CN**: 中文简体
- **zh-TW**: 中文繁体
- **ja**: 日语
- **ko**: 韩语
- **es**: 西班牙语
- **fr**: 法语
- **de**: 德语

### 自定义存储路径

可以通过环境变量自定义存储路径：

```bash
# 设置自定义视频存储路径
export YTB_DOWNLOAD_PATH="/path/to/your/videos"

# 设置自定义字幕存储路径
export YTB_SUBTITLE_PATH="/path/to/your/subtitles"

# 设置自定义数据存储路径
export YTB_DATA_PATH="/path/to/your/data"
```

或在项目根目录创建 `.env` 文件：

```env
YTB_DOWNLOAD_PATH=/path/to/your/videos
YTB_SUBTITLE_PATH=/path/to/your/subtitles
YTB_DATA_PATH=/path/to/your/data
```

### 文件命名规则

- **视频文件**: 使用 YouTube 视频标题作为文件名，自动清理不安全字符
- **字幕文件**: 格式为 `[视频标题].[语言代码].[格式后缀]`
- **特殊字符处理**: 自动替换或移除文件系统不支持的字符
- **重复文件**: 如果文件已存在，会自动添加数字后缀

### 存储空间管理

- **默认限制**: 单个文件最大 5GB
- **自动清理**: 支持清理临时文件和不完整的下载
- **空间检查**: 下载前自动检查可用磁盘空间
- **压缩优化**: 自动选择合适的视频质量以节省空间

## 代码质量

项目严格遵循 Python 编码规范，使用多种工具确保代码质量：

### 代码格式化和检查
```bash
# 检查代码
uv run ruff check .

# 自动修复代码问题
uv run ruff check . --fix

# 格式化代码
uv run ruff format .
```

### 类型检查
```bash
# 运行类型检查
uv run mypy src/ytb_dual_subtitles/
```

### 依赖管理
```bash
# 添加新的生产依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 更新所有依赖
uv sync --upgrade
```

## 开发指南

### 开发最佳实践

项目遵循现代化的 Python 开发最佳实践：

- **架构设计**: 使用 FastAPI 构建高性能 Web API，采用分层架构
- **异步编程**: 采用 asyncio 和异步编程模式提高并发性能
- **前端技术**: 集成 React + TypeScript + Vite 现代前端技术栈
- **错误处理**: 完善的错误处理和日志记录机制
- **异步处理**: 采用 asyncio 和异步编程模式提高并发性能

### 开发流程

1. **功能开发**:
   - 创建功能分支：`git checkout -b feature/your-feature-name`
   - 编写代码并遵循项目规范
   - 运行代码检查确保质量合规
   - 提交代码：`git commit -m "feat: add new feature"`

2. **代码审查**:
   - 推送分支：`git push origin feature/your-feature-name`
   - 创建 Pull Request
   - 等待代码审查和合并

3. **发布流程**:
   - 更新版本号
   - 创建发布标签
   - 部署到生产环境

## 故障排除

### 常见问题

1. **模块导入错误**:
   ```bash
   # 确保在项目根目录并已安装依赖
   uv sync
   ```

2. **前端无法访问后端 API**:
   - 检查后端服务是否运行在 http://localhost:8000
   - 确认 CORS 设置正确

3. **类型检查失败**:
   ```bash
   # 检查 mypy 配置和类型注解
   uv run mypy src/ytb_dual_subtitles/ --show-error-codes
   ```

4. **代码检查失败**:
   ```bash
   # 运行详细代码检查
   uv run ruff check . --show-source
   uv run mypy src/ytb_dual_subtitles/ --show-error-codes
   ```

## 贡献

欢迎提交 Issue 和 Pull Request！在提交代码前，请确保：

1. 代码通过 lint 检查和类型检查
2. 遵循项目编码规范
3. 更新了相关文档

## 许可证

MIT License - 详见 LICENSE 文件。
