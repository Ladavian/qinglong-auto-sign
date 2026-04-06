#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS 独立签到脚本 - 完整版
支持任务中心、天天领福利双页面任务
完全独立，不依赖任何外部仓库

环境变量配置：
export wps_cookie="cookie1&cookie2"  # 多个账号用 & 或 @ 或换行分隔
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选
"""
import os
import time
import requests
from datetime import datetime


def get_accounts():
    """获取账号列表"""
    cookie_str = os.environ.get('wps_cookie', '')
    if not cookie_str:
        print('❌ 未配置 wps_cookie')
        return []

    cookies = []
    for sep in ['&', '@', '\n']:
        if sep in cookie_str:
            cookies = [c.strip() for c in cookie_str.split(sep) if c.strip()]
            break
    else:
        cookies = [cookie_str.strip()]

    return [{'cookie': c} for c in cookies if c]


def send_webhook(title, content):
    """发送 webhook 通知"""
    url = os.environ.get('CUSTOM_WEBHOOK_URL', '') or os.environ.get('NOTIFY_WEBHOOK', '')
    if not url:
        print("未配置 CUSTOM_WEBHOOK_URL 或 NOTIFY_WEBHOOK，跳过通知")
        return False
    try:
        payload = {
            "title": title,
            "content": content,
            "timestamp": int(time.time())
        }
        response = requests.post(url, json=payload,
                                headers={"Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            print("✓ 通知发送成功")
            return True
        else:
            print(f"✗ 通知发送失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 通知发送异常: {e}")
        return False


def get_user_info(cookie):
    """获取用户信息"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'application/json',
    }

    try:
        resp = requests.get('https://account.wps.cn/api/v1/user/info',
                           headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('result') == 'ok':
                user = data.get('info', {})
                return {
                    'nickname': user.get('nickname', '-'),
                    'vip_level': user.get('vip_level', 0),
                    'exp': user.get('exp', 0),
                }
    except Exception as e:
        print(f"获取用户信息失败: {e}")
    return None


def do_daily_checkin(cookie):
    """执行每日签到（天天领福利）"""
    name = "WPS-天天领福利"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    result = []
    try:
        # WPS 签到接口
        resp = requests.post('https://vip.wps.cn/sign/v2',
                            headers=headers,
                            data={'platform': 'pc'},
                            timeout=15)
        data = resp.json()

        if data.get('result') == 'ok':
            sign_data = data.get('data', {})
            exp = sign_data.get('exp', 0)
            days = sign_data.get('continue_sign_days', 0)
            result.append("✅ 签到成功")
            result.append(f"💰 获得经验: {exp}")
            result.append(f"📅 连续签到: {days}天")
            print(f"[{name}] ✅ 签到成功 | +{exp}经验 | 连续{days}天")
        elif '已签' in str(data.get('msg', '')):
            result.append("ℹ️ 今日已签到")
            print(f"[{name}] ℹ️ 今日已签到")
        else:
            result.append(f"❌ 签到失败: {data.get('msg', '未知错误')}")
            print(f"[{name}] ❌ 签到失败")
    except Exception as e:
        result.append(f"❌ 签到异常: {str(e)}")
        print(f"[{name}] ✗ 签到异常: {e}")

    return "\n".join(result)


def get_task_list(cookie):
    """获取任务中心任务列表"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'application/json',
    }

    try:
        # 获取任务列表
        resp = requests.get('https://vip.wps.cn/task/list',
                           headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('result') == 'ok':
                tasks = data.get('data', {}).get('tasks', [])
                return tasks
    except Exception as e:
        print(f"获取任务列表失败: {e}")
    return []


def complete_task(cookie, task_id):
    """完成任务"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    try:
        resp = requests.post('https://vip.wps.cn/task/complete',
                            headers=headers,
                            data={'task_id': task_id},
                            timeout=15)
        data = resp.json()
        if data.get('result') == 'ok':
            return True, "完成成功"
        else:
            return False, data.get('msg', '完成失败')
    except Exception as e:
        return False, str(e)


def do_task_center(cookie):
    """执行任务中心任务"""
    name = "WPS-任务中心"
    print(f"[{name}] 开始获取任务列表...")

    tasks = get_task_list(cookie)
    if not tasks:
        msg = "未找到可执行的任务"
        print(f"[{name}] {msg}")
        return msg

    success_count = 0
    fail_count = 0
    skip_count = 0
    results = []

    print(f"[{name}] 找到 {len(tasks)} 个任务")

    for task in tasks:
        task_name = task.get('name', '未知任务')
        task_id = task.get('id', '')
        status = task.get('status', 0)  # 0:未完成, 1:已完成, 2:已领取

        # 跳过已完成的任务
        if status in [1, 2]:
            skip_count += 1
            continue

        print(f"[{name}] 执行任务: {task_name}")

        time.sleep(2)
        success, message = complete_task(cookie, task_id)

        if success:
            success_count += 1
            results.append(f"✅ {task_name}")
            print(f"[{name}] ✓ 完成成功")
        else:
            fail_count += 1
            results.append(f"❌ {task_name}: {message}")
            print(f"[{name}] ✗ 完成失败: {message}")

        time.sleep(2)

    summary = f"任务中心: 成功{success_count}个, 失败{fail_count}个, 跳过{skip_count}个"
    if results:
        summary += "\n" + "\n".join(results[:5])  # 只显示前5个结果

    print(f"[{name}] {summary}")
    return summary


def process_account(cookie, index, total):
    """处理单个账号的所有任务"""
    print(f"\n{'='*60}")
    print(f"开始处理账号 {index}/{total}")
    print(f"{'='*60}")

    results = []

    # 获取用户信息
    print("\n【0】获取用户信息...")
    user_info = get_user_info(cookie)
    if user_info:
        info_msg = f"👤 用户: {user_info['nickname']}\n🎖️ VIP等级: {user_info['vip_level']}\n⭐ 经验值: {user_info['exp']}"
        print(f"用户: {user_info['nickname']} | VIP: {user_info['vip_level']}")
        results.append(info_msg)

    # 1. 天天领福利（签到）
    print("\n【1】执行天天领福利...")
    checkin_result = do_daily_checkin(cookie)
    results.append(checkin_result)

    # 2. 任务中心
    print("\n【2】执行任务中心...")
    time.sleep(3)
    task_result = do_task_center(cookie)
    results.append(task_result)

    return "\n".join(results)


def main():
    print("=" * 60)
    print("WPS 独立签到脚本 - 完整版")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    accounts = get_accounts()
    if not accounts:
        print("没有找到可用的账号配置")
        return

    print(f"共 {len(accounts)} 个账号\n")

    all_results = []
    for i, acc in enumerate(accounts, 1):
        result = process_account(acc['cookie'], i, len(accounts))
        all_results.append(f"账号{i}:\n{result}")

        if i < len(accounts):
            print("\n等待5秒后处理下一个账号...")
            time.sleep(5)

    # 输出总结
    print("\n" + "=" * 60)
    print("签到结果汇总")
    print("=" * 60)
    summary = "\n\n".join(all_results)
    print(summary)

    # 发送 webhook 通知
    send_webhook("✅ WPS签到完成", summary)

    print("\n✨ 所有任务完成")


if __name__ == '__main__':
    main()
