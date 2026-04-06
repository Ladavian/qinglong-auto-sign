# 青龙面板签到脚本集合

适用于青龙面板的自动化签到脚本，支持多账号配置和自定义 webhook 通知。

## 支持的站点

- [x] 远景论坛 (PCBeta) - `ql_pcbeta.py`
- [x] 绿联论坛 (UGreen Discuz) - `ql_ugreen.py`
- [x] 什么值得买 (SMZDM) - `ql_smzdm.py`
- [x] 恩山论坛 (Enshan) - `ql_enshan.py`
- [x] WPS - `ql_wps.py`

---

## 快速开始

### 方式一：订阅管理（推荐）

青龙面板 2.12+ 版本支持订阅管理功能，可以更方便地管理和更新脚本。

#### 1. 添加订阅

在青龙面板 → **订阅管理** → **添加订阅**：

| 配置项 | 值 |
|--------|-----|
| 名称 | `qinglong-auto-sign` |
| 类型 | `公开仓库` |
| 链接 | `https://github.com/Ladavian/qinglong-auto-sign.git` |
| 定时类型 | `crontab` |
| 定时规则 | `0 0 * * *` |
| 文件后缀 | `.py` |
| 白名单 | `ql_` |
| 依赖文件 | `requirements.txt` |
| 执行前命令 | `pip3 install requests pycryptodome` |
| 是否启用 | ✅ 是 |

点击 **确定** 保存。

#### 2. 运行订阅

在订阅列表中找到刚添加的订阅，点击右侧的 **运行** 按钮。

脚本会自动下载到 `/ql/scripts/Ladavian_qinglong-auto-sign/` 目录，并自动创建对应的定时任务。

#### 3. 配置环境变量

在青龙面板 → 环境变量中添加对应变量（见下方各站点配置）。

#### 4. 修改签到时间

订阅运行后，会自动创建定时任务。在 **定时任务** 列表中找到对应的任务，修改定时规则即可。

---

### 方式二：定时拉取任务

适用于旧版本青龙面板或不使用订阅管理的用户。

#### 1. 添加定时拉取任务

在青龙面板 → 定时任务中添加：

```
名称: 拉取签到脚本
命令: ql repo https://github.com/Ladavian/qinglong-auto-sign.git "ql_" "" "requirements.txt"
定时规则: 0 0 * * *
```

**命令说明：**
- `ql repo` - 青龙内置的仓库拉取命令
- `https://github.com/Ladavian/qinglong-auto-sign.git` - 仓库地址
- `"ql_"` - 只拉取以 `ql_` 开头的文件（签到脚本）
- `""` - 不依赖特定文件
- `"requirements.txt"` - 需要保留的依赖文件

点击运行一次，脚本会自动下载到 `/ql/scripts/Ladavian_qinglong-auto-sign/` 目录。

#### 2. 安装依赖

在青龙容器终端执行：
```bash
pip3 install requests pycryptodome
```

> **注意**: 绿联论坛签到需要 `pycryptodome` 库用于 AES 加密

#### 3. 配置环境变量

在青龙面板 → 环境变量中添加对应变量（见下方各站点配置）。

#### 4. 添加签到任务

脚本拉取后会自动出现在定时任务列表中，修改定时规则即可。

#### 1. 克隆仓库

在青龙容器终端执行：

```bash
cd /ql/scripts
git clone https://github.com/Ladavian/qinglong-auto-sign.git
cd qinglong-auto-sign
pip3 install requests pycryptodome
```

#### 2. 配置环境变量和定时任务

见下方各站点配置说明。

---

## 站点配置

### 远景论坛 (PCBeta)

#### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `pcbeta_username` | 用户名 | `your_username` |
| `pcbeta_password` | 密码 | `your_password` |

**多账号配置**（使用 `&`、`@` 或换行符分隔）：

```
pcbeta_username: user1&user2&user3
pcbeta_password: pass1&pass2&pass3
```

#### 定时任务

```
名称: 远景论坛签到
命令: python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_pcbeta.py
定时规则: 0 8 * * *
```

---

### 绿联论坛 (UGreen Discuz)

#### 环境变量

**方式一：使用 Cookie（推荐，更稳定）**

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ugreen_cookie` | 登录后的 Cookie 字符串 | `6LQh_2132_auth=xxx; 6LQh_2132_saltkey=xxx` |

**方式二：使用用户名密码（Cookie 失效时自动登录）**

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ugreen_username` | 用户名 | `your_username` |
| `ugreen_password` | 密码 | `your_password` |

> **提示**: 可以同时配置 Cookie 和用户名密码。脚本会优先使用 Cookie，当 Cookie 失效时自动通过 OAuth 登录获取新 Cookie。

**多账号配置**（使用 `&`、`@` 或换行符分隔）：

```
# Cookie 方式
ugreen_cookie: cookie1&cookie2&cookie3

# 或用户名密码方式
ugreen_username: user1&user2&user3
ugreen_password: pass1&pass2&pass3
```

#### 如何获取 Cookie

1. 浏览器打开 https://club.ugnas.com/ 并登录
2. 按 F12 打开开发者工具
3. 切换到 Network（网络）标签
4. 刷新页面，点击任意请求
5. 在 Request Headers 中找到 `Cookie` 字段
6. 复制整个 Cookie 值到 `ugreen_cookie` 环境变量

#### 定时任务

```
名称: 绿联论坛签到
命令: python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_ugreen.py
定时规则: 0 8 * * *
```

#### 工作原理

1. **优先使用 Cookie**：直接使用配置的 Cookie 访问论坛完成签到
2. **Cookie 检测**：每次签到前检查 Cookie 是否有效
3. **自动刷新**：Cookie 失效时，自动通过 OAuth API 登录获取新 Cookie
4. **访问即签到**：Discuz 论坛访问用户主页即完成签到

---

### 什么值得买 (SMZDM)

#### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `smzdm_cookie` | Cookie 字符串 | `your_cookie_here` |

**多账号配置**（使用 `&`、`@` 或换行符分隔）：

```
smzdm_cookie: cookie1&cookie2&cookie3
```

#### 如何获取 Cookie

1. 浏览器打开 https://www.smzdm.com/ 并登录
2. 按 F12 打开开发者工具
3. 切换到 Network（网络）标签
4. 刷新页面，点击任意请求
5. 在 Request Headers 中找到 `Cookie` 字段
6. 复制整个 Cookie 值

#### 定时任务

```
名称: 什么值得买签到
命令: python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_smzdm.py
定时规则: 0 8 * * *
```

---

### 恩山论坛 (Enshan)

#### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `enshan_username` | 用户名 | `your_username` |
| `enshan_password` | 密码 | `your_password` |

**多账号配置**（使用 `&`、`@` 或换行符分隔）：

```
enshan_username: user1&user2&user3
enshan_password: pass1&pass2&pass3
```

#### 定时任务

```
名称: 恩山论坛签到
命令: python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_enshan.py
定时规则: 0 8 * * *
```

---

### WPS

#### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `wps_cookie` | Cookie 字符串（需要包含 wps_sid） | `your_cookie_here` |

**多账号配置**（使用 `&`、`@` 或换行符分隔）：

```
wps_cookie: cookie1&cookie2&cookie3
```

#### 如何获取 Cookie

1. 浏览器打开 https://www.wps.cn/ 并登录
2. 按 F12 打开开发者工具
3. 切换到 Network（网络）标签
4. 刷新页面，点击任意请求
5. 在 Request Headers 中找到 `Cookie` 字段
6. 复制整个 Cookie 值（确保包含 `wps_sid`）

#### 定时任务

```
名称: WPS签到
命令: python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_wps.py
定时规则: 0 9 * * *
```

---

## 自定义通知 Webhook

所有脚本都支持通过自定义 webhook 发送签到结果通知。

### 配置

在青龙面板 → 环境变量中添加：

```
名称: CUSTOM_WEBHOOK_URL
值: https://your-webhook-url.com/api/notify
```

> **提示**: 此配置同时适用于本项目和 ZaiZaiCat-Checkin 等其他项目，实现统一通知管理。

### Webhook 请求格式

**请求方式:** POST  
**Content-Type:** application/json; charset=utf-8

**请求体:**
```json
{
  "title": "签到结果",
  "content": "账号1(user1): ✓ 签到成功\n积分: 100",
  "timestamp": 1712345678
}
```

### 支持的 Webhook 服务

- 企业微信机器人
- 钉钉机器人
- 飞书机器人
- Server酱
- 任何支持 JSON POST 的自定义 API

### 多项目统一配置

如果你同时使用多个签到项目，只需配置一次 `CUSTOM_WEBHOOK_URL`，所有项目都会自动使用同一个 webhook 地址：

- ✅ qinglong-auto-sign（本项目）
- ✅ ZaiZaiCat-Checkin（配合 webhook_wrapper.py）
- ✅ 其他支持该变量的项目

---

## 目录结构

```
qinglong-auto-sign/
├── ql_pcbeta.py       # 远景论坛签到脚本
├── ql_ugreen.py       # 绿联论坛签到脚本
├── requirements.txt   # Python依赖
└── README.md          # 说明文档
```

---

## 注意事项

1. **账号安全**: 请确保账号密码正确，避免频繁登录失败导致账号锁定
2. **签到频率**: 建议设置合理的签到时间（如每天一次），避免频繁请求
3. **依赖安装**: 绿联论坛需要安装 `pycryptodome` 库
4. **通知配置**: `NOTIFY_WEBHOOK` 是可选的，不配置不影响签到功能
5. **多账号延迟**: 多账号签到之间会自动延迟 5 秒，避免请求过快
6. **脚本更新**: 
   - 订阅方式：在订阅管理中点击"运行"即可更新
   - 定时任务方式：`ql repo` 任务会每天自动拉取最新脚本
7. **青龙版本**: 订阅功能需要青龙面板 2.12+ 版本

---

## 常见问题

### Q: 如何使用订阅方式拉取脚本？
A: 在青龙面板 → 订阅管理 → 添加订阅，填写仓库地址 `https://github.com/Ladavian/qinglong-auto-sign.git`，白名单填写 `ql_`，保存后点击运行即可。

### Q: 订阅和定时任务有什么区别？
A: 订阅管理是青龙 2.12+ 的新功能，可以更直观地管理脚本仓库，支持自动创建定时任务、安装依赖等功能。定时任务方式需要手动配置更多参数。

### Q: 如何使用 ql repo 命令拉取脚本？
A: 在青龙面板 → 定时任务中添加任务：
```
命令: ql repo https://github.com/Ladavian/qinglong-auto-sign.git "ql_"
```
运行后即可自动拉取脚本到 `/ql/scripts/Ladavian_qinglong-auto-sign/` 目录。

### Q: 绿联论坛签到失败，提示"加密失败"？
A: 请确保已安装 `pycryptodome` 库：
```bash
pip3 install pycryptodome
```

### Q: 如何查看签到日志？
A: 在青龙面板 → 定时任务 → 点击任务右侧的"日志"按钮查看。

### Q: 支持哪些通知方式？
A: 支持任何接受 JSON POST 请求的 webhook 服务，包括企业微信、钉钉、飞书等。

### Q: 如何测试脚本是否正常工作？
A: 可以在青龙面板中手动运行一次任务，查看日志输出。

### Q: 脚本更新后如何获取最新版本？
A: 
- **订阅方式**: 在订阅管理中点击对应订阅的"运行"按钮
- **定时任务方式**: 重新运行 `ql repo` 拉取任务

### Q: 拉取的脚本路径是什么？
A: 默认路径为 `/ql/scripts/Ladavian_qinglong-auto-sign/ql_xxx.py`

### Q: 我的青龙版本不支持订阅功能怎么办？
A: 可以使用定时任务方式（`ql repo` 命令）或手动部署方式。
