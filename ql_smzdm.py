#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
什么值得买（SMZDM）青龙面板签到脚本 - 完整版
支持每日签到、众测任务、互动任务

此脚本通过包装器调用 ZaiZaiCat-Checkin 的完整功能，并添加自定义 webhook 通知

环境变量配置：
export smzdm_config_path="/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin/config/token.json"
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选

注意：需要先订阅 ZaiZaiCat-Checkin 仓库并在 config/token.json 中配置账号
"""
import os
import sys
import time
from datetime import datetime


def send_webhook(title, content):
    """发送自定义webhook通知"""
    import requests
    webhook_url = os.environ.get('CUSTOM_WEBHOOK_URL', '') or os.environ.get('NOTIFY_WEBHOOK', '')
    if not webhook_url:
        return False
    try:
        requests.post(webhook_url, json={"title": title, "content": content, "timestamp": int(time.time())},
                     headers={"Content-Type": "application/json"}, timeout=10)
        return True
    except:
        return False


def main():
    print("=" * 60)
    print("什么值得买（SMZDM）签到 - 完整版")
    print("=" * 60)

    config_path = os.environ.get('smzdm_config_path', '/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin/config/token.json')

    if not os.path.exists(config_path):
        msg = f"配置文件不存在: {config_path}"
        print(msg)
        send_webhook("❌ SMZDM签到失败", msg)
        return

    # 添加原仓库路径
    repo_path = '/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin'
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)

    # 捕获输出
    output = []
    import builtins
    old_print = builtins.print
    def capture_print(*args, **kwargs):
        text = ' '.join(str(a) for a in args)
        output.append(text)
        old_print(*args, **kwargs)
    builtins.print = capture_print

    start_time = time.time()
    try:
        from script.smzdm.sign_daily_task.main import SmzdmTaskManager
        manager = SmzdmTaskManager()

        # 替换通知方法
        orig_notify = manager.send_task_notification
        def wrapped_notify(start, end):
            try:
                orig_notify(start, end)
            except: pass

            duration = int((end - start).total_seconds())
            success = sum(1 for r in manager.account_results if r.get('success'))
            fail = len(manager.account_results) - success

            lines = [f"👥 账号: {len(manager.account_results)}个", f"✅ 成功: {success}", f"❌ 失败: {fail}", f"⏱️ 耗时: {duration}秒", ""]

            for i, r in enumerate(manager.account_results, 1):
                name = r.get('account_name', f'账号{i}')
                if r.get('success'):
                    ck = r.get('checkin', {})
                    zc = r.get('zhongce', {})
                    it = r.get('interactive', {})
                    lines.append(f"✅ [{name}]")
                    if ck.get('continuous_days', 0) > 0:
                        lines.append(f"   📅 连续{ck['continuous_days']}天")
                    lines.append(f"   🎯 众测: ✅{zc.get('success',0)} ⚠️{zc.get('fail',0)}")
                    lines.append(f"   🎯 互动: ✅{it.get('success',0)} ⚠️{it.get('fail',0)}")
                else:
                    lines.append(f"❌ [{name}]: {r.get('error','未知')}")
                if i < len(manager.account_results):
                    lines.append("")

            send_webhook("✅ SMZDM签到完成", "\n".join(lines))

        manager.send_task_notification = wrapped_notify
        manager.run()

    except Exception as e:
        msg = f"执行失败: {str(e)}"
        print(msg)
        import traceback
        traceback.print_exc()
        send_webhook("❌ SMZDM签到失败", msg)
    finally:
        builtins.print = old_print
        print("\n" + "=" * 60)
        print("✨ 完成")
        print("=" * 60)


if __name__ == '__main__':
    main()
