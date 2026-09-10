# 智聘通 - 智能招聘平台（毕业设计）

基于 **Boss直聘数据爬取 + AI智能分析** 的一站式求职招聘平台。系统通过 Selenium 多线程爬取招聘数据，结合 DeepSeek 大模型提供岗位推荐、简历优化、AI 职业助手等能力，覆盖求职者、企业、管理员三种角色。

## 功能模块

| 模块 | 说明 |
| --- | --- |
| 数据爬取 | Selenium 多线程并发爬取 Boss直聘（职位名称/薪资/公司/要求/地点等），UA 随机切换、IP 代理池、请求间隔控制、验证码检测与处理、真实爬取失败自动降级模拟数据、网站结构变更监测 |
| 用户功能 | JWT 认证注册登录、密码强度校验、邮箱验证、登录失败锁定、简历上传解析（PDF/Word/TXT）、个人信息/教育/工作/技能管理、角色权限管理（user/enterprise/admin） |
| 智能分析 | AI 岗位推荐算法（技能/薪资/城市/经验/学历多维匹配）、企业候选人匹配、DeepSeek 多轮对话、简历 AI 优化建议 |
| 系统集成 | Boss直聘原文一键跳转、DeepSeek API 封装（重试/降级）、响应式现代 UI |

## 技术栈

- **后端**：Python 3.9+ · Flask 3 · Flask-SQLAlchemy · Flask-JWT-Extended · Flask-Bcrypt · APScheduler · Selenium
- **前端**：Vue 3 · Vite · Element Plus · Pinia · Vue Router · Axios · ECharts
- **数据库**：SQLite
- **AI**：DeepSeek Chat Completions API

## 目录结构

```
毕业设计/
├── backend/                 # Flask 后端
│   ├── app/
│   │   ├── api/             # 接口层（auth/user/jobs/resume/crawl/chat/recommend/admin）
│   │   ├── models/          # 数据模型（用户/职位/简历/交互/画像）
│   │   ├── services/
│   │   │   ├── crawler/     # 爬虫（管理器/反检测/代理池/验证码/结构监测/模拟数据）
│   │   │   ├── ai_service.py      # DeepSeek 封装
│   │   │   ├── recommend_service.py # 推荐算法
│   │   │   └── resume_parser.py   # 简历解析
│   │   ├── utils/           # 通用（响应/校验/日志/装饰器）
│   │   ├── config.py        # 配置（含环境变量）
│   │   └── __init__.py      # 应用工厂 + 种子数据 + 定时任务
│   ├── tests/               # pytest 测试
│   ├── requirements.txt
│   └── run.py               # 启动入口
└── frontend/                # Vue3 前端
    ├── src/
    │   ├── views/           # 页面（登录/注册/职位大厅/详情/推荐/AI对话/爬虫/简历/个人中心/管理后台）
    │   ├── api/             # Axios 封装与接口定义
    │   ├── router/          # 路由 + 权限守卫
    │   ├── stores/          # Pinia 状态
    │   └── components/      # 公共组件
    ├── package.json
    └── vite.config.js       # 开发代理 /api -> 127.0.0.1:5000
```

## 快速开始

### 环境要求

- Python 3.9+（爬取真实模式需要安装 Chrome 与对应版本 [ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/)）
- Node.js 16+

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python run.py          # 默认 0.0.0.0:5000
```

首次启动自动建库并写入种子数据（演示职位、默认账号）。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173，已代理 /api 到后端
```

### 默认账号

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `Admin@123456` |
| 演示用户 | `demo` | `Demo@123456` |

## 配置说明（环境变量）

后端配置位于 `backend/app/config.py`，均可通过环境变量覆盖：

| 变量 | 说明 | 默认 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（AI 功能） | 已内置项目密钥 |
| `SECRET_KEY` / `JWT_SECRET_KEY` | 应用/令牌签名密钥 | 开发默认值 |
| `DATA_ENCRYPTION_KEY` | 敏感字段加密密钥，为空时自动生成 | 空 |
| `CRAWL_MODE` | 爬取模式：`real` 真实 / `mock` 模拟 / `auto` 失败自动降级 | `auto` |
| `CRAWL_THREADS` | 并发线程数 | 3 |
| `CRAWL_DELAY_MIN` / `CRAWL_DELAY_MAX` | 请求间隔（秒） | 6 / 10 |
| `CRAWL_PROXY_LIST` | 代理池（逗号分隔） | 空 |
| `CRAWL_HEADLESS` | 无头模式 | 1 |
| `MAIL_SERVER` 等 | SMTP 邮箱配置，未配置时验证邮件输出到控制台 | 空 |

## 测试

```bash
cd backend
python -m pytest tests/ -q     # 22 个用例：认证/简历解析/推荐算法/爬虫工具
```

## 说明

- **法律与合规**：爬虫真实模式仅用于学习与研究，请遵守目标网站 Robots 协议及当地法律法规；正式使用建议将 `CRAWL_MODE` 设为 `mock` 或控制爬取频率与规模。
- **生产部署**：开发服务器仅用于演示，生产环境请使用 Gunicorn/Waitress + Nginx，并妥善设置 JWT/数据加密密钥与 SMTP。
