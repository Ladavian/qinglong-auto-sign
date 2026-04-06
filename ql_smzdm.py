#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
什么值得买（SMZDM）青龙面板签到脚本 - 完整版
支持每日签到、众测任务、互动任务、能量值系统

此脚本通过调用 ZaiZaiCat-Checkin 的完整功能，并添加自定义 webhook 通知

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
        print("未配置 CUSTOM_WEBHOOK_URL，跳过通知")
        return False
    try:
        requests.post(webhook_url, json={"title": title, "content": content, "timestamp": int(time.time())},
                     headers={"Content-Type": "application/json"}, timeout=10)
        return True
    except Exception as e:
        print(f"通知发送失败: {e}")
        return False


def main():
    print("=" * 60)
    print("什么值得买（SMZDM）签到 - 完整版")
    print("=" * 60)

    # 添加原仓库路径到 Python 路径（支持多种命名）
    repo_paths = [
        '/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin',
        '/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin_main',
    ]
    
    repo_path = None
    for path in repo_paths:
        if os.path.exists(path):
            repo_path = path
            break
    
    if not repo_path:
        msg = "❌ 未找到 ZaiZaiCat-Checkin 仓库\n\n请先订阅仓库：\nhttps://github.com/Cat-zaizai/ZaiZaiCat-Checkin.git"
        print(msg)
        send_webhook("❌ SMZDM配置错误", msg)
        return
    
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)
    
    print(f"✓ 使用仓库路径: {repo_path}")

    # 捕获输出用于通知
    output_lines = []
    import builtins
    old_print = builtins.print
    
    def capture_print(*args, **kwargs):
        text = ' '.join(str(a) for a in args)
        output_lines.append(text)
        old_print(*args, **kwargs)
    
    builtins.print = capture_print

    start_time = time.time()
    
    try:
        # 导入原仓库的 SMZDM 模块
        from script.smzdm.sign_daily_task.main import SmzdmTaskManager
        
        manager = SmzdmTaskManager()
        
        # 替换通知方法，添加自定义 webhook
        orig_notify = manager.send_task_notification
        
        def wrapped_notify(start_time_obj, end_time_obj):
            # 先调用原通知方法
            try:
                orig_notify(start_time_obj, end_time_obj)
            except:
                pass

            # 计算执行统计
            duration = int((end_time_obj - start_time_obj).total_seconds())
            success_count = sum(1 for r in manager.account_results if r.get('success'))
            fail_count = len(manager.account_results) - success_count

            # 构建通知内容
            lines = [
                f"👥 账号: {len(manager.account_results)}个",
                f"✅ 成功: {success_count}",
                f"❌ 失败: {fail_count}",
                f"⏱️ 耗时: {duration}秒",
                ""
            ]

            for i, result in enumerate(manager.account_results, 1):
                name = result.get('account_name', f'账号{i}')
                
                if result.get('success'):
                    # 签到信息
                    checkin = result.get('checkin', {})
                    continuous_days = checkin.get('continuous_days', 0)
                    
                    # 众测任务
                    zhongce = result.get('zhongce', {})
                    zc_success = zhongce.get('success', 0)
                    zc_fail = zhongce.get('fail', 0)
                    
                    # 互动任务
                    interactive = result.get('interactive', {})
                    it_success = interactive.get('success', 0)
                    it_fail = interactive.get('fail', 0)
                    
                    lines.append(f"✅ [{name}]")
                    if continuous_days > 0:
                        lines.append(f"   📅 连续签到: {continuous_days}天")
                    
                    points = checkin.get('points', '-')
                    if points != '-':
                        lines.append(f"   💰 当前积分: {points}")
                    
                    lines.append(f"   🎯 众测任务: ✅{zc_success} ⚠️{zc_fail}")
                    lines.append(f"   🎯 互动任务: ✅{it_success} ⚠️{it_fail}")
                else:
                    error_msg = result.get('error', '未知错误')
                    lines.append(f"❌ [{name}]: {error_msg}")
                
                if i < len(manager.account_results):
                    lines.append("")

            # 发送 webhook
            send_webhook("✅ SMZDM签到完成", "\n".join(lines))

        # 替换通知方法
        manager.send_task_notification = wrapped_notify
        
        # 执行任务
        print("\n开始执行 SMZDM 任务...\n")
        manager.run()

    except Exception as e:
        msg = f"❌ 执行失败: {str(e)}"
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
