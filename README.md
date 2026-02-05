# YouTube 双语字幕系统

一个支持 YouTube 视频下载、管理和双语字幕播放的现代化 Web 应用。

## 📋 目录

- [产品功能](#-产品功能)
- [安装步骤](#-安装步骤)
- [运行方式](#-运行方式)
- [使用指南](#-使用指南)
- [项目目录](#-项目目录)

---

## ✨ 产品功能

### 核心功能

- **视频下载与管理**
  - 🎥 输入 YouTube URL 快速下载视频
  - 📊 实时显示下载进度、速度和剩余时间
  - 📁 自动分类管理下载的视频
  - 🔍 支持搜索和排序视频列表

- **双语字幕播放**
  - 🎬 内置视频播放器，支持双语字幕同步显示
  - 🌐 自动下载并翻译字幕（支持多种语言）
  - 📥 导出字幕文件（SRT 格式）
  - 🎯 字幕精准定位和高亮显示
---

## ⚠️ 使用前提条件

在开始使用本系统之前，请确保满足以下条件：

### 必备条件

1. **YouTube 账号**
   - 需要有效的 YouTube 账号用于访问视频内容

2. **网络环境**
   - 需要能够正常访问 YouTube 的网络环境（VPN 翻墙工具）
   - 确保网络连接稳定，以便下载视频和字幕

3. **Chrome 浏览器登录**
   - **重要**：在下载视频前，需要使用 Chrome 浏览器登录 YouTube 网站
   - 系统会自动获取 Chrome 浏览器中的 YouTube Cookie，用于验证身份和下载视频
   - 确保 Chrome 浏览器已安装并登录 YouTube 账号

### 准备步骤

```bash
# 1. 确保已安装 Chrome 浏览器
# 2. 打开 Chrome 浏览器访问 https://www.youtube.com
# 3. 使用您的 YouTube 账号登录
# 4. 登录成功后，关闭浏览器即可
# 5. 系统会在下载时自动读取 Cookie 进行身份验证
```

**注意**：如果下载时遇到身份验证问题，请确认 Chrome 浏览器中的 YouTube 登录状态是否有效。

---

## 🚀 安装步骤

### 前置环境准备

假设您使用全新的 Mac 电脑，需要依次安装以下环境：

#### 1. 安装 Homebrew

Homebrew 是 macOS 的包管理器，用于安装其他开发工具。

```bash
# 打开终端（Terminal），执行以下命令
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装完成后，根据提示将 Homebrew 添加到 PATH
```

#### 2. 安装 Python 3.11+

```bash
# 使用 Homebrew 安装 Python
brew install python@3.11

# 验证安装
python3 --version  # 应显示 Python 3.11.x 或更高版本
```

#### 3. 安装 uv（Python 包管理器）

uv 是一个快速的 Python 包管理器，比传统的 pip 更快。

```bash
# 使用 Homebrew 安装 uv
brew install uv

# 验证安装
uv --version
```

#### 4. 安装 Node.js 和 npm

Node.js 用于前端开发和构建。

```bash
# 使用 Homebrew 安装 Node.js（包含 npm）
brew install node

# 验证安装
node --version  # 应显示 v18.x 或更高版本
npm --version
```

#### 5. 安装 Git（可选，用于克隆项目）

```bash
# 使用 Homebrew 安装 Git
brew install git

# 验证安装
git --version
```

### 项目安装

#### 1. 获取项目代码

```bash
# 如果使用 Git
git clone <repository-url>
cd ytb_dual_subtitles

# 或者直接下载项目压缩包并解压
```

#### 2. 安装后端依赖

```bash
# 在项目根目录执行
uv sync

# 如果需要开发工具（可选）
uv sync --extra dev
```

#### 3. 安装前端依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 返回项目根目录
cd ..
```

---

## 🎮 运行方式

### 开发环境运行

适合开发和调试，前后端分别启动。

#### 启动后端服务

```bash
# 在项目根目录执行
uv run python -m ytb_dual_subtitles

# 后端服务将在 http://localhost:8000 启动
```

#### 启动前端服务

```bash
# 打开新的终端窗口，进入前端目录
cd frontend

# 启动前端开发服务器
npm run dev

# 前端应用将在 http://localhost:5173 启动
```

#### 访问应用

打开浏览器访问：
- **前端界面**：http://localhost:5173
- **后端 API 文档**：http://localhost:8000/docs

### 生产环境运行

适合日常使用，前端打包后由后端统一提供服务。

```bash
# 1. 构建前端（只需执行一次）
cd frontend
npm run build
cd ..

# 2. 启动服务
uv run ytb-subtitles

# 访问 http://localhost:8000
```

### 常用命令

```bash
# 停止服务：在终端按 Ctrl + C

# 重启服务：再次执行启动命令

# 查看日志：启动服务后会在终端显示日志
```

---

## 📖 使用指南

### 1. 下载视频

1. 在首页（下载页）的输入框中粘贴 YouTube 视频链接
2. 选择下载选项（视频质量、字幕语言等）
3. 点击"下载"按钮
4. 等待下载完成，可以在"当前下载"区域查看进度

### 2. 浏览视频

1. 点击顶部导航栏的"视频列表"
2. 左侧边栏显示所有分类
   - 点击"全部"查看所有视频
   - 点击特定分类查看该分类下的视频
3. 使用搜索框快速查找视频
4. 点击视频卡片播放视频

### 3. 管理分类

**创建分类**：
1. 在视频列表页左侧边栏底部
2. 点击"➕ 添加分类"按钮
3. 输入分类名称，按回车或点击 ✓ 保存

**编辑分类**：
1. 鼠标悬停在分类上，点击 ✏️ 编辑按钮
2. 修改分类名称，按回车或点击 ✓ 保存

**删除分类**：
1. 鼠标悬停在分类上，点击 🗑️ 删除按钮
2. 确认删除（该分类下的视频会移至"未分类"）

### 4. 管理视频

**移动视频到分类**：
1. 鼠标悬停在视频卡片上
2. 点击右上角的三点菜单（⋮）
3. 选择"🏷️ 移动到分类"
4. 选择目标分类

**导出字幕**：
1. 点击视频卡片右上角的三点菜单（⋮）
2. 选择"📥 导出字幕"
3. 字幕文件会自动下载（SRT 格式）

**删除视频**：
1. 点击视频卡片右上角的三点菜单（⋮）
2. 选择"🗑️ 删除视频"
3. 确认删除

### 5. 观看视频与字幕

1. 点击视频卡片进入播放页
2. 视频自动播放，字幕同步显示
3. 字幕显示格式：
   - 上方：中文翻译
   - 下方：原文（英文）
4. 当前播放的字幕会高亮显示
5. 使用播放器控制栏调整音量、进度等

### 6. 搜索与排序

**搜索视频**：
- 在搜索框输入关键词（标题、频道名称等）
- 按回车或点击搜索按钮

**排序视频**：
- 点击搜索框旁的排序选项
- 支持按创建时间、标题、时长等排序
- 支持升序和降序

---

## 📁 项目目录

```
ytb_dual_subtitles/
│
├── frontend/                      # 前端应用（React + TypeScript）
│   ├── src/
│   │   ├── container/            # 页面容器组件
│   │   │   ├── DownloadPage/     # 下载页面
│   │   │   ├── VideoListPage/    # 视频列表页
│   │   │   └── PlayerPage/       # 播放器页面
│   │   ├── components/           # 通用组件
│   │   ├── services/             # API 服务
│   │   ├── hooks/                # 自定义 Hooks
│   │   ├── contexts/             # React Context
│   │   └── types/                # TypeScript 类型定义
│   ├── package.json              # 前端依赖配置
│   └── vite.config.ts            # Vite 构建配置
│
├── src/ytb_dual_subtitles/       # 后端应用（Python + FastAPI）
│   ├── api/                      # REST API 接口
│   │   ├── app.py               # FastAPI 应用入口
│   │   └── routes/              # API 路由
│   │       ├── downloads.py     # 下载管理 API
│   │       ├── files.py         # 文件管理 API
│   │       ├── categories.py    # 分类管理 API
│   │       └── player.py        # 播放器 API
│   │
│   ├── core/                     # 核心业务逻辑
│   │   ├── database.py          # 数据库管理
│   │   ├── download_manager.py  # 下载管理器
│   │   ├── settings.py          # 配置管理
│   │   └── subtitle_generator.py # 字幕生成器
│   │
│   ├── services/                 # 业务服务层
│   │   ├── youtube_service.py   # YouTube 视频服务
│   │   ├── subtitle_service.py  # 字幕处理服务
│   │   ├── translation_service.py # 翻译服务
│   │   └── file_service.py      # 文件管理服务
│   │
│   ├── models/                   # 数据模型
│   │   ├── video.py             # 视频数据模型
│   │   └── category.py          # 分类数据模型
│   │
│   └── utils/                    # 工具函数
│
├── pyproject.toml                # Python 项目配置
├── uv.lock                       # uv 依赖锁定文件
└── README.md                     # 项目说明文档
```

### 核心模块说明

**前端模块**：
- `DownloadPage`：视频下载页面，输入 URL 并管理下载任务
- `VideoListPage`：视频列表页面，展示和管理已下载的视频
- `PlayerPage`：视频播放页面，播放视频并显示双语字幕

**后端模块**：
- `api/routes`：定义所有 HTTP API 接口
- `core`：核心业务逻辑，如下载管理、数据库操作
- `services`：具体业务服务实现，如 YouTube 视频获取、字幕翻译
- `models`：数据模型定义，与数据库表对应

### 数据存储

默认情况下，系统会在用户主目录下创建 `~/ytb/` 文件夹：

```
~/ytb/
├── videos/          # 视频文件
├── subtitles/       # 字幕文件
└── data/           # 数据库文件
    └── ytb.db      # SQLite 数据库
```

---

## 🔧 常见问题

**问：下载视频时提示"无效的 URL"**
答：请确保粘贴的是完整的 YouTube 视频链接，格式类似：`https://www.youtube.com/watch?v=xxxxx`

**问：字幕没有显示**
答：请确保下载视频时选择了下载字幕选项，或者该视频确实有字幕可用。

**问：视频无法播放**
答：请确认视频文件已完整下载，可以尝试重新下载该视频。

**问：如何修改存储路径**
答：可以通过设置环境变量 `YTB_DOWNLOAD_PATH` 来指定自定义存储路径。

**问：端口被占用无法启动**
答：确保 8000 端口（后端）和 5173 端口（前端开发）没有被其他程序占用。

---

## 📄 许可证

MIT License - 详见 LICENSE 文件。
