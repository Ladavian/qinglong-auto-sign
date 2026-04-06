#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
什么值得买（SMZDM）独立签到脚本 - 完整版
支持每日签到、众测任务、互动任务
完全独立，不依赖任何外部仓库

环境变量配置：
export smzdm_cookie="cookie1&cookie2"  # 多个账号用 & 或 @ 或换行分隔
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选
"""
import os
import re
import time
import requests
from datetime import datetime


def get_accounts():
    """获取账号列表"""
    cookie_str = os.environ.get('smzdm_cookie', '')
    if not cookie_str:
        print('❌ 未配置 smzdm_cookie')
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


def sign_in(cookie):
    """执行每日签到"""
    name = "什么值得买"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Cookie': cookie,
        'Accept': 'application/json',
        'Referer': 'https://www.smzdm.com/',
    }

    result = []
    try:
        # 签到
        resp = requests.post('https://user-api.smzdm.com/checkin',
                            headers=headers,
                            params={'touchstone_event': '', 'sk': '1'},
                            timeout=15)
        data = resp.json()

        if data.get('error_code') == 0:
            d = data.get('data', {})
            points = d.get('add_point', '0')
            days = d.get('continue_checkin_days', 0)
            result.append(f"✅ 签到成功")
            result.append(f"💰 获得积分: {points}")
            result.append(f"📅 连续签到: {days}天")
            print(f"[{name}] ✅ 签到成功 | +{points}积分 | 连续{days}天")
        elif '已签' in str(data.get('error_msg', '')):
            result.append("ℹ️ 今日已签到")
            print(f"[{name}] ℹ️ 今日已签到")
        else:
            result.append(f"❌ 签到失败: {data.get('error_msg', '未知错误')}")
            print(f"[{name}] ❌ 签到失败")

        # 获取用户信息
        time.sleep(2)
        resp = requests.get('https://user-api.smzdm.com/user/info', headers=headers, timeout=15)
        if resp.status_code == 200:
            udata = resp.json()
            if udata.get('error_code') == 0:
                u = udata.get('data', {})
                nickname = u.get('nickname', '-')
                level_info = u.get('level', {})
                level_name = level_info.get('level_name', '-') if isinstance(level_info, dict) else '-'
                gold = u.get('gold', '0')
                prestige = u.get('prestige', '0')
                result.append(f"👤 用户: {nickname}")
                result.append(f"🎖️ 等级: {level_name}")
                result.append(f"💎 金币: {gold} | 威望: {prestige}")
                print(f"[{name}] 用户: {nickname} | 等级: {level_name}")
    except Exception as e:
        result.append(f"❌ 签到异常: {str(e)}")
        print(f"[{name}] ✗ 签到异常: {e}")

    return "\n".join(result)


def get_zhongce_tasks(cookie):
    """获取众测任务列表"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'application/json',
        'Referer': 'https://try.smzdm.com/',
    }

    try:
        # 获取众测列表
        resp = requests.get('https://try-api.smzdm.com/home/list',
                           headers=headers,
                           params={'page': 1, 'per_page': 10},
                           timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('error_code') == 0:
                tasks = data.get('data', {}).get('rows', [])
                return tasks
    except Exception as e:
        print(f"获取众测任务失败: {e}")
    return []


def apply_zhongce(cookie, task_id):
    """申请众测任务"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'application/json',
        'Referer': 'https://try.smzdm.com/',
        'Origin': 'https://try.smzdm.com',
    }

    try:
        resp = requests.post('https://try-api.smzdm.com/trial/apply',
                            headers=headers,
                            json={'article_id': task_id},
                            timeout=15)
        data = resp.json()
        if data.get('error_code') == 0:
            return True, "申请成功"
        else:
            return False, data.get('error_msg', '申请失败')
    except Exception as e:
        return False, str(e)


def do_zhongce_tasks(cookie):
    """执行众测任务"""
    name = "什么值得买-众测"
    print(f"[{name}] 开始获取众测任务...")

    tasks = get_zhongce_tasks(cookie)
    if not tasks:
        msg = "未找到可申请的众测任务"
        print(f"[{name}] {msg}")
        return msg

    success_count = 0
    fail_count = 0
    results = []

    print(f"[{name}] 找到 {len(tasks)} 个众测任务")

    for task in tasks[:5]:  # 最多处理前5个任务
        task_id = task.get('article_id', '')
        task_title = task.get('article_title', '未知任务')
        print(f"[{name}] 尝试申请: {task_title}")

        time.sleep(2)
        success, message = apply_zhongce(cookie, task_id)

        if success:
            success_count += 1
            results.append(f"✅ {task_title}")
            print(f"[{name}] ✓ 申请成功")
        else:
            fail_count += 1
            results.append(f"❌ {task_title}: {message}")
            print(f"[{name}] ✗ 申请失败: {message}")

        time.sleep(2)

    summary = f"众测任务: 成功{success_count}个, 失败{fail_count}个"
    if results:
        summary += "\n" + "\n".join(results[:3])  # 只显示前3个结果

    print(f"[{name}] {summary}")
    return summary


def do_interactive_tasks(cookie):
    """执行互动任务（点赞、收藏等）"""
    name = "什么值得买-互动"
    print(f"[{name}] 开始执行互动任务...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Cookie': cookie,
        'Accept': 'application/json',
        'Referer': 'https://www.smzdm.com/',
    }

    success_count = 0
    total_count = 0

    try:
        # 获取首页文章列表
        resp = requests.get('https://home-api.smzdm.com/index/list',
                           headers=headers,
                           params={'limit': 5, 'offset': 0},
                           timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get('data', [])

            for article in articles[:3]:  # 处理前3篇文章
                article_id = article.get('article_id', '')
                if not article_id:
                    continue

                total_count += 1
                time.sleep(1)

                # 点赞
                try:
                    resp_like = requests.post('https://user-api.smzdm.com/likes/like',
                                            headers=headers,
                                            json={'article_id': article_id, 'channel': '1'},
                                            timeout=10)
                    if resp_like.status_code == 200:
                        success_count += 1
                except:
                    pass

                time.sleep(1)
    except Exception as e:
        print(f"[{name}] 互动任务异常: {e}")

    summary = f"互动任务: 成功{success_count}/{total_count}个"
    print(f"[{name}] {summary}")
    return summary


def process_account(cookie, index, total):
    """处理单个账号的所有任务"""
    print(f"\n{'='*60}")
    print(f"开始处理账号 {index}/{total}")
    print(f"{'='*60}")

    results = []

    # 1. 每日签到
    print("\n【1】执行每日签到...")
    sign_result = sign_in(cookie)
    results.append(sign_result)

    # 2. 众测任务
    print("\n【2】执行众测任务...")
    time.sleep(3)
    zhongce_result = do_zhongce_tasks(cookie)
    results.append(zhongce_result)

    # 3. 互动任务
    print("\n【3】执行互动任务...")
    time.sleep(3)
    interactive_result = do_interactive_tasks(cookie)
    results.append(interactive_result)

    return "\n".join(results)


def main():
    print("=" * 60)
    print("什么值得买（SMZDM）独立签到脚本 - 完整版")
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
    send_webhook("✅ SMZDM签到完成", summary)

    print("\n✨ 所有任务完成")


if __name__ == '__main__':
    main()
