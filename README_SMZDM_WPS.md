# WPS 完整功能配置指南

## 重要说明

什么值得买（SMZDM）完整功能已内置到本仓库（`script/smzdm/`），直接运行 `script/smzdm/sign_daily_task/main.py` 即可，**无需再订阅外部仓库**，配置方法见 [README.md](README.md#什么值得买-smzdm)。

本文档仅适用于 **WPS**：原脚本功能复杂、包含多个模块和依赖，继续使用 ZaiZaiCat-Checkin 仓库的完整功能，通过包装脚本添加 webhook 通知。

---

## 方案：使用包装脚本

### 1. 确保已订阅 ZaiZaiCat-Checkin

在青龙面板中确认已添加订阅：
```
链接: https://github.com/Cat-zaizai/ZaiZaiCat-Checkin.git
```

### 2. 配置 token.json

编辑 `/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin/config/token.json`：

#### WPS 配置
```json
{
  "wps": {
    "accounts": [
      {
        "name": "账号1",
        "cookie": "你的Cookie（需要包含wps_sid）"
      }
    ]
  }
}
```

### 3. 创建 WPS 包装脚本 (`/ql/scripts/my_wps_full.py`)

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/ql/scripts')
sys.path.insert(0, '/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin')

from webhook_wrapper import send_webhook

output_lines = []
import builtins
original_print = builtins.print

def custom_print(*args, **kwargs):
    text = ' '.join(str(a) for a in args)
    output_lines.append(text)
    original_print(*args, **kwargs)

builtins.print = custom_print

try:
    from script.wps.main import main as wps_main
    wps_main()

    if output_lines:
        content = '\n'.join(output_lines[-50:])
        send_webhook("✅ WPS签到完成", content)

except Exception as e:
    send_webhook("❌ WPS签到失败", str(e))

finally:
    builtins.print = original_print
```

### 4. 创建定时任务

| 名称 | 命令 | 定时规则 |
|------|------|----------|
| WPS签到(完整版) | `python3 /ql/scripts/my_wps_full.py` | `0 9 * * *` |

### 5. 禁用原有任务

禁用从 ZaiZaiCat-Checkin 订阅的原始任务，只保留包装脚本任务。

---

## 优势

✅ **完整功能**：保留原脚本的所有功能（众测任务、互动任务、任务中心、天天领福利）
✅ **Webhook 通知**：通过包装脚本添加自定义通知
✅ **不会被覆盖**：包装脚本独立于子仓库
✅ **统一管理**：使用 `CUSTOM_WEBHOOK_URL`

---

## 注意事项

1. **配置文件位置**：token.json 在原仓库的 config 目录
2. **Cookie 获取**：需要从浏览器中获取完整的 Cookie
3. **依赖完整**：确保 ZaiZaiCat-Checkin 仓库已正确订阅
4. **日志输出**：包装脚本会捕获所有 print 输出并通过 webhook 发送

---

## Cookie 获取方法

### WPS
1. 浏览器登录 https://www.wps.cn/
2. F12 → Network → 刷新页面
3. 复制任意请求的 Cookie（必须包含 wps_sid）
