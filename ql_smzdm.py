#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
什么值得买（SMZDM）青龙面板签到脚本 - 完整版
支持每日签到、众测任务、互动任务、能量值系统

完整功能模块已内置在本仓库 script/smzdm/ 目录，自包含运行，不再依赖外部仓库。
旧环境（青龙上仍订阅了 ZaiZaiCat-Checkin）会自动回退到外部仓库路径。

环境变量配置：
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选

注意：账号配置在仓库根目录的 config/token.json（参考 config/template_token.json）
"""
import os
import sys
import time
from datetime import datetime


def send_webhook(title, content):
    """发送自定义webhook通知"""
    import requests
    webhook_url = os.environ.get('CUSTOM_WEBHOOK_URL', '') or os.environ.get('NOTIFY_WEBHOOK', '')
    
    print(f"\n[Webhook] 检查环境变量...")
    print(f"[Webhook] CUSTOM_WEBHOOK_URL: {os.environ.get('CUSTOM_WEBHOOK_URL', '未设置')[:20]}..." if os.environ.get('CUSTOM_WEBHOOK_URL') else "[Webhook] CUSTOM_WEBHOOK_URL: 未设置")
    print(f"[Webhook] NOTIFY_WEBHOOK: {os.environ.get('NOTIFY_WEBHOOK', '未设置')[:20]}..." if os.environ.get('NOTIFY_WEBHOOK') else "[Webhook] NOTIFY_WEBHOOK: 未设置")
    
    if not webhook_url:
        print("[Webhook] ⚠️ 未配置 webhook URL，跳过通知")
        return False
    
    print(f"[Webhook] ✓ 使用 URL: {webhook_url[:30]}...")
    
    try:
        print(f"[Webhook] 正在发送通知...")
        response = requests.post(webhook_url, json={"title": title, "content": content, "timestamp": int(time.time())},
                     headers={"Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            print(f"[Webhook] ✓ 通知发送成功")
            return True
        else:
            print(f"[Webhook] ✗ 通知发送失败: HTTP {response.status_code}")
            print(f"[Webhook] 响应内容: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[Webhook] ✗ 通知发送异常: {e}")
        return False


def main():
    print("=" * 60)
    print("什么值得买（SMZDM）签到 - 完整版")
    print("=" * 60)

    # 添加仓库路径到 Python 路径（优先使用本仓库内置模块，回退到外部 ZaiZaiCat-Checkin）
    # 脚本所在目录即本仓库根目录
    local_dir = os.path.dirname(os.path.abspath(__file__))
    repo_paths = [
        local_dir,
        '/ql/scripts/Ladavian_qinglong-auto-sign',
        '/ql/scripts/Ladavian_qinglong-auto-sign_main',
        '/ql/data/scripts/Ladavian_qinglong-auto-sign',
        '/ql/data/scripts/Ladavian_qinglong-auto-sign_main',
        # 旧环境回退：外部 ZaiZaiCat-Checkin 仓库
        '/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin',
        '/ql/scripts/Cat-zaizai_ZaiZaiCat-Checkin_main',
        '/ql/data/scripts/Cat-zaizai_ZaiZaiCat-Checkin',
        '/ql/data/scripts/Cat-zaizai_ZaiZaiCat-Checkin_main',
    ]

    def has_smzdm_module(path):
        """校验仓库根目录下是否包含内置 SMZDM 模块"""
        return os.path.exists(os.path.join(path, 'script', 'smzdm', 'sign_daily_task', 'main.py'))

    repo_path = None
    for path in repo_paths:
        if has_smzdm_module(path):
            repo_path = path
            break

    if not repo_path:
        # 尝试动态查找（兼容青龙不同的仓库命名）
        import glob
        for match in glob.glob('/ql/*/scripts/*'):
            if has_smzdm_module(match):
                repo_path = match
                print(f"✓ 自动找到仓库路径: {repo_path}")
                break

    if not repo_path:
        msg = "❌ 未找到内置 SMZDM 模块（script/smzdm/）\n\n请确认已订阅本仓库：\nhttps://github.com/Ladavian/qinglong-auto-sign.git"
        print(msg)
        send_webhook("❌ SMZDM配置错误", msg)
        return
    
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)
    
    # 添加 script 子目录到路径（解决模块导入问题）
    script_path = os.path.join(repo_path, 'script')
    if os.path.exists(script_path) and script_path not in sys.path:
        sys.path.insert(0, script_path)
    
    # 添加 sign_daily_task 子目录到路径
    smzdm_task_path = os.path.join(repo_path, 'script', 'smzdm', 'sign_daily_task')
    if os.path.exists(smzdm_task_path) and smzdm_task_path not in sys.path:
        sys.path.insert(0, smzdm_task_path)
    
    print(f"✓ 使用仓库路径: {repo_path}")
    print(f"✓ Python 路径已添加: {script_path}")

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
        # 导入仓库内置的 SMZDM 模块（ql_smzdm.py 与本模块位于同一仓库）
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
        print("✓ 已添加自定义 webhook 通知")
        
        # 执行任务
        print("\n开始执行 SMZDM 任务...\n")
        manager.run()
        
        # 确保发送通知（兜底）
        print("\n发送签到结果通知...")
        duration = int(time.time() - start_time)
        success_count = sum(1 for r in manager.account_results if r.get('success'))
        fail_count = len(manager.account_results) - success_count
        
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
                checkin = result.get('checkin', {})
                continuous_days = checkin.get('continuous_days', 0)
                
                zhongce = result.get('zhongce', {})
                zc_success = zhongce.get('success', 0)
                zc_fail = zhongce.get('fail', 0)
                
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
        
        send_webhook("✅ SMZDM签到完成", "\n".join(lines))

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
