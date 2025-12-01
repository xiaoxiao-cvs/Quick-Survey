"""
数据库迁移脚本 - 添加提交时间记录字段
运行方式: python migrate_add_time_fields.py
"""
import sqlite3
from pathlib import Path


def migrate():
    db_path = Path("data/survey.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在，无需迁移")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(submissions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    migrations = []
    
    if "fill_duration" not in columns:
        migrations.append(
            "ALTER TABLE submissions ADD COLUMN fill_duration REAL"
        )
        print("📝 将添加 fill_duration 字段")
    
    if "first_viewed_at" not in columns:
        migrations.append(
            "ALTER TABLE submissions ADD COLUMN first_viewed_at DATETIME"
        )
        print("📝 将添加 first_viewed_at 字段")
    
    if not migrations:
        print("✅ 所有字段已存在，无需迁移")
        conn.close()
        return
    
    # 执行迁移
    for sql in migrations:
        try:
            cursor.execute(sql)
            print(f"✅ 执行成功: {sql}")
        except Exception as e:
            print(f"❌ 执行失败: {sql}")
            print(f"   错误: {e}")
    
    conn.commit()
    conn.close()
    print("\n🎉 迁移完成！")


if __name__ == "__main__":
    migrate()
