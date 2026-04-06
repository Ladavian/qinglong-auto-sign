# 青龙面板自动签到脚本

完全独立的青龙面板签到脚本，无需订阅外部仓库，开箱即用。

## 支持站点

| 站点 | 脚本 | 功能 |
|------|------|------|
| **什么值得买** | `ql_smzdm_standalone.py` | 每日签到 + 众测任务 + 互动任务 |
| **WPS** | `ql_wps_standalone.py` | 天天领福利 + 任务中心 |
| **恩山论坛** | `ql_enshan.py` | 论坛签到 |
| **远景论坛** | `ql_pcbeta.py` | 论坛签到 |
| **绿联论坛** | `ql_ugreen.py` | 论坛签到（Cookie/OAuth） |

## 快速部署

### 方式一：订阅管理（推荐）

青龙面板 → 订阅管理 → 添加订阅：

```
名称: qinglong-auto-sign
链接: https://github.com/Ladavian/qinglong-auto-sign.git
白名单: ql_
执行前命令: pip3 install requests pycryptodome
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

---

#### WPS

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
pip3 install requests pycryptodome
```

> **注意**：绿联论坛需要 `pycryptodome` 库用于加密

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
├── ql_smzdm_standalone.py    # 什么值得买（独立完整版）
├── ql_wps_standalone.py      # WPS（独立完整版）
├── ql_pcbeta.py              # 远景论坛
├── ql_ugreen.py              # 绿联论坛
├── ql_enshan.py              # 恩山论坛
├── requirements.txt          # Python依赖
└── README.md                 # 说明文档
```
