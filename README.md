# 青龙面板自动签到脚本

完全独立的青龙面板签到脚本，支持独立运行和配合外部仓库两种模式。

## 支持站点

### 独立脚本（推荐 ⭐）
无需订阅外部仓库，开箱即用：

| 站点 | 脚本 | 功能 |
|------|------|------|
| **什么值得买** | `ql_smzdm_standalone.py` | 每日签到（基础版） |
| **WPS** | `ql_wps_standalone.py` | 天天领福利 + 任务中心 |
| **恩山论坛** | `ql_enshan.py` | 论坛签到（Cookie/账密） |
| **远景论坛** | `ql_pcbeta.py` | 论坛签到 |
| **绿联论坛** | `ql_ugreen.py` | 论坛签到（Cookie/OAuth） |

### 完整功能版

| 站点 | 脚本 | 功能 | 依赖 |
|------|------|------|------|
| **什么值得买** | `ql_smzdm.py` | 签到 + 众测 + 互动 + 能量值系统（已内置，自包含 ✅） | 无需外部仓库 |
| **WPS** | `ql_wps.py` | 任务中心 + 天天领福利（完整版） | 需订阅 [ZaiZaiCat-Checkin](https://github.com/Cat-zaizai/ZaiZaiCat-Checkin) |

> 💡 **说明**: 什么值得买完整功能模块已随本仓库提供（`script/smzdm/`），订阅本仓库即可使用，无需再订阅外部仓库；WPS 完整版仍需订阅 ZaiZaiCat-Checkin

## 快速部署

### 方式一：daidai-panel（呆呆面板）

面板 → 订阅管理 → 添加订阅：

```
链接: https://github.com/Ladavian/qinglong-auto-sign.git
保存目录: qinglong-auto-sign
白名单: ql_
依赖规则: script/smzdm, notification.py, config
定时同步: 0 0 * * *
```

- 白名单 `ql_`：匹配 `ql_` 开头的文件建成定时任务（如 `ql_smzdm.py`）
- 依赖规则：`script/smzdm`（API/任务模块）、`notification.py`（通知模块）、`config`（配置模板）会被拉取到脚本目录供主脚本调用，但**不会**建成任务（匹配为子串包含，`,` 或 `|` 均可分隔）

SMZDM 任务的命令为 `python ql_smzdm.py`，账号用面板「环境变量」配置（见下文），通知走面板内置的 18 种渠道，任务运行时自动生效。

### 方式二：青龙订阅管理

青龙面板 → 订阅管理 → 添加订阅：

```
名称: qinglong-auto-sign
链接: https://github.com/Ladavian/qinglong-auto-sign.git
白名单: ql_
执行前命令: pip3 install requests pycryptodome pillow
```

保存后点击运行即可。

### 方式三：青龙定时拉取

青龙面板 → 定时任务 → 添加任务：

```
名称: 拉取签到脚本
命令: ql repo https://github.com/Ladavian/qinglong-auto-sign.git "ql_" "" "requirements.txt"
定时规则: 0 0 * * *
```

## 配置说明

### 通用环境变量

所有脚本都支持以下通知配置（可选）：

```bash
CUSTOM_WEBHOOK_URL=https://your-webhook-url.com/api/notify
```

### 各站点配置

#### 什么值得买 (SMZDM)

**方式一：独立脚本（基础版）**

```bash
# 环境变量
smzdm_cookie=cookie1&cookie2&cookie3

# 定时任务
python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_smzdm_standalone.py
# 建议时间: 0 8 * * *
```

**获取 Cookie：**
1. 浏览器登录 https://www.smzdm.com/
2. F12 → Network → 刷新页面
3. 复制请求头中的 Cookie 值

**方式二：完整功能版（推荐，已内置）**

SMZDM 完整功能模块已随本仓库提供（`script/smzdm/`），无需订阅外部仓库。

**配置账号（二选一）：**

方式 A：面板「环境变量」（daidai-panel / 青龙通用，推荐）：

```
smzdm_cookie=cookie1&cookie2&cookie3     # 多账号用 &、@ 或换行分隔
SMZDM_USER_AGENT=Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X) ...   # 手机 App 抓包得到的 UA，勿用 PC 浏览器 UA
```

> 💡 `SMZDM_USER_AGENT` 必须填**手机（iPhone）App** 请求的 User-Agent（与 `smzdm_cookie` 同一抓包会话），脚本的签名与风控按 App 环境设计，PC 浏览器 UA 会导致请求被拒。

方式 B：仓库根目录创建 `config/token.json`（参考 `config/template_token.json`）：

```json
{
  "smzdm": {
    "accounts": [
      {
        "name": "账号1",
        "cookie": "你的Cookie",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X)...",
        "setting": ""
      }
    ]
  }
}
```

**青龙面板 → 订阅管理 / `ql repo` 拉取后，`ql_smzdm.py` 会自动出现在任务列表中**（白名单 `ql_` 匹配），直接编辑定时规则运行即可：

```
名称: ql_smzdm.py
命令: task ql_smzdm.py
定时规则: 0 8 * * *
```

> 💡 `ql_smzdm.py` 只是入口启动器：它通过 `os.path.realpath` 定位本仓库真实目录（兼容青龙将脚本软链到 `/ql/scripts/` 的执行方式），再调用内置的 `script/smzdm/sign_daily_task/main.py`。若面板任务里没有出现，在订阅管理中把白名单保持为 `ql_` 并重新运行一次订阅即可。

完整功能包括：每日签到、众测任务、互动任务、能量值系统、奖励领取等。

**通知**：SMZDM 完整版支持两种方式：
1. 设置环境变量 `CUSTOM_WEBHOOK_URL`（通用 JSON POST，兼容任意通知服务，格式见下方"Webhook 通知"）；
2. 使用 `config/notification.json` 推送（支持企业微信/钉钉/飞书/Server酱/Bark 等，模板见 `config/template_notification.json`）。

---

#### WPS

**方式一：独立脚本（推荐）**

```bash
# 环境变量
wps_cookie=cookie1&cookie2&cookie3

# 定时任务
python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_wps_standalone.py
# 建议时间: 0 9 * * *
```

**获取 Cookie：**
1. 浏览器登录 https://www.wps.cn/
2. F12 → Network → 刷新页面
3. 复制包含 `wps_sid` 的 Cookie 值

**方式二：完整功能版（需外部仓库）**

需要先订阅 ZaiZaiCat-Checkin 仓库，然后在 `config/token.json` 中配置账号。

```bash
# 环境变量
wps_config_path=/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin/config/token.json

# 定时任务
python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_wps.py
# 建议时间: 0 9 * * *
```

---

#### 恩山论坛

```bash
# 方式一：Cookie（推荐）
enshan_cookie=cookie1&cookie2&cookie3

# 方式二：用户名密码（备用）
enshan_username=user1&user2
enshan_password=pass1&pass2

# 定时任务
python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_enshan.py
# 建议时间: 0 8 * * *
```

**获取 Cookie：**
1. 浏览器登录 https://www.right.com.cn/
2. F12 → Network → 刷新页面
3. 复制请求头中的 Cookie 值

---

#### 远景论坛 (PCBeta)

远景的签到是**回帖打卡任务**（申请任务 → 到打卡帖回复 → 领取 PB币），任务 id 与打卡帖每期变化，脚本会自动识别。

**方式一：Cookie（推荐，绕开登录风控）**

```bash
# 环境变量（浏览器登录 https://i.pcbeta.com 后，F12 → Application → Cookies 复制 jqCP_887f_auth 的值）
pcbeta_cookie=jqCP_887f_auth=xxx&jqCP_887f_auth=yyy     # 多账号用 & 分隔
pcbeta_reply_content=打卡签到                             # 可选，回帖内容（默认"打卡签到"）

# 定时任务
python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_pcbeta.py
# 建议时间: 0 8 * * *
```

**方式二：账号密码（备用）**

```bash
pcbeta_username=user1&user2
pcbeta_password=pass1&pass2
```

> 💡 远景登录有失败次数限制，连续失败会临时封锁 IP；Cookie 有效期约一个月，失效时重新复制一次即可。

---

#### 绿联论坛

```bash
# 方式一：Cookie（推荐）
ugreen_cookie=6LQh_2132_auth=xxx; 6LQh_2132_saltkey=xxx

# 方式二：用户名密码（Cookie失效时自动登录）
ugreen_username=user1&user2
ugreen_password=pass1&pass2

# 定时任务
python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_ugreen.py
# 建议时间: 0 8 * * *
```

**获取 Cookie：**
1. 浏览器登录 https://club.ugnas.com/
2. F12 → Network → 刷新页面
3. 复制请求头中的 Cookie 值

---

## 多账号配置

所有脚本都支持多账号，使用 `&`、`@` 或换行符分隔：

```bash
# 示例：SMZDM 多账号
smzdm_cookie=cookie1&cookie2&cookie3

# 示例：用户名密码多账号
enshan_username=user1&user2&user3
enshan_password=pass1&pass2&pass3
```

## Webhook 通知

配置 `CUSTOM_WEBHOOK_URL` 后，签到结果会自动发送到指定地址。

**请求格式：**
```json
{
  "title": "签到结果",
  "content": "账号1: 签到成功\n积分: 100",
  "timestamp": 1712345678
}
```

**支持的服务：**
- 企业微信机器人
- 钉钉机器人
- 飞书机器人
- Server酱
- 任意支持 JSON POST 的 API

## 依赖安装

首次使用需要安装依赖：

```bash
pip3 install requests pycryptodome pillow
```

> **注意**：绿联论坛需要 `pycryptodome` 库用于加密；什么值得买完整版需要 `pillow` 库（图片验证码处理）

## 常见问题

**Q: 脚本会被覆盖吗？**  
A: 不会。所有脚本都是独立的，不依赖外部仓库，订阅更新不会影响你的配置。

**Q: 如何查看签到日志？**  
A: 青龙面板 → 定时任务 → 点击任务右侧的"日志"按钮。

**Q: 绿联论坛提示"加密失败"？**  
A: 执行 `pip3 install pycryptodome` 安装加密库。

**Q: 如何测试脚本？**  
A: 青龙面板中手动运行一次任务，查看日志输出。

## 目录结构

```
qinglong-auto-sign/
├── ql_smzdm.py               # 什么值得买（完整功能版入口，自动被 ql_ 白名单拉取）
├── ql_smzdm_standalone.py    # 什么值得买（独立基础版）
├── ql_wps_standalone.py      # WPS（独立完整版）
├── ql_pcbeta.py              # 远景论坛
├── ql_ugreen.py              # 绿联论坛
├── ql_enshan.py              # 恩山论坛
├── notification.py           # 通知模块（SMZDM 完整版依赖）
├── script/
│   └── smzdm/                # 什么值得买完整功能模块（自包含）
│       ├── api/              # API 封装 + 签名计算
│       └── sign_daily_task/  # 任务入口（main.py）+ 服务层（service.py）
├── config/
│   ├── template_token.json   # 账号配置模板（复制为 token.json 使用）
│   └── template_notification.json
├── requirements.txt          # Python依赖
└── README.md                 # 说明文档
```
