#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远景论坛（PCBeta）青龙面板签到脚本
支持账号密码登录方式

环境变量配置：
export pcbeta_username="你的用户名"
export pcbeta_password="你的密码"
export NOTIFY_WEBHOOK="https://your-webhook-url.com/api/notify"  # 可选，自定义通知webhook地址

多账号用 & 或 @ 或 \n 分隔，例如：
export pcbeta_username="user1&user2"
export pcbeta_password="pass1&pass2"
"""
import os
import re
import sys
import time
import json
import requests


def get_env():
    """获取环境变量配置"""
    username = os.environ.get('pcbeta_username', '')
    password = os.environ.get('pcbeta_password', '')

    if not username or not password:
        print('未配置环境变量 pcbeta_username 或 pcbeta_password')
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
    webhook_url = os.environ.get('NOTIFY_WEBHOOK', '')

    if not webhook_url:
        print("未配置 NOTIFY_WEBHOOK，跳过通知")
        return False

    try:
        # 构建通知数据（通用webhook格式）
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
            print(f"通知发送成功")
            return True
        else:
            print(f"通知发送失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"通知发送异常: {e}")
        return False


def sign_in(username, password):
    """
    远景论坛签到

    Args:
        username: 用户名
        password: 密码

    Returns:
        str: 签到结果消息
    """
    name = "远景论坛"
    result_msg = f"[{name}] "

    try:
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
        session = requests.Session()
        session.headers.update({"User-Agent": ua})

        print(f"[{name}] 开始登录...")

        # 1. 登录
        login_url = "https://i.pcbeta.com/member.php?mod=logging&action=login&loginsubmit=yes&inajax=1"
        login_data = {
            "username": username,
            "password": password
        }

        res = session.post(login_url, data=login_data, timeout=20)

        # 检查登录是否成功
        if res.status_code != 200:
            msg = f"登录失败：HTTP {res.status_code}"
            print(f"[{name}] {msg}")
            return msg

        print(f"[{name}] 登录成功")

        # 2. 领取任务
        time.sleep(2)
        task_apply_url = "https://i.pcbeta.com/home.php?mod=task&do=apply&id=149"
        res = session.get(task_apply_url, timeout=20)
        print(f"[{name}] 已领取任务")

        # 3. 完成任务（签到）
        time.sleep(2)
        task_draw_url = "https://i.pcbeta.com/home.php?mod=task&do=draw&id=149"
        res = session.get(task_draw_url, timeout=20)

        # 4. 检查结果
        result_text = res.text
        sign_status = ""
        if "成功完成" in result_text:
            sign_status = "签到成功"
        elif "不是进行中" in result_text or "已完成过" in result_text:
            sign_status = "今日已签到"
        else:
            sign_status = "签到完成"

        # 5. 获取积分信息
        time.sleep(2)
        credit_url = "https://i.pcbeta.com/home.php?mod=spacecp&ac=credit"
        try:
            res_credit = session.get(credit_url, timeout=20)
            credit_html = res_credit.text

            # 提取用户名
            nickname_match = re.search(r'访问我的空间">(.+?)<', credit_html)
            nickname = nickname_match.group(1) if nickname_match else username

            # 提取积分信息 (PB币部分)
            pb_section = re.search(r'<em>\s*PB币([\s\S]+?)</ul>', credit_html)
            if pb_section:
                pb_info = pb_section.group(0)
                # 清理HTML标签
                pb_clean = re.sub(r'<[^>]+>', ' ', pb_info)
                # 清理HTML实体
                pb_clean = pb_clean.replace('&nbsp;', ' ').replace('&amp;', '&')
                pb_clean = ' '.join(pb_clean.split())

                # 去掉公式部分（括号及其内容）
                pb_clean = re.sub(r'\s*\([^)]*总积分[^)]*\)\s*', '', pb_clean)

                info_msg = f"{nickname} {pb_clean}"
                result_msg += f"✓ {sign_status}\n{info_msg}"
                print(f"[{name}] ✓ {sign_status}")
                print(f"[{name}] {info_msg}")
            else:
                result_msg += f"✓ {sign_status}（未获取到积分详情）"
                print(f"[{name}] ✓ {sign_status}（未获取到积分详情）")
        except Exception as e:
            result_msg += f"✓ {sign_status}（获取积分信息失败: {e}）"
            print(f"[{name}] ✓ {sign_status}（获取积分信息失败: {e}）")

        return result_msg

    except Exception as e:
        msg = f"✗ 运行出错: {e}"
        print(f"[{name}] {msg}")
        return msg


def main():
    """主函数"""
    print("=" * 50)
    print("远景论坛（PCBeta）青龙面板签到脚本")
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
    send_webhook_notify("远景论坛签到结果", summary)


if __name__ == '__main__':
    main()
