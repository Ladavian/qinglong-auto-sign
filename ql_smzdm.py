#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
什么值得买（SMZDM）青龙面板任务入口

青龙面板（订阅管理 / ql repo）只把文件名匹配白名单 ql_ 的脚本创建为任务，
本文件即为此入口：通过 os.path.realpath 定位本仓库真实目录（兼容青龙将脚本
软链到 /ql/scripts/ 的执行方式），然后调用内置的完整功能模块
script/smzdm/sign_daily_task/main.py（该模块本身零改动）。

配置：
- 账号: 仓库根目录 config/token.json（参考 config/template_token.json）
- 通知: 环境变量 CUSTOM_WEBHOOK_URL 或 config/notification.json
"""
import os
import sys

# 青龙会以软链方式在 /ql/scripts/ 下执行本文件，__file__ 指向软链位置，
# realpath 可解析回仓库真实路径（无论仓库在 /ql/repo/ 还是 /ql/scripts/）
repo_root = os.path.dirname(os.path.realpath(__file__))
main_py = os.path.join(repo_root, 'script', 'smzdm', 'sign_daily_task', 'main.py')

if not os.path.exists(main_py):
    print(f"❌ 未找到内置 SMZDM 模块: {main_py}")
    print("请确认本文件位于 qinglong-auto-sign 仓库内（应通过订阅/ql repo 拉取，而非单独复制）")
    sys.exit(1)

# 将仓库根与 sign_daily_task 目录加入 sys.path，供 main.py 的模块导入使用
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
task_dir = os.path.join(repo_root, 'script', 'smzdm', 'sign_daily_task')
if task_dir not in sys.path:
    sys.path.insert(0, task_dir)

# 导入内置模块并执行（main.py 内部基于 __file__ 推导配置路径，此处为仓库真实路径）
from script.smzdm.sign_daily_task.main import main as smzdm_main

if __name__ == '__main__':
    sys.exit(smzdm_main())
