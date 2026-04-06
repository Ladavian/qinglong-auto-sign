#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恩山论坛（Enshan）青龙面板签到脚本
支持用户名密码登录和多账号配置

环境变量配置：
export enshan_username="user1&user2"
export enshan_password="pass1&pass2"
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选

多账号用 & 或 @ 或 \n 分隔
"""
import os
import re
import time
import requests


def get_env():
    """获取环境变量配置"""
    username = os.environ.get('enshan_username', '')
    password = os.environ.get('enshan_password', '')

    if not username or not password:
        print('未配置环境变量 enshan_username 或 enshan_password')
        return []

    # 支持多种分隔符
    for sep in ['&', '@', '\n']:
        if sep in username:
            usernames = username.split(sep)
            passwords = password.split(sep)
            break
    else:
        usernames = [username]
        passwords = [password]

    # 清理空格和空值
    accounts = []
    for u, p in zip(usernames, passwords):
        u = u.strip()
        p = p.strip()
        if u and p:
            accounts.append({'username': u, 'password': p})

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


def sign_in(username, password):
    """
    恩山论坛签到

    Args:
        username: 用户名
        password: 密码

    Returns:
        str: 签到结果消息
    """
    name = "恩山论坛"
    result_msg = f"[{name}] "

    try:
        session = requests.Session()
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"

        session.headers.update({
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

        # 1. 登录
        print(f"[{name}] 正在登录...")
        login_url = "https://www.right.com.cn/forum/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1"
        login_data = {
            'username': username,
            'password': password,
            'quickforward': 'yes'
        }

        resp = session.post(login_url, data=login_data, timeout=15)

        if resp.status_code != 200:
            msg = f"登录失败: HTTP {resp.status_code}"
            print(f"[{name}] {msg}")
            return msg

        # 检查登录是否成功
        if '欢迎您回来' not in resp.text and '退出' not in resp.text:
            msg = "登录失败，请检查用户名和密码"
            print(f"[{name}] {msg}")
            return msg

        print(f"[{name}] 登录成功")

        # 2. 访问签到页面
        time.sleep(2)
        print(f"[{name}] 正在签到...")

        # 恩山论坛的签到通常是访问 home.php
        home_url = "https://www.right.com.cn/forum/home.php?mod=task&do=apply&id=1"
        resp = session.get(home_url, timeout=15)

        # 检查签到结果
        if '任务已完成' in resp.text or '您已经完成过这个任务' in resp.text:
            result_msg += "今日已签到"
            print(f"[{name}] 今日已签到")
        elif '恭喜' in resp.text or '成功' in resp.text:
            result_msg += "✓ 签到成功"
            print(f"[{name}] ✓ 签到成功")
        else:
            # 可能已经签到了或者不需要签到
            result_msg += "签到完成"
            print(f"[{name}] 签到完成")

        # 3. 获取用户信息
        time.sleep(2)
        print(f"[{name}] 获取用户信息...")

        # 访问个人中心
        profile_url = "https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit"
        resp = session.get(profile_url, timeout=15)
        html = resp.text

        # 提取积分信息
        points_match = re.search(r'积分[：:\s]*(\d+)', html)
        points = points_match.group(1) if points_match else '-'

        # 提取威望
        prestige_match = re.search(r'威望[：:\s]*(\d+)', html)
        prestige = prestige_match.group(1) if prestige_match else '-'

        # 提取金钱
        money_match = re.search(r'金钱[：:\s]*(\d+)', html)
        money = money_match.group(1) if money_match else '-'

        result_msg += f"\n💰 积分: {points}\n"
        result_msg += f"🎖️ 威望: {prestige}\n"
        result_msg += f"💵 金钱: {money}"

        print(f"[{name}] 积分: {points}")
        print(f"[{name}] 威望: {prestige}")
        print(f"[{name}] 金钱: {money}")

        return result_msg

    except Exception as e:
        msg = f"✗ 运行出错: {e}"
        print(f"[{name}] {msg}")
        return msg


def main():
    """主函数"""
    print("=" * 50)
    print("恩山论坛（Enshan）青龙面板签到脚本")
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
        print(f"开始处理第 {i}/{len(accounts)} 个账号: {account['username']}")
        print(f"{'='*50}")

        result = sign_in(account['username'], account['password'])
        results.append(f"账号{i}({account['username']}): {result}")

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
    send_webhook_notify("恩山论坛签到结果", summary)


if __name__ == '__main__':
    main()
