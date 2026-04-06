#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS 青龙面板签到脚本 - 完整版
支持任务中心、天天领福利双页面任务

此脚本通过包装器调用 ZaiZaiCat-Checkin 的完整功能，并添加自定义 webhook 通知

环境变量配置：
export wps_config_path="/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin/config/token.json"
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选

注意：需要先订阅 ZaiZaiCat-Checkin 仓库并在 config/token.json 中配置账号
"""
import os
import sys
import time


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
    print("WPS 签到 - 完整版（任务中心 + 天天领福利）")
    print("=" * 60)

    config_path = os.environ.get('wps_config_path', '/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin/config/token.json')

    if not os.path.exists(config_path):
        msg = f"配置文件不存在: {config_path}"
        print(msg)
        send_webhook("❌ WPS签到失败", msg)
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
        from script.wps.main import WPSMultiPageRunner
        runner = WPSMultiPageRunner()

        # 替换运行方法
        orig_run = runner.run
        def wrapped_run():
            start = time.time()
            try:
                orig_run()
            except Exception as e:
                print(f"执行失败: {e}")
                import traceback
                traceback.print_exc()
                send_webhook("❌ WPS签到失败", str(e))
                return

            duration = int(time.time() - start)
            success = sum(1 for r in runner.account_results if r.get('success'))
            fail = len(runner.account_results) - success

            lines = [
                f"👥 账号: {len(runner.account_results)}个",
                f"✅ 成功: {success}",
                f"❌ 失败: {fail}",
                f"⏱️ 耗时: {duration}秒",
                "",
                "📋 执行页面:",
                "   - 任务中心",
                "   - 天天领福利"
            ]

            send_webhook("✅ WPS签到完成", "\n".join(lines))

        runner.run = wrapped_run
        runner.run()

    except Exception as e:
        msg = f"执行失败: {str(e)}"
        print(msg)
        import traceback
        traceback.print_exc()
        send_webhook("❌ WPS签到失败", msg)
    finally:
        builtins.print = old_print
        print("\n" + "=" * 60)
        print("✨ 完成")
        print("=" * 60)


if __name__ == '__main__':
    main()
