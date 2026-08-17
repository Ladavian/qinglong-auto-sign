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
| **什么值得买** | `script/smzdm/sign_daily_task/main.py` | 签到 + 众测 + 互动 + 能量值系统（已内置，自包含 ✅） | 无需外部仓库 |
| **WPS** | `ql_wps.py` | 任务中心 + 天天领福利（完整版） | 需订阅 [ZaiZaiCat-Checkin](https://github.com/Cat-zaizai/ZaiZaiCat-Checkin) |

> 💡 **说明**: 什么值得买完整功能模块已随本仓库提供（`script/smzdm/`），订阅本仓库即可使用，无需再订阅外部仓库；WPS 完整版仍需订阅 ZaiZaiCat-Checkin

## 快速部署

### 方式一：订阅管理（推荐）

青龙面板 → 订阅管理 → 添加订阅：

```
名称: qinglong-auto-sign
链接: https://github.com/Ladavian/qinglong-auto-sign.git
白名单: ql_
执行前命令: pip3 install requests pycryptodome pillow
```

保存后点击运行即可。

### 方式二：定时拉取

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

在仓库根目录创建 `config/token.json`（参考 `config/template_token.json`）：

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

**青龙面板 → 定时任务 → 添加任务**（脚本自带青龙 Env 头）：

```
名称: 什么值得买签到
命令: python3 /ql/scripts/Ladavian_qinglong-auto-sign_main/script/smzdm/sign_daily_task/main.py
定时规则: 0 8 * * *
```

> 💡 若青龙订阅拉取的仓库目录名不带 `_main` 后缀，将命令中的 `Ladavian_qinglong-auto-sign_main` 改为 `Ladavian_qinglong-auto-sign` 即可（可在青龙文件管理 `/ql/scripts/` 下确认实际目录名）。

完整功能包括：每日签到、众测任务、互动任务、能量值系统、奖励领取等。

**通知**：SMZDM 完整版使用 `config/notification.json` 推送（支持企业微信/钉钉/飞书/Server酱/Bark 等），模板见 `config/template_notification.json`，配置后放入仓库根目录 `config/notification.json` 即可生效。

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

```bash
# 环境变量
pcbeta_username=user1&user2
pcbeta_password=pass1&pass2

# 定时任务
python3 /ql/scripts/Ladavian_qinglong-auto-sign/ql_pcbeta.py
# 建议时间: 0 8 * * *
```

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
