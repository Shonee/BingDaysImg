# BingDaysImg 使用指南

## 项目简介

每天自动从必应获取每日壁纸，通过 GitHub Actions 定时运行 Python 脚本，将壁纸数据存储为 JSON 并生成静态 HTML 页面，最终通过 GitHub Pages 展示。

**零外部依赖**：纯 Python 标准库实现，无需 `pip install`。

## 初始化步骤

### 1. 创建 GitHub 仓库

在 GitHub 上创建一个新的公开仓库（如 `BingDaysImg`）。

### 2. 准备项目文件

仓库初始只需要 **3 个文件**：

```
BingDaysImg/
├── .github/workflows/
│   └── update-wallpaper.yml   # GitHub Actions 工作流
├── .gitignore                 # Git 忽略规则
└── fetch_bing.py              # Python 主脚本
```

将这三个文件推送到仓库 `main` 分支：

```bash
git init
git add .
git commit -m "init: 必应每日壁纸项目"
git remote add origin https://github.com/<你的用户名>/BingDaysImg.git
git branch -M main
git push -u origin main
```

### 3. 配置 GitHub Actions 权限

1. 进入仓库页面，点击 **Settings**
2. 左侧菜单选择 **Actions → General**
3. 滚动到 **Workflow permissions** 部分
4. 选择 **Read and write permissions**
5. 点击 **Save**

> 这一步确保 Actions 有权限将壁纸更新推送回仓库。

### 4. 配置 GitHub Pages

1. 进入仓库页面，点击 **Settings**
2. 左侧菜单选择 **Pages**
3. **Source** 选择 `Deploy from a branch`
4. **Branch** 选择 `main`，目录选择 `/ (root)`
5. 点击 **Save**

等待部署完成后，访问 `https://<你的用户名>.github.io/BingDaysImg/` 即可看到页面。

### 5. 首次手动触发

1. 进入仓库页面，点击 **Actions** 标签
2. 左侧选择 **更新必应壁纸** 工作流
3. 点击 **Run workflow → Run workflow**

首次运行后，脚本会自动生成以下文件：

```
BingDaysImg/
├── data/2026-07.json          # 当月壁纸数据
├── archives/2026-07.html      # 当月归档页面
├── index.html                 # 首页
└── README.md                  # 项目说明
```

## 自动运行

配置完成后，GitHub Actions 会在每天 **北京时间 0:00**（UTC 16:00）自动执行：

1. 调用必应 API 获取当日壁纸数据
2. 保存到 `data/YYYY-MM.json`
3. 重新生成所有 HTML 页面和 README.md
4. 自动提交并推送到仓库
5. GitHub Pages 自动部署更新

## 本地调试

```bash
python3 fetch_bing.py
```

运行后会在当前目录生成 `data/`、`archives/`、`index.html`、`README.md`。

## 项目特点

- 纯 Python 标准库，零依赖安装
- 单文件脚本，逻辑清晰易维护
- 暗色沉浸式 UI，支持 Lightbox 灯箱浏览
- 支持 4K 原图下载
- 按月自动归档
- 键盘左右箭头翻页

## 参考项目

- [bing.shenzjd.com](https://github.com/wu529778790/bing.shenzjd.com)
