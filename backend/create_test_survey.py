#!/usr/bin/env python
"""创建测试问卷的脚本 - 直接操作 SQLite"""

import sqlite3
import secrets
import json
import os
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "survey.db")

def create_test_survey():
    """创建蔚蓝档案测试问卷"""
    
    # 确保 data 目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 生成问卷码
    code = secrets.token_urlsafe(8)[:8]
    now = datetime.utcnow().isoformat()
    
    # 插入问卷
    cursor.execute("""
        INSERT INTO surveys (title, description, code, is_active, is_random, random_count, created_at, updated_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "蔚蓝档案玩家调查",
        "欢迎参与蔚蓝档案玩家调查问卷！请如实填写以下问题。",
        code,
        1,  # is_active = True
        0,  # is_random = False
        None,  # random_count
        now,
        now,
        None,  # created_by
    ))
    
    survey_id = cursor.lastrowid
    
    # 问题1：是否玩过蔚蓝档案（单选）
    options1 = json.dumps([
        {"value": "yes", "label": "是，我正在玩"},
        {"value": "played", "label": "是，但已经不玩了"},
        {"value": "no", "label": "否，没有玩过"},
    ])
    cursor.execute("""
        INSERT INTO questions (survey_id, title, description, type, options, is_required, "order", validation, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        survey_id,
        "你是否玩过《蔚蓝档案》？",
        "请选择一个选项",
        "single",
        options1,
        1,  # is_required = True
        0,  # order
        None,
        now,
    ))
    
    # 问题2：上传大厅截图（图片）
    validation2 = json.dumps({"max_images": 3})
    cursor.execute("""
        INSERT INTO questions (survey_id, title, description, type, options, is_required, "order", validation, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        survey_id,
        "请上传你的蔚蓝档案大厅截图",
        "请上传一张能展示你游戏进度的大厅截图",
        "image",
        None,
        1,  # is_required = True
        1,  # order
        validation2,
        now,
    ))
    
    # 问题3：列出攻击与护盾类型（简答）
    validation3 = json.dumps({"min_length": 10, "max_length": 500})
    cursor.execute("""
        INSERT INTO questions (survey_id, title, description, type, options, is_required, "order", validation, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        survey_id,
        "请列出游戏中所有的攻击类型与护盾类型",
        "例如：爆发攻击、贯穿攻击等。请尽可能完整地列出。",
        "text",
        None,
        1,  # is_required = True
        2,  # order
        validation3,
        now,
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ 问卷创建成功！")
    print(f"   问卷 ID: {survey_id}")
    print(f"   问卷标题: 蔚蓝档案玩家调查")
    print(f"   问卷码: {code}")
    print(f"   问题数量: 3")


if __name__ == "__main__":
    create_test_survey()

