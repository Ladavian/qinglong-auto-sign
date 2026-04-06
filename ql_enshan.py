#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恩山论坛（Enshan）青龙面板签到脚本
支持 Cookie 登录（推荐）和用户名密码登录（备用）

环境变量配置：
方式一（推荐）：export enshan_cookie="cookie1&cookie2"
方式二（备用）：export enshan_username="user1&user2"
              export enshan_password="pass1&pass2"

CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选

多账号用 & 或 @ 或 \n 分隔
"""
import os
import re
import time
import requests


def get_env():
    """获取环境变量配置"""
    cookie_str = os.environ.get('enshan_cookie', '')
    username = os.environ.get('enshan_username', '')
    password = os.environ.get('enshan_password', '')

    accounts = []

    # 优先使用 Cookie 方式
    if cookie_str:
        cookies = []
        for sep in ['&', '@', '\n']:
            if sep in cookie_str:
                cookies = [c.strip() for c in cookie_str.split(sep) if c.strip()]
                break
        else:
            cookies = [cookie_str.strip()]

        for cookie in cookies:
            if cookie:
                accounts.append({'type': 'cookie', 'cookie': cookie})
        print(f"使用 Cookie 方式，共 {len(accounts)} 个账号")
    elif username and password:
        # 备用：用户名密码方式
        usernames = []
        passwords = []
        for sep in ['&', '@', '\n']:
            if sep in username:
                usernames = username.split(sep)
                passwords = password.split(sep)
                break
        else:
            usernames = [username]
            passwords = [password]

        for u, p in zip(usernames, passwords):
            u = u.strip()
            p = p.strip()
            if u and p:
                accounts.append({'type': 'password', 'username': u, 'password': p})
        print(f"使用用户名密码方式，共 {len(accounts)} 个账号")
    else:
        print('未配置环境变量 enshan_cookie 或 enshan_username/enshan_password')

    return accounts


def check_cookie_valid(cookie):
    """检查 Cookie 是否有效"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Cookie': cookie,
    }
    try:
        resp = requests.get('https://www.right.com.cn/forum/home.php?mod=spacecp', 
                           headers=headers, timeout=10, allow_redirects=False)
        # 如果返回 302 跳转到登录页，说明 Cookie 失效
        if resp.status_code == 302 and 'login' in resp.headers.get('Location', '').lower():
            return False
        # 或者直接访问，检查是否包含登录成功的标志
        resp_full = requests.get('https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit',
                                headers=headers, timeout=10)
        if '退出' in resp_full.text or '欢迎您回来' in resp_full.text:
            return True
        return False
    except:
        return False


def send_webhook_notify(title, content):
    """发送自定义webhook通知"""
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


def sign_in(account):
    """
    恩山论坛签到

    Args:
        account: 账号信息字典，包含 type、cookie 或 username/password

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

        # 根据账号类型进行认证
        if account['type'] == 'cookie':
            print(f"[{name}] 使用 Cookie 登录...")
            session.headers.update({'Cookie': account['cookie']})
            
            # 检查 Cookie 是否有效
            if not check_cookie_valid(account['cookie']):
                msg = "Cookie 已失效，请更新 enshan_cookie"
                print(f"[{name}] {msg}")
                return msg
            
            print(f"[{name}] Cookie 有效")
        else:
            # 用户名密码登录
            print(f"[{name}] 正在登录...")
            login_url = "https://www.right.com.cn/forum/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1"
            login_data = {
                'username': account['username'],
                'password': account['password'],
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
        if account['type'] == 'cookie':
            print(f"开始处理第 {i}/{len(accounts)} 个账号")
        else:
            print(f"开始处理第 {i}/{len(accounts)} 个账号: {account['username']}")
        print(f"{'='*50}")

        result = sign_in(account)
        if account['type'] == 'cookie':
            results.append(f"账号{i}: {result}")
        else:
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
