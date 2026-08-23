#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远景论坛（PCBeta）签到脚本（daidai-panel / 青龙通用）
支持 Cookie 方式（推荐）与账号密码方式

远景的签到是"回帖打卡"任务（每期一个，任务 id 与回帖帖子每期变化）：
申请任务 → 到打卡帖回复 → 领取奖励（PB币）。

环境变量配置：
export pcbeta_cookie="jqCP_887f_auth=xxx&jqCP_887f_auth=yyy"   # 推荐：浏览器登录后获取，多账号用 & 分隔
export pcbeta_reply_content="打卡签到"                          # 可选：回帖内容（默认"打卡签到"）
export pcbeta_username="user1&user2"                            # 备用：账号密码
export pcbeta_password="pass1&pass2"
export CUSTOM_WEBHOOK_URL="https://your-webhook-url.com/api/notify"  # 可选

多账号用 & 或 @ 或 \n 分隔。

Cookie 获取：浏览器登录 https://i.pcbeta.com 后，F12 → Application → Cookies
→ i.pcbeta.com，复制 jqCP_887f_auth 的值。
"""
import os
import re
import sys
import time
import json
import requests

# 远景论坛基础地址
PC_BASE = "https://i.pcbeta.com"
PC_BBS = "https://bbs.pcbeta.com"


def get_env():
    """
    获取环境变量配置

    优先使用 Cookie 方式（pcbeta_cookie），其次账号密码方式
    """
    cookie_str = os.environ.get('pcbeta_cookie', '').strip()

    if cookie_str:
        accounts = []
        for i, c in enumerate(cookie_str.split('&'), 1):
            c = c.strip()
            if c:
                accounts.append({'cookie': c, 'name': f'Cookie账号{i}'})
        if accounts:
            return accounts
        print('环境变量 pcbeta_cookie 中没有有效的 Cookie')

    username = os.environ.get('pcbeta_username', '')
    password = os.environ.get('pcbeta_password', '')

    if not username or not password:
        print('未配置环境变量 pcbeta_cookie 或 pcbeta_username/pcbeta_password')
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
        headers = {"Content-Type": "application/json; charset=utf-8"}

        response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)

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


def make_session():
    """创建带标准请求头的会话"""
    ua = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")
    s = requests.Session()
    s.headers.update({
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    return s


def bypass_js_challenge(session):
    """
    绕过远景论坛 JS 挑战防护

    远景对无会话的新访问会返回 JS 挑战页（需设置 access_js_verified 等 cookie 后重载），
    未通过验证的会话在部分网络/IP 下会直接返回 403。
    """
    try:
        resp = session.get(f"{PC_BASE}/", timeout=20)
        if "access_js_verified" in resp.text:
            session.cookies.set("access_js_verified", "1", domain="pcbeta.com", path="/")
            session.cookies.set("access_js_platform", "MacIntel", domain="pcbeta.com", path="/")
            resp = session.get(f"{PC_BASE}/", timeout=20)
            if "access_js_verified" in resp.text:
                print("[远景论坛] ⚠️ JS 挑战验证失败，仍被拦截")
                return False
        return True
    except Exception as e:
        print(f"[远景论坛] 访问论坛异常: {e}")
        return False


def get_formhash(session):
    """获取登录页 formhash（Discuz 登录必需参数）"""
    try:
        resp = session.get(f"{PC_BASE}/member.php?mod=logging&action=login", timeout=20)
        m = re.search(r'name="formhash" value="([a-f0-9]+)"', resp.text)
        return m.group(1) if m else ""
    except Exception as e:
        print(f"[远景论坛] 获取登录页异常: {e}")
        return ""


def _text(html, n=300):
    """HTML 转纯文本摘要"""
    t = re.sub(r"<script[\s\S]*?</script>", " ", html)
    t = re.sub(r"<[^>]+>", " ", t)
    return " ".join(t.split())[:n]


def get_task_and_thread(session):
    """
    获取本期"回帖打卡"任务 id 与回帖帖子 tid（每期变化，动态提取）

    依次检查：新任务页（未申请）→ 进行中 → 已完成，任何状态都能定位任务。

    Returns:
        (task_id, thread_tid, status, err)
        status: new / doing / done / ""
    """
    try:
        # 1. 新任务页（未申请）
        resp = session.get(f"{PC_BASE}/home.php?mod=task", timeout=20)
        html = resp.text
        if "登录" in html and "退出" not in html:
            return None, None, "", "未登录"
        if "access_js_verified" in html and len(html) < 1000:
            return None, None, "", "被 JS 挑战拦截"

        m = re.search(r'do=apply(?:&amp;|&)id=(\d+)', html)
        status = "new"
        if not m:
            # 2. 进行中的任务
            resp = session.get(f"{PC_BASE}/home.php?mod=task&item=doing", timeout=20)
            m = re.search(r'do=(?:draw|view)(?:&amp;|&)id=(\d+)', resp.text)
            status = "doing" if m else "done"
            if not m:
                # 3. 已完成的任务
                resp = session.get(f"{PC_BASE}/home.php?mod=task&item=done", timeout=20)
                m = re.search(r'do=view(?:&amp;|&)id=(\d+)', resp.text)
                status = "done" if m else ""
        if not m:
            return None, None, "", "本期无任务（新任务/进行中/已完成均为空）"
        task_id = m.group(1)

        # 任务详情页找回帖帖子链接
        resp2 = session.get(f"{PC_BASE}/home.php?mod=task&do=view&id={task_id}", timeout=20)
        t_match = re.search(r'thread-(\d+)-1-1\.html', resp2.text)
        thread_tid = t_match.group(1) if t_match else ""

        return task_id, thread_tid, status, ""
    except Exception as e:
        return None, None, "", f"获取任务信息异常: {e}"


def apply_task(session, task_id):
    """申请任务。返回: already(已申请) / ok(新申请) / other(提示文本)"""
    try:
        resp = session.get(
            f"{PC_BASE}/home.php?mod=task&do=apply&id={task_id}", timeout=20,
            headers={"Referer": f"{PC_BASE}/home.php?mod=task"},
        )
        text = resp.text
        if "申请过此任务" in text or "请下期再来" in text:
            return "already"
        if "成功" in text:
            return "ok"
        return "other:" + _text(text, 100)
    except Exception as e:
        return f"other:apply异常 {e}"


def reply_thread(session, thread_tid, content):
    """
    到打卡帖回帖。返回: ok(已回帖/无需回帖) / err(错误提示)
    """
    try:
        # 打开帖子页，提取 fid / formhash，检查是否已回帖
        resp = session.get(f"{PC_BBS}/viewthread-{thread_tid}-1-1.html", timeout=20)
        html = resp.text
        fh = re.search(r'name="formhash" value="([a-f0-9]+)"', html)
        fid_m = re.search(r'reply&fid=(\d+)', html)
        formhash = fh.group(1) if fh else ""
        fid = fid_m.group(1) if fid_m else ""
        if not formhash or not fid:
            return "err:帖子页参数提取失败（可能被风控拦截）"

        # 已回帖检查（页面出现本账号回复楼层会多出现一次 uid 链接）
        uid_m = re.search(r"discuz_uid = '(\d+)'", html)
        uid = uid_m.group(1) if uid_m else ""
        if uid and html.count(f"space-uid-{uid}") > 1:
            return "ok"  # 已有回复，无需重复回帖

        # 回帖（Discuz 快速回复）
        reply_url = (
            f"{PC_BBS}/forum.php?mod=post&action=reply&fid={fid}&tid={thread_tid}"
            "&extra=page%3D1&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1"
        )
        data = {
            "formhash": formhash,
            "message": content,
            "posttime": str(int(time.time())),
            "noticeauthor": "",
            "noticetrimstr": "",
            "noticepm": "1",
            "usesig": "0",
            "subject": "",
        }
        rr = session.post(reply_url, data=data, timeout=25, headers={
            "Referer": f"{PC_BBS}/viewthread-{thread_tid}-1-1.html",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        if rr.status_code != 200:
            return f"err:回帖 HTTP {rr.status_code}"
        body = rr.text
        if "间隔少于" in body or "post_floodctrl" in body:
            return "ok"  # 刚回帖过（防灌水），视为已完成
        if "回复发布成功" in body or "succeed" in body or len(body) < 600:
            return "ok"
        return "err:" + _text(body, 120)
    except Exception as e:
        return f"err:回帖异常 {e}"


def draw_task(session, task_id):
    """领取任务奖励。返回提示文本"""
    try:
        resp = session.get(
            f"{PC_BASE}/home.php?mod=task&do=draw&id={task_id}", timeout=20,
            headers={"Referer": f"{PC_BASE}/home.php?mod=task&item=doing"},
        )
        text = resp.text
        if "成功" in text:
            return "领取成功"
        if "已完成" in text or "领取" in text and "重复" in text:
            return "已领取过"
        if "您还没有开始执行任务" in text:
            return "任务未完成（回帖可能未被识别，请手动检查）"
        return _text(text, 80)
    except Exception as e:
        return f"领取异常 {e}"


def get_credit_info(session, fallback_name):
    """获取积分信息"""
    try:
        resp = session.get(f"{PC_BASE}/home.php?mod=spacecp&ac=credit", timeout=20)
        html = resp.text
        nickname_match = re.search(r'访问我的空间">(.+?)<', html)
        nickname = nickname_match.group(1) if nickname_match else fallback_name

        pb_section = re.search(r'<em>\s*PB币([\s\S]+?)</ul>', html)
        if pb_section:
            pb_info = pb_section.group(0)
            pb_clean = re.sub(r'<[^>]+>', ' ', pb_info)
            pb_clean = pb_clean.replace('&nbsp;', ' ').replace('&amp;', '&')
            pb_clean = ' '.join(pb_clean.split())
            pb_clean = re.sub(r'\s*\([^)]*总积分[^)]*\)\s*', '', pb_clean)
            return f"{nickname} {pb_clean}"
        return f"{nickname}（未获取到积分详情）"
    except Exception as e:
        return f"获取积分信息失败: {e}"


def sign_in(account):
    """
    远景论坛签到（申请任务 → 回帖打卡 → 领取奖励）

    Args:
        account: 账号信息字典，两种方式：
            - Cookie 方式: {'cookie': 'jqCP_887f_auth=xxx'}
            - 账号密码: {'username': 'xxx', 'password': 'xxx'}

    Returns:
        str: 签到结果消息
    """
    name = "远景论坛"
    result_msg = f"[{name}] "
    cookie = account.get('cookie', '')
    username = account.get('username', '')
    password = account.get('password', '')

    try:
        session = make_session()

        # 绕过远景 JS 挑战防护（未通过验证的会话会被 403 拦截）
        if not bypass_js_challenge(session):
            msg = "访问论坛失败（网络异常或 IP 被临时限制），请稍后重试"
            print(f"[{name}] {msg}")
            return msg

        if cookie:
            # ===== Cookie 方式（推荐）：直接使用浏览器登录态 =====
            print(f"[{name}] 使用 Cookie 方式（免登录）...")
            session.headers["Cookie"] = cookie
            resp = session.get(f"{PC_BASE}/home.php?mod=space&uid=1", timeout=20)
            if resp.status_code == 403:
                msg = "Cookie 无效：IP 被远景临时限制或触发风控，请稍后重试"
                print(f"[{name}] {msg}")
                return msg
            if "登录" in resp.text and "退出" not in resp.text:
                msg = "Cookie 无效或已过期，请重新从浏览器获取 jqCP_887f_auth"
                print(f"[{name}] {msg}")
                return msg
            print(f"[{name}] 登录态有效")
        else:
            # ===== 账号密码方式 =====
            print(f"[{name}] 开始登录...")
            formhash = get_formhash(session)
            if not formhash:
                msg = "获取登录参数失败，可能触发了验证码或风控，请稍后重试"
                print(f"[{name}] {msg}")
                return msg

            login_url = f"{PC_BASE}/member.php?mod=logging&action=login&loginsubmit=yes&inajax=1"
            login_data = {
                "username": username,
                "password": password,
                "formhash": formhash,
                "questionid": "0",
                "answer": "",
            }
            login_headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{PC_BASE}/member.php?mod=logging&action=login",
            }
            res = session.post(login_url, data=login_data, headers=login_headers, timeout=20)

            if res.status_code == 403:
                msg = "登录失败：HTTP 403（IP 被远景临时限制或触发风控，建议等待一段时间后重试）"
                print(f"[{name}] {msg}")
                return msg
            if res.status_code != 200:
                msg = f"登录失败：HTTP {res.status_code}"
                print(f"[{name}] {msg}")
                return msg

            login_ok = any("auth" in c.name for c in session.cookies) or "succeed" in res.text
            if not login_ok:
                fail_reason = re.sub(r"<[^>]+>", "", res.text).strip()[:120] or "未知原因"
                msg = f"登录失败：{fail_reason}"
                print(f"[{name}] {msg}")
                return msg
            print(f"[{name}] 登录成功")

        # ===== 打卡签到流程 =====
        task_id, thread_tid, task_status, task_err = get_task_and_thread(session)
        if task_err:
            msg = f"获取任务失败：{task_err}"
            print(f"[{name}] {msg}")
            return msg
        print(f"[{name}] 本期任务 id={task_id}, 打卡帖 tid={thread_tid}, 状态={task_status}")

        if task_status == "done":
            # 已完成：直接输出积分信息
            time.sleep(1)
            credit = get_credit_info(session, username or account.get('name') or '未知用户')
            print(f"[{name}] ✓ 本期打卡已完成（无需重复签到）")
            print(f"[{name}] {credit}")
            result_msg += f"✓ 本期打卡已完成（今日无需重复）\n{credit}"
            return result_msg

        # 1. 申请任务（仅 new 状态需要）
        if task_status == "new":
            apply_res = apply_task(session, task_id)
            if apply_res == "ok":
                print(f"[{name}] ✓ 任务申请成功")
            elif apply_res == "already":
                print(f"[{name}] 任务已申请过（今天或本期）")
            else:
                msg = apply_res
                print(f"[{name}] {msg}")
                return result_msg + msg
        else:
            print(f"[{name}] 任务已申请（进行中），直接打卡")

        # 2. 回帖打卡（已回帖则自动跳过）
        if thread_tid:
            reply_content = os.environ.get('pcbeta_reply_content', '').strip() or "打卡签到"
            time.sleep(1)
            reply_res = reply_thread(session, thread_tid, reply_content)
            if reply_res == "ok":
                print(f"[{name}] ✓ 打卡回帖完成")
            else:
                msg = reply_res
                print(f"[{name}] ✗ {msg}")
                return result_msg + msg

        # 3. 领取奖励
        time.sleep(2)
        draw_msg = draw_task(session, task_id)
        print(f"[{name}] 领取结果: {draw_msg}")

        # 4. 积分信息
        time.sleep(1)
        credit = get_credit_info(session, username or account.get('name') or '未知用户')
        print(f"[{name}] {credit}")

        result_msg += f"✓ {draw_msg}\n{credit}"
        return result_msg

    except Exception as e:
        msg = f"✗ 运行出错: {e}"
        print(f"[{name}] {msg}")
        return msg


def main():
    """主函数"""
    print("=" * 50)
    print("远景论坛（PCBeta）签到脚本")
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
        print(f"开始处理第 {i}/{len(accounts)} 个账号: {account.get('name') or account.get('username', '未知账号')}")
        print(f"{'='*50}")

        result = sign_in(account)
        results.append(f"账号{i}({account.get('name') or account.get('username', '未知账号')}): {result}")

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
