# SearXNG Proxy Search — Open WebUI 互联网搜索扩展工具

一个可部署到 **Zeabur** 的独立搜索代理服务，内置 SearXNG 搜索引擎，支持通过 **SOCKS5 静态住宅 IP** 代理搜索互联网内容，并提供配套的 **Open WebUI Tool 插件**。

---

## ✨ 功能特性

- 🔍 **多引擎聚合搜索** — 内置 SearXNG，聚合 Google、Bing、DuckDuckGo、Brave、Wikipedia 等搜索引擎
- 🌐 **静态住宅 IP 代理** — 支持 SOCKS5 代理，通过静态住宅 IP 发起搜索请求，避免被封锁
- 🖥️ **Web 管理面板** — 暗色主题管理界面，可在线配置代理地址、测试连接、快速搜索
- 🔌 **Open WebUI 插件** — 提供即用的 Tool 插件文件，复制到 Open WebUI 即可让 AI 模型搜索互联网
- 🚀 **一键部署** — 支持 Zeabur / Docker 一键部署，开箱即用
- 🔑 **API Key 鉴权** — 可选的 API 密钥保护，防止未授权访问

---

## 📦 项目结构

```
openwebui_serch/
├── main.py                  # FastAPI 主入口 (API + Web 面板)
├── searxng_client.py        # SearXNG 搜索客户端封装
├── config.py                # 配置管理 (SOCKS5 代理等)
├── templates/
│   └── index.html           # Web 管理面板
├── static/
│   └── style.css            # 面板样式
├── searxng/
│   └── settings.yml         # SearXNG 配置
├── openwebui_tool.py        # Open WebUI Tool 插件文件
├── Dockerfile               # Docker 构建文件
├── docker-compose.yml       # 本地开发
├── supervisord.conf         # 进程管理
└── requirements.txt         # Python 依赖
```

---

## 🚀 部署方式

### Zeabur 部署（推荐）

1. Fork 本仓库或将代码推送到你的 GitHub
2. 登录 [Zeabur](https://zeabur.com)，新建项目
3. 选择 Git 仓库部署，Zeabur 会自动识别 Dockerfile 并构建
4. 部署完成后访问服务 URL，打开管理面板配置 SOCKS5 代理

### Docker 本地部署

```bash
git clone https://github.com/austin0056/openwebui_serch.git
cd openwebui_serch
docker-compose up -d
```

访问 `http://localhost:8080` 打开管理面板。

---

## 🔧 使用方法

### 1. 配置代理

访问服务地址（如 `https://your-service.zeabur.app`），在管理面板中：

- 填入 SOCKS5 代理地址（格式：`socks5://用户名:密码@地址:端口`）
- 设置 API 密钥（可选，用于保护搜索 API）
- 点击「测试代理连接」验证连通性
- 点击「保存配置」

### 2. 安装 Open WebUI 插件

1. 复制 `openwebui_tool.py` 文件内容
2. 在 Open WebUI 中进入 **Workspace → Tools → 创建工具**
3. 粘贴代码并保存
4. 点击齿轮图标，在 Valves 中填入：
   - `api_base_url`：你的服务地址
   - `api_key`：管理面板中设置的 API 密钥
5. 启用工具，AI 模型即可调用搜索功能

### 3. API 接口

**搜索**
```bash
curl -X POST https://your-service.zeabur.app/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"query": "搜索关键词", "num_results": 5}'
```

**抓取网页**
```bash
curl -X POST https://your-service.zeabur.app/api/fetch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"url": "https://example.com"}'
```

---

## 🌐 静态住宅 IP 代理推荐

> **[moon9.cloud](https://moon9.cloud)** — 优质网络中转服务站
>
> 提供稳定、高速的静态住宅 IP 代理和网络中转服务，适用于搜索引擎访问、数据采集、跨境业务等场景。
>
> 🔗 **访问 [moon9.cloud](https://moon9.cloud) 获取优质代理服务**

---

## 📄 License

MIT
