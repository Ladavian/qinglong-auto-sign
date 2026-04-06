#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS 青龙面板签到脚本
支持多账号配置和自定义 webhook 通知

环境变量配置：
export wps_cookie="cookie1&cookie2"  # 多个账号用 & 分隔
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选

Cookie 获取方法：
1. 浏览器登录 https://www.wps.cn/
2. F12 打开开发者工具
3. Network 标签中复制任意请求的 Cookie（主要需要 wps_sid）
"""
import os
import re
import time
import requests


def get_env():
    """获取环境变量配置"""
    cookie_str = os.environ.get('wps_cookie', '')

    if not cookie_str:
        print('未配置环境变量 wps_cookie')
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
    WPS 签到

    Args:
        cookie: Cookie 字符串

    Returns:
        str: 签到结果消息
    """
    name = "WPS"
    result_msg = f"[{name}] "

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Cookie': cookie,
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.wps.cn/',
            'Origin': 'https://www.wps.cn',
        }

        # 1. 执行签到
        print(f"[{name}] 正在签到...")
        checkin_url = "https://vip.wps.cn/sign/v2"

        resp = requests.post(checkin_url, headers=headers, timeout=15)
        data = resp.json()

        if data.get('result') == 'ok':
            sign_data = data.get('data', {})
            exp = sign_data.get('exp', 0)
            continuous_days = sign_data.get('continue_sign_count', 0)

            result_msg += f"✓ 签到成功\n"
            result_msg += f"💰 获得经验: {exp}\n"
            result_msg += f"📅 连续签到: {continuous_days}天"

            print(f"[{name}] ✓ 签到成功")
            print(f"[{name}] 获得经验: {exp}")
            print(f"[{name}] 连续签到: {continuous_days}天")
        elif data.get('msg') and ('已签' in data['msg'] or '重复' in data['msg']):
            result_msg += "今日已签到"
            print(f"[{name}] 今日已签到")
        else:
            error_msg = data.get('msg', '未知错误')
            result_msg += f"✗ 签到失败: {error_msg}"
            print(f"[{name}] ✗ 签到失败: {error_msg}")

        # 2. 获取用户信息
        time.sleep(2)
        print(f"[{name}] 获取用户信息...")

        # 尝试从 cookie 中提取用户名或使用 API 获取
        user_url = "https://account.wps.cn/api/v3/user/info"
        resp = requests.get(user_url, headers=headers, timeout=15)

        if resp.status_code == 200:
            user_data = resp.json()
            if user_data.get('result') == 'ok':
                user_info = user_data.get('data', {})
                nickname = user_info.get('nickname', '未知用户')
                vip_type = user_info.get('vip', {}).get('name', '非会员')

                result_msg += f"\n👤 用户: {nickname}\n"
                result_msg += f"🎖️ 会员: {vip_type}"

                print(f"[{name}] 用户: {nickname}")
                print(f"[{name}] 会员: {vip_type}")

        return result_msg

    except Exception as e:
        msg = f"✗ 运行出错: {e}"
        print(f"[{name}] {msg}")
        return msg


def main():
    """主函数"""
    print("=" * 50)
    print("WPS 青龙面板签到脚本")
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
    send_webhook_notify("WPS签到结果", summary)


if __name__ == '__main__':
    main()
