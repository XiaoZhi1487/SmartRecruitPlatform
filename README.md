# 智聘通 - 智能招聘平台（毕业设计）

基于 **前程无忧(51job)数据爬取 + AI智能分析** 的一站式求职招聘平台。系统通过 Selenium 多线程爬取招聘数据，结合 DeepSeek 大模型提供岗位推荐、简历优化、AI 职业助手等能力，覆盖求职者、企业、管理员三种角色。

## 功能模块

| 模块 | 说明 |
| --- | --- |
| 数据爬取 | Selenium 多线程并发爬取 前程无忧（职位名称/薪资/公司/要求/地点等），UA 随机切换、IP 代理池、请求间隔控制、验证码检测与处理、CDP 附加模式复用登录态、每 6 小时定时自动爬取、真实爬取失败自动降级模拟数据、网站结构变更监测 |
| 用户功能 | JWT 认证注册登录、密码强度校验、邮箱验证、登录失败锁定、简历上传解析（PDF/Word/TXT）、个人信息/教育/工作/技能管理、职位收藏、角色权限管理（user/enterprise/admin） |
| 智能分析 | 动态自适应推荐算法（技能/薪资/城市/经验/学历五维加权，权重由岗位数据区分度 + 用户行为反馈三层动态调节）、企业候选人匹配、DeepSeek 多轮对话、简历 AI 优化建议；职位深度解读与简历优化结果自动归档为 AI 职业助手新对话 |
| 数据可视化 | 招聘市场数据分析（岗位需求排行/岗位平均薪资/学历对薪资影响/学历分布/地区平均薪资排行 + AI 结论），薪资统一折算为 K/月（年÷12、天×22）|
| 系统集成 | 前程无忧原文一键跳转、DeepSeek API 封装（重试/降级）、响应式现代 UI |

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
│   │   │   ├── analysis_service.py # 市场数据分析（薪资折算/聚合/结论）
│   │   │   ├── recommend_service.py # 推荐算法
│   │   │   └── resume_parser.py   # 简历解析
│   │   ├── utils/           # 通用（响应/校验/日志/装饰器）
│   │   ├── config.py        # 配置（含环境变量）
│   │   └── __init__.py      # 应用工厂 + 种子数据 + 定时任务
│   ├── tests/               # pytest 测试
│   ├── drivers/             # 内置 WebDriver（msedgedriver.exe，已在 .gitignore 中忽略）
│   ├── start_edge_debug.py  # 以远程调试端口启动浏览器（供爬虫 CDP 附加复用登录态）
│   ├── requirements.txt
│   └── run.py               # 启动入口
└── frontend/                # Vue3 前端
    ├── src/
    │   ├── views/           # 页面（登录/注册/职位大厅/市场分析/职位详情/我的收藏/智能推荐/AI职业助手/爬虫控制台/简历/个人中心/管理后台）
    │   ├── api/             # Axios 封装与接口定义
    │   ├── router/          # 路由 + 权限守卫
    │   ├── stores/          # Pinia 状态
    │   └── components/      # 公共组件
    ├── package.json
    └── vite.config.js       # 开发代理 /api -> 127.0.0.1:5000
```

## 快速开始

### 环境要求

- Python 3.9+（爬取真实模式需要本机已安装 Edge 或 Chrome 浏览器）
- Node.js 16+

### 浏览器与 WebDriver

- 爬虫默认使用 **Edge**（`CRAWL_BROWSER=edge`），与本地浏览器保持一致，命中验证码时会弹出浏览器窗口便于人工处理。
- WebDriver 默认使用项目内置的 `backend/drivers/msedgedriver.exe`（与 Edge 149 配套）。若更换浏览器或驱动版本，可通过环境变量 `CRAWL_BROWSER_PATH` / `CRAWL_DRIVER_PATH` 指定，或删除后交由 Selenium Manager 自动管理。

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
| `CRAWL_BROWSER` | 浏览器引擎：`edge` / `chrome` | `edge` |
| `CRAWL_BROWSER_PATH` | 浏览器可执行文件路径（留空自动探测常见安装位置） | 空 |
| `CRAWL_DRIVER_PATH` | WebDriver 路径（留空由 Selenium Manager 自动管理） | 项目内置驱动 |
| `CRAWL_ATTACH_PORT` | CDP 附加端口，>0 时优先附加到已运行的 Edge/Chrome（复用登录态），无调试实例时自动回退独立启动，0 禁用 | 9222 |
| `CRAWL_CAPTCHA_WAIT` | 命中验证码后等待人工处理的最长时间（秒） | 180 |
| `MAIL_SERVER` 等 | SMTP 邮箱配置，未配置时验证邮件输出到控制台 | 空 |

### 真实模式说明

爬取目标为 **前程无忧（51job）**，真实（`real`/`auto`）模式无需登录即可访问，处理策略如下：

1. 列表页使用桌面版 SPA（`we.51job.com/pc/search`，`jobArea` 参数真实生效可精确按城市爬取）；「全国」使用手机版搜索源兜底（`we.51job.com/m/search`，不受账号/IP 所在地区锁定影响）。
2. 搜索列表为前端渲染，Worker 会自动等待并滚动页面触发懒加载后提取职位卡片（`.joblist-item`，字段优先取自卡片 `sensorsdata` 属性）；详情描述走 msearch 手机详情页（服务端渲染，可免验证码读取）。
3. 若命中验证码，会自动弹出浏览器窗口交由人工处理（等待 `CRAWL_CAPTCHA_WAIT` 秒），处理完成后继续爬取。
4. 薪资按 K/月统一归一化（`万/月` ×10、`千/月` 原值），供推荐算法与统计使用。
5. 无产出且配置为 `auto` 时，自动降级为模拟数据，保证演示流程不中断。
6. 城市代码（`CRAWL_CITY_CODES`，前端传城市名称自动换算，直接传 6 位代码则原样使用）：`000000`全国、`010000`北京、`020000`上海、`030200`广州、`040000`深圳、`030800`东莞、`060000`重庆、`070200`南京、`070300`苏州、`080200`杭州、`090200`成都、`110200`福州、`120200`济南、`120300`青岛、`140200`南宁、`140400`柳州、`150200`合肥、`160200`石家庄、`170200`郑州、`180200`武汉、`190200`长沙、`200200`西安、`220200`哈尔滨、`230200`沈阳、`240200`长春、`250200`昆明、`260200`贵阳、`280100`呼和浩特。
7. **CDP 附加模式**（`CRAWL_ATTACH_PORT` > 0 时启用）：WebDriver 默认新开独立浏览器进程，不带登录态；如需复用本地浏览器登录态，先完全退出 Edge，再运行 `python start_edge_debug.py` 以 `--remote-debugging-port=9222` 启动，之后爬虫会自动附加到该实例并在其中新开标签页，不再新开浏览器窗口。

## 测试

```bash
cd backend
python -m pytest tests/ -q     # 28 个用例：认证/简历解析/推荐算法/爬虫工具/AI 服务
```

## 说明

- **法律与合规**：爬虫真实模式仅用于学习与研究，请遵守目标网站 Robots 协议及当地法律法规；正式使用建议将 `CRAWL_MODE` 设为 `mock` 或控制爬取频率与规模。
- **生产部署**：开发服务器仅用于演示，生产环境请使用 Gunicorn/Waitress + Nginx，并妥善设置 JWT/数据加密密钥与 SMTP。
