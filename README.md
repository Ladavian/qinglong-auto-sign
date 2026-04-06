# 青龙面板签到脚本集合

适用于青龙面板的自动化签到脚本，支持多账号配置和自定义 webhook 通知。

## 支持的站点

- [x] 远景论坛 (PCBeta)
- [x] 绿联论坛 (UGreen Discuz)

## 快速开始

### 1. 安装依赖

在青龙面板中执行：

```bash
pip3 install requests pycryptodome
```

> **注意**: 绿联论坛签到需要 `pycryptodome` 库用于 AES 加密

### 2. 配置环境变量

在青龙面板 → 环境变量中添加对应变量。

---

## 远景论坛 (PCBeta)

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `pcbeta_username` | 用户名 | `your_username` |
| `pcbeta_password` | 密码 | `your_password` |

**多账号配置**（使用 `&`、`@` 或换行符分隔）：

```
pcbeta_username: user1&user2&user3
pcbeta_password: pass1&pass2&pass3
```

### 定时任务

```
名称: 远景论坛签到
命令: python3 ql_pcbeta.py
定时规则: 0 8 * * *
```

---

## 绿联论坛 (UGreen Discuz)

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ugreen_username` | 用户名 | `your_username` |
| `ugreen_password` | 密码 | `your_password` |

**多账号配置**（使用 `&`、`@` 或换行符分隔）：

```
ugreen_username: user1&user2&user3
ugreen_password: pass1&pass2&pass3
```

### 定时任务

```
名称: 绿联论坛签到
命令: python3 ql_ugreen.py
定时规则: 0 8 * * *
```

### 工作原理

绿联论坛使用 OAuth API 进行登录：
1. 获取加密密钥
2. AES-128-CBC 加密用户名和密码
3. 通过 OAuth API 获取访问令牌
4. 授权回调设置 Cookie
5. 访问用户主页完成签到（Discuz 论坛访问即签到）

---

## 自定义通知 Webhook

所有脚本都支持通过自定义 webhook 发送签到结果通知。

### 配置

添加环境变量：

```
名称: NOTIFY_WEBHOOK
值: https://your-webhook-url.com/api/notify
```

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

---

## 目录结构

```
qinglong-sign/
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

---

## 常见问题

### Q: 绿联论坛签到失败，提示"加密失败"？
A: 请确保已安装 `pycryptodome` 库：
```bash
pip3 install pycryptodome
```

### Q: 如何查看签到日志？
A: 在青龙面板 → 定时任务 → 点击任务右侧的"日志"按钮查看

### Q: 支持哪些通知方式？
A: 支持任何接受 JSON POST 请求的 webhook 服务，包括企业微信、钉钉、飞书等

### Q: 如何测试脚本是否正常工作？
A: 可以在青龙面板中手动运行一次任务，查看日志输出
