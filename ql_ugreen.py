#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绿联论坛（UGreen Discuz）青龙面板签到脚本
优先使用 Cookie 签到，Cookie 失效时自动通过 OAuth 登录获取新 Cookie

环境变量配置：
export ugreen_cookie="你的Cookie字符串"              # 优先使用，可选
export ugreen_username="你的用户名"                  # Cookie失效时使用
export ugreen_password="你的密码"                    # Cookie失效时使用
export NOTIFY_WEBHOOK="https://your-webhook-url.com/api/notify"  # 可选，自定义通知webhook地址

多账号用 & 或 @ 或 \n 分隔，例如：
export ugreen_cookie="cookie1&cookie2"
或
export ugreen_username="user1&user2"
export ugreen_password="pass1&pass2"
"""
import os
import re
import sys
import time
import json
import uuid
import base64
import requests
from urllib.parse import quote


def get_env():
    """获取环境变量配置"""
    cookie = os.environ.get('ugreen_cookie', '')
    username = os.environ.get('ugreen_username', '')
    password = os.environ.get('ugreen_password', '')

    accounts = []

    # 如果配置了 Cookie，优先使用 Cookie
    if cookie:
        # 支持多种分隔符
        for sep in ['&', '@', '\n']:
            if sep in cookie:
                cookies = cookie.split(sep)
                break
        else:
            cookies = [cookie]

        for i, c in enumerate(cookies):
            c = c.strip()
            if c:
                accounts.append({
                    'cookie': c,
                    'username': username.split('&')[i] if '&' in username else (username.split('@')[i] if '@' in username else username),
                    'password': password.split('&')[i] if '&' in password else (password.split('@')[i] if '@' in password else password)
                })
    elif username and password:
        # 如果没有 Cookie，使用用户名密码
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
                accounts.append({'cookie': '', 'username': u, 'password': p})
    else:
        print('未配置环境变量 ugreen_cookie 或 ugreen_username/ugreen_password')

    return accounts


def aes_encrypt(text, key_str, iv_str):
    """
    AES-128-CBC 加密

    Args:
        text: 待加密文本
        key_str: 密钥字符串
        iv_str: IV字符串（取前16字节）

    Returns:
        str: Base64编码的加密结果
    """
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad

        key = key_str.encode('utf-8')
        iv = iv_str[:16].encode('utf-8')
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode('utf-8')
    except ImportError:
        print("警告: 未安装 pycryptodome，无法进行 OAuth 登录")
        return None


def oauth_login(username, password):
    """
    通过 OAuth API 登录绿联论坛

    Args:
        username: 用户名
        password: 密码

    Returns:
        tuple: (success: bool, cookie: str)
    """
    try:
        sess = requests.Session()
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'

        headers_json = {
            'User-Agent': ua,
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://web.ugnas.com',
            'Referer': 'https://web.ugnas.com/',
            'Accept-Language': 'zh-CN',
        }

        # 1. 获取加密密钥
        print("[OAuth] 获取加密密钥...")
        r1 = sess.get('https://api-zh.ugnas.com/api/user/v3/sa/encrypt/key', headers=headers_json, timeout=12)
        if r1.status_code != 200:
            print(f"[OAuth] 加密密钥获取失败: {r1.status_code}")
            return False, ''

        data = r1.json()
        api_data = data.get('data', {})
        encrypt_key = api_data.get('encryptKey')
        api_uuid = api_data.get('uuid')

        if not encrypt_key or not api_uuid:
            print("[OAuth] 未获取到有效的加密密钥")
            return False, ''

        print("[OAuth] 密钥获取成功")

        # 2. AES 加密用户名和密码
        enc_user = aes_encrypt(username, encrypt_key, api_uuid)
        enc_pwd = aes_encrypt(password, encrypt_key, api_uuid)

        if not enc_user or not enc_pwd:
            print("[OAuth] 加密失败")
            return False, ''

        print("[OAuth] 凭据加密完成")

        # 3. 登录获取 Token
        form_headers = {
            'User-Agent': ua,
            'Accept': 'application/json;charset=UTF-8',
            'Origin': 'https://web.ugnas.com',
            'Referer': 'https://web.ugnas.com/',
            'Accept-Language': 'zh-CN',
        }

        req_bid = uuid.uuid4().hex

        files = {
            'platform': (None, 'PC'),
            'clientType': (None, 'browser'),
            'osVer': (None, '142.0.0.0'),
            'model': (None, 'Edge/142.0.0.0'),
            'bid': (None, req_bid),
            'alias': (None, 'Edge/142.0.0.0'),
            'grant_type': (None, 'password'),
            'username': (None, enc_user),
            'password': (None, enc_pwd),
            'uuid': (None, api_uuid),
        }

        print("[OAuth] 正在登录...")
        r2 = sess.post('https://api-zh.ugnas.com/api/oauth/token', headers=form_headers, files=files, timeout=12)
        if r2.status_code != 200:
            print(f"[OAuth] 获取令牌失败: {r2.status_code}")
            return False, ''

        tok = r2.json()
        access_token = tok.get('access_token') or tok.get('data', {}).get('access_token')

        if not access_token:
            print("[OAuth] 未获取到有效的访问令牌")
            return False, ''

        print("[OAuth] 令牌获取成功")

        # 4. 授权回调
        state = uuid.uuid4().hex[:12]
        authorize_url = (
            'https://api-zh.ugnas.com/api/oauth/authorize?response_type=code&client_id=discuz-client&scope=user_info'
            f'&state={state}&redirect_uri={quote("https://club.ugnas.com/api/ugreen/callback.php")}&access_token={access_token}'
        )

        print("[OAuth] 正在进行授权...")
        r3 = sess.get(authorize_url, headers=headers_json, allow_redirects=False, timeout=12)
        loc = r3.headers.get('location') or r3.headers.get('Location')

        if not loc:
            print("[OAuth] 未获取到回调地址")
            return False, ''

        # 5. 访问回调地址设置 Cookie
        r4 = sess.get(loc, headers={
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN'
        }, timeout=12)

        # 刷新站点首页以确保 Cookie 生效
        sess.get('https://club.ugnas.com/', headers={
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN'
        }, timeout=12)

        # 汇总 Cookie
        cookie_items = []
        for c in sess.cookies:
            cookie_items.append(f"{c.name}={c.value}")

        if cookie_items:
            ck = '; '.join(cookie_items)
            if '6LQh_2132_BBRules_ok=' not in ck:
                ck += '; 6LQh_2132_BBRules_ok=1'
            print("[OAuth] 登录成功，已获取 Cookie")
            return True, ck

        return False, ''

    except Exception as e:
        print(f"[OAuth] 登录异常: {e}")
        return False, ''


def check_cookie_valid(cookie):
    """
    检查 Cookie 是否有效

    Args:
        cookie: Cookie 字符串

    Returns:
        bool: Cookie 是否有效
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Cookie': cookie
        }
        resp = requests.get('https://club.ugnas.com/forum.php', headers=headers, timeout=10, allow_redirects=False)

        # 如果返回 302 重定向到登录页，说明 Cookie 失效
        if resp.status_code == 302:
            location = resp.headers.get('location', '').lower()
            if 'login' in location or 'member.php' in location:
                return False

        # 检查响应内容是否包含登录表单
        if 'login' in resp.text.lower() and 'password' in resp.text.lower():
            return False

        return True

    except Exception as e:
        print(f"[Cookie检查] 异常: {e}")
        return False


def fetch_user_profile(cookie):
    """
    获取用户资料信息

    Args:
        cookie: 登录后的 Cookie 字符串

    Returns:
        dict: 用户信息字典
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cookie': cookie
        }

        # 发现 UID
        uid = discover_uid(headers)

        html = ""
        if uid:
            url = f'https://club.ugnas.com/home.php?mod=space&uid={uid}'
            print(f"[用户资料] 访问用户主页: uid={uid}")
            resp = requests.get(url, headers=headers, timeout=15)
            html = resp.text or ""
        else:
            url = 'https://club.ugnas.com/forum.php?mod=forumdisplay&fid=0'
            print(f"[用户资料] 未发现UID，访问论坛首页")
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            html = resp.text or ""

        # 提取用户名
        username = "-"
        t = re.search(r"<li><em>用户名</em>([^<]+)</li>", html)
        if t:
            username = t.group(1).strip()
        else:
            t3 = re.search(r"class=\"kmname\">([^<]+)</span>", html)
            if t3:
                username = t3.group(1).strip()

        # 提取积分
        points = 0
        p = re.search(r"class=\"kmjifen kmico09\"><span>(\d+)</span>积分", html)
        if p:
            points = int(p.group(1))
        else:
            p2 = re.search(r"积分[：:]\s*(\d+)", html)
            if p2:
                points = int(p2.group(1))

        # 提取用户组
        usergroup = None
        ug = re.search(r"<li><em>用户组</em>.*?<a[^>]*>([^<]+)</a>", html)
        if ug:
            usergroup = ug.group(1).strip()

        # 提取主题数
        threads = 0
        th = re.search(r"<span>(\d+)</span>主题数", html)
        if th:
            threads = int(th.group(1))

        # 提取回帖数
        posts = 0
        po = re.search(r"<span>(\d+)</span>回帖数", html)
        if po:
            posts = int(po.group(1))

        # 提取好友数
        friends = 0
        fr = re.search(r"<span>(\d+)</span>好友数", html)
        if fr:
            friends = int(fr.group(1))

        # 提取头像
        avatar = "https://bbs-cn-oss.ugnas.com/bbs/avatar/noavatar.png"
        avatar_match = re.search(r'<img[^>]*class="user_avatar"[^>]*>', html)
        if avatar_match:
            img_tag = avatar_match.group(0)
            src_match = re.search(r'src="([^"]+)"', img_tag)
            if src_match:
                avatar_url = src_match.group(1)
                if '/avatar/' in avatar_url and avatar_url.startswith('http'):
                    try:
                        head_resp = requests.head(avatar_url, timeout=3, allow_redirects=True)
                        if head_resp.status_code == 200:
                            avatar = avatar_url
                    except Exception:
                        avatar = avatar_url
                else:
                    avatar = avatar_url

        info = {
            "uid": uid,
            "username": username,
            "points": points,
            "avatar": avatar,
            "usergroup": usergroup,
            "threads": threads,
            "posts": posts,
            "friends": friends
        }

        return info

    except Exception as e:
        print(f"[用户资料] 获取失败: {e}")
        return {}


def discover_uid(headers):
    """
    从页面中发现用户 UID

    Args:
        headers: 请求头（包含 Cookie）

    Returns:
        str: 用户 UID 或 None
    """
    try:
        urls = [
            'https://club.ugnas.com/forum.php?mod=forumdisplay&fid=0',
            'https://club.ugnas.com/home.php',
        ]
        for u in urls:
            resp = requests.get(u, headers=headers, timeout=12, allow_redirects=True)
            html = resp.text or ""

            # 尝试从多个位置提取 UID
            patterns = [
                r'uid=(\d+)',
                r'data-uid="(\d+)"',
                r'_discuz_uid["\']?\s*[:=]\s*["\']?(\d+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    uid = match.group(1)
                    if uid and uid != '0':
                        return uid
    except Exception as e:
        print(f"[UID] 发现失败: {e}")

    return None


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
            print(f"响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"通知发送异常: {e}")
        return False


def sign_in(account):
    """
    绿联论坛签到

    Args:
        account: 账号信息字典，包含 cookie, username, password

    Returns:
        str: 签到结果消息
    """
    name = "绿联论坛"
    result_msg = f"[{name}] "
    cookie = account.get('cookie', '')
    username = account.get('username', '')
    password = account.get('password', '')

    try:
        # 1. 优先使用 Cookie
        if cookie:
            print(f"[{name}] 使用 Cookie 签到...")

            # 检查 Cookie 是否有效
            if not check_cookie_valid(cookie):
                print(f"[{name}] Cookie 已失效")

                # 尝试 OAuth 登录获取新 Cookie
                if username and password:
                    print(f"[{name}] 尝试 OAuth 登录获取新 Cookie...")
                    success, new_cookie = oauth_login(username, password)
                    if success:
                        cookie = new_cookie
                        print(f"[{name}] 已获取新 Cookie，请更新 ugreen_cookie 环境变量")
                    else:
                        msg = "Cookie 失效且 OAuth 登录失败"
                        print(f"[{name}] {msg}")
                        return msg
                else:
                    msg = "Cookie 失效且未配置用户名密码"
                    print(f"[{name}] {msg}")
                    return msg
            else:
                print(f"[{name}] Cookie 有效")
        elif username and password:
            # 没有 Cookie，直接使用 OAuth 登录
            print(f"[{name}] 开始 OAuth 登录...")
            success, cookie = oauth_login(username, password)
            if not success:
                msg = "OAuth 登录失败"
                print(f"[{name}] {msg}")
                return msg
        else:
            msg = "未配置 Cookie 或用户名密码"
            print(f"[{name}] {msg}")
            return msg

        # 2. 获取用户资料（访问即签到）
        time.sleep(2)
        print(f"[{name}] 获取用户资料...")
        info = fetch_user_profile(cookie)

        if not info:
            msg = "无法获取用户资料"
            print(f"[{name}] {msg}")
            return msg

        username_display = info.get('username', '-')
        uid = info.get('uid', '')
        points = info.get('points', 0)
        usergroup = info.get('usergroup', '-')
        threads = info.get('threads', 0)
        posts = info.get('posts', 0)

        result_msg += f"✓ 签到成功\n"
        result_msg += f"👤 用户：{username_display}\n"
        if uid:
            result_msg += f"🆔 UID：{uid}\n"
        result_msg += f"💰 积分：{points}\n"
        if usergroup:
            result_msg += f"🎖️ 用户组：{usergroup}\n"
        result_msg += f"📝 主题：{threads} | 回帖：{posts}"

        print(f"[{name}] ✓ 签到成功")
        print(f"[{name}] 用户：{username_display}")
        if uid:
            print(f"[{name}] UID：{uid}")
        print(f"[{name}] 积分：{points}")
        if usergroup:
            print(f"[{name}] 用户组：{usergroup}")
        print(f"[{name}] 主题：{threads} | 回帖：{posts}")

        return result_msg

    except Exception as e:
        msg = f"✗ 运行出错: {e}"
        print(f"[{name}] {msg}")
        return msg


def main():
    """主函数"""
    print("=" * 50)
    print("绿联论坛（UGreen）青龙面板签到脚本")
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
        if account.get('cookie'):
            print(f"开始处理第 {i}/{len(accounts)} 个账号 (Cookie模式)")
        else:
            print(f"开始处理第 {i}/{len(accounts)} 个账号: {account.get('username', '未知')}")
        print(f"{'='*50}")

        result = sign_in(account)
        if account.get('cookie'):
            results.append(f"账号{i}(Cookie): {result}")
        else:
            results.append(f"账号{i}({account.get('username', '未知')}): {result}")

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
    send_webhook_notify("绿联论坛签到结果", summary)


if __name__ == '__main__':
    main()
