#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
什么值得买（SMZDM）青龙面板签到脚本
支持多账号配置和自定义 webhook 通知

环境变量配置：
export smzdm_cookie="cookie1&cookie2"  # 多个账号用 & 分隔
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选

Cookie 获取方法：
1. 浏览器登录 https://www.smzdm.com/
2. F12 打开开发者工具
3. Network 标签中复制任意请求的 Cookie
"""
import os
import re
import time
import json
import requests


def get_env():
    """获取环境变量配置"""
    cookie_str = os.environ.get('smzdm_cookie', '')

    if not cookie_str:
        print('未配置环境变量 smzdm_cookie')
        return []

    # 支持多种分隔符
    for sep in ['&', '@', '\n']:
        if sep in cookie_str:
            cookies = cookie_str.split(sep)
            break
    else:
        cookies = [cookie_str]

    # 清理空格和空值
    accounts = []
    for c in cookies:
        c = c.strip()
        if c:
            accounts.append({'cookie': c})

    return accounts


def send_webhook_notify(title, content):
    """
    发送自定义webhook通知

    Args:
        title: 通知标题
        content: 通知内容

    Returns:
        bool: 是否发送成功
    """
    # 优先使用 CUSTOM_WEBHOOK_URL，兼容 NOTIFY_WEBHOOK
    webhook_url = os.environ.get('CUSTOM_WEBHOOK_URL', '') or os.environ.get('NOTIFY_WEBHOOK', '')

    if not webhook_url:
        print("未配置 CUSTOM_WEBHOOK_URL 或 NOTIFY_WEBHOOK，跳过通知")
        return False

    try:
        payload = {
            "title": title,
            "content": content,
            "timestamp": int(time.time())
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }

        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            print("通知发送成功")
            return True
        else:
            print(f"通知发送失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"通知发送异常: {e}")
        return False


def sign_in(cookie):
    """
    什么值得买签到

    Args:
        cookie: Cookie 字符串

    Returns:
        str: 签到结果消息
    """
    name = "什么值得买"
    result_msg = f"[{name}] "

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Cookie': cookie,
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.smzdm.com/',
        }

        # 1. 执行签到
        print(f"[{name}] 正在签到...")
        checkin_url = "https://user-api.smzdm.com/checkin"
        params = {
            'touchstone_event': '',
            'sk': '1',
            'token': '',
            'captcha': '',
            'v': ''
        }

        resp = requests.post(checkin_url, headers=headers, params=params, timeout=15)
        data = resp.json()

        if data.get('error_code') == 0:
            checkin_data = data.get('data', {})
            points = checkin_data.get('add_point', '0')
            continuous_days = checkin_data.get('continue_checkin_days', 0)

            result_msg += f"✓ 签到成功\n"
            result_msg += f"💰 获得积分: {points}\n"
            result_msg += f"📅 连续签到: {continuous_days}天"

            print(f"[{name}] ✓ 签到成功")
            print(f"[{name}] 获得积分: {points}")
            print(f"[{name}] 连续签到: {continuous_days}天")
        elif '已领取' in data.get('error_msg', '') or '已签到' in data.get('error_msg', ''):
            result_msg += "今日已签到"
            print(f"[{name}] 今日已签到")
        else:
            error_msg = data.get('error_msg', '未知错误')
            result_msg += f"✗ 签到失败: {error_msg}"
            print(f"[{name}] ✗ 签到失败: {error_msg}")

        # 2. 获取用户信息
        time.sleep(2)
        print(f"[{name}] 获取用户信息...")
        user_url = "https://user-api.smzdm.com/user/info"
        resp = requests.get(user_url, headers=headers, timeout=15)
        user_data = resp.json()

        if user_data.get('error_code') == 0:
            user_info = user_data.get('data', {})
            nickname = user_info.get('nickname', '未知用户')
            level = user_info.get('level', {}).get('level_name', '-')
            gold = user_info.get('gold', '0')
            prestige = user_info.get('prestige', '0')

            result_msg += f"\n👤 用户: {nickname}\n"
            result_msg += f"🎖️ 等级: {level}\n"
            result_msg += f"💎 金币: {gold} | 威望: {prestige}"

            print(f"[{name}] 用户: {nickname}")
            print(f"[{name}] 等级: {level}")
            print(f"[{name}] 金币: {gold} | 威望: {prestige}")

        return result_msg

    except Exception as e:
        msg = f"✗ 运行出错: {e}"
        print(f"[{name}] {msg}")
        return msg


def main():
    """主函数"""
    print("=" * 50)
    print("什么值得买（SMZDM）青龙面板签到脚本")
    print("=" * 50)

    # 获取账号列表
    accounts = get_env()

    if not accounts:
        print("没有找到可用的账号配置")
        return

    print(f"共找到 {len(accounts)} 个账号\n")

    # 执行签到
    results = []
    for i, account in enumerate(accounts, 1):
        print(f"\n{'='*50}")
        print(f"开始处理第 {i}/{len(accounts)} 个账号")
        print(f"{'='*50}")

        result = sign_in(account['cookie'])
        results.append(f"账号{i}: {result}")

        # 多账号之间延迟
        if i < len(accounts):
            time.sleep(5)

    # 输出总结
    print(f"\n{'='*50}")
    print("签到结果汇总")
    print(f"{'='*50}")
    for result in results:
        print(result)

    # 发送webhook通知
    summary = "\n".join(results)
    send_webhook_notify("什么值得买签到结果", summary)


if __name__ == '__main__':
    main()
