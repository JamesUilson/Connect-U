"""
ConnectU — Database Migration Script
Mavjud SQLite/PostgreSQL bazasiga yangi ustunlar qo'shadi.
Server qayta ishga tushirilganda avtomatik ishga tushadi.

Ishlatish:
    python db_migrate.py
    yoki app.py ga qo'shish: from db_migrate import run_migrations
"""

import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

# ─── SQLite migration (lokal dev) ───
SQLITE_MIGRATIONS = [
    # Withdrawal jadvaliga yangi ustunlar
    "ALTER TABLE withdrawals ADD COLUMN card_name VARCHAR(50)",
    "ALTER TABLE withdrawals ADD COLUMN check_url VARCHAR(500)",
    # Status ni kengaytirish (SQLite da type yo'q, lekin default o'zgartiramiz)

    # MentorProfile yangi ustunlar
    "ALTER TABLE mentor_profiles ADD COLUMN card_name VARCHAR(50)",
    "ALTER TABLE mentor_profiles ADD COLUMN individual_price INTEGER DEFAULT 8000",
    "ALTER TABLE mentor_profiles ADD COLUMN group_price INTEGER DEFAULT 2000",
    "ALTER TABLE mentor_profiles ADD COLUMN pending_balance INTEGER DEFAULT 0",
    "ALTER TABLE mentor_profiles ADD COLUMN subjects TEXT",
    "ALTER TABLE mentor_profiles ADD COLUMN languages TEXT",

    # MentorPoint yangi ustunlar
    "ALTER TABLE mentor_points ADD COLUMN reason_text VARCHAR(200)",
    "ALTER TABLE mentor_points ADD COLUMN description VARCHAR(300)",

    # Material yangi ustunlar
    "ALTER TABLE materials ADD COLUMN mentor_id VARCHAR(36)",
    "ALTER TABLE materials ADD COLUMN access_type VARCHAR(20) DEFAULT 'free'",
    "ALTER TABLE materials ADD COLUMN thumbnail VARCHAR(500)",
    "ALTER TABLE materials ADD COLUMN description TEXT",
    "ALTER TABLE materials ADD COLUMN views INTEGER DEFAULT 0",
    "ALTER TABLE materials ADD COLUMN likes INTEGER DEFAULT 0",

    # Sessions jadvaliga yangi ustunlar (Telegram guruh sessiya uchun)
    "ALTER TABLE sessions ADD COLUMN tg_group_link VARCHAR(500)",
    "ALTER TABLE sessions ADD COLUMN tg_group_id VARCHAR(50)",
    "ALTER TABLE sessions ADD COLUMN started_at TIMESTAMP",
    "ALTER TABLE sessions ADD COLUMN terms_agreed INTEGER DEFAULT 0",

    # News yangi ustunlar
    "ALTER TABLE news ADD COLUMN category VARCHAR(50) DEFAULT 'general'",
    "ALTER TABLE news ADD COLUMN priority VARCHAR(20) DEFAULT 'normal'",
    "ALTER TABLE news ADD COLUMN link VARCHAR(500)",
    "ALTER TABLE news ADD COLUMN image_url VARCHAR(500)",
    "ALTER TABLE news ADD COLUMN target VARCHAR(20) DEFAULT 'all'",
]

# ─── PostgreSQL migration ───
POSTGRES_MIGRATIONS = [
    # Withdrawal
    "ALTER TABLE withdrawals ADD COLUMN IF NOT EXISTS card_name VARCHAR(50)",
    "ALTER TABLE withdrawals ADD COLUMN IF NOT EXISTS check_url VARCHAR(500)",

    # MentorProfile
    "ALTER TABLE mentor_profiles ADD COLUMN IF NOT EXISTS card_name VARCHAR(50)",
    "ALTER TABLE mentor_profiles ADD COLUMN IF NOT EXISTS individual_price INTEGER DEFAULT 8000",
    "ALTER TABLE mentor_profiles ADD COLUMN IF NOT EXISTS group_price INTEGER DEFAULT 2000",
    "ALTER TABLE mentor_profiles ADD COLUMN IF NOT EXISTS pending_balance INTEGER DEFAULT 0",
    "ALTER TABLE mentor_profiles ADD COLUMN IF NOT EXISTS subjects TEXT",
    "ALTER TABLE mentor_profiles ADD COLUMN IF NOT EXISTS languages TEXT",

    # MentorPoint
    "ALTER TABLE mentor_points ADD COLUMN IF NOT EXISTS reason_text VARCHAR(200)",
    "ALTER TABLE mentor_points ADD COLUMN IF NOT EXISTS description VARCHAR(300)",

    # Material (jadval nomi tekshiriladi)
    "ALTER TABLE materials ADD COLUMN IF NOT EXISTS mentor_id VARCHAR(36)",
    "ALTER TABLE materials ADD COLUMN IF NOT EXISTS access_type VARCHAR(20) DEFAULT 'free'",
    "ALTER TABLE materials ADD COLUMN IF NOT EXISTS thumbnail VARCHAR(500)",
    "ALTER TABLE materials ADD COLUMN IF NOT EXISTS description TEXT",
    "ALTER TABLE materials ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0",
    "ALTER TABLE materials ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0",

    # Sessions
    "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS tg_group_link VARCHAR(500)",
    "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS tg_group_id VARCHAR(50)",
    "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS started_at TIMESTAMP",
    "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS terms_agreed INTEGER DEFAULT 0",

    # News
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'general'",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'normal'",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS link VARCHAR(500)",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS target VARCHAR(20) DEFAULT 'all'",
]


def run_migrations_sqlite(db_path='connectu.db'):
    """SQLite bazasiga migration"""
    if not os.path.exists(db_path):
        print(f"SQLite bazasi topilmadi: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    applied = 0
    skipped = 0
    
    for sql in SQLITE_MIGRATIONS:
        try:
            cur.execute(sql)
            conn.commit()
            applied += 1
            col_name = sql.split('ADD COLUMN')[1].strip().split()[0] if 'ADD COLUMN' in sql else sql
            print(f"  ✅ {col_name}")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                skipped += 1
            else:
                print(f"  ⚠️  {e}")
    
    conn.close()
    print(f"\nSQLite migration: {applied} yangi, {skipped} mavjud")
    return True


def run_migrations_postgres(db_url=None):
    """PostgreSQL bazasiga migration"""
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 o'rnatilmagan, PostgreSQL migration o'tkazildi")
        return False
    
    db_url = db_url or os.environ.get('DATABASE_URL', '')
    if not db_url:
        return False
    
    # Render/Heroku postgres:// -> postgresql://
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        applied = 0
        errors = 0
        
        for sql in POSTGRES_MIGRATIONS:
            try:
                cur.execute(sql)
                applied += 1
                col_name = sql.split('ADD COLUMN IF NOT EXISTS')[1].strip().split()[0] if 'ADD COLUMN' in sql else sql[:50]
                print(f"  ✅ {col_name}")
            except Exception as e:
                errors += 1
                print(f"  ⚠️  {e}")
        
        cur.close()
        conn.close()
        print(f"\nPostgreSQL migration: {applied} muvaffaqiyatli, {errors} xato")
        return True
    except Exception as e:
        print(f"PostgreSQL ulanish xatosi: {e}")
        return False


def run_migrations():
    """Avtomatik DB turini aniqlab migration ishga tushiradi"""
    print("=" * 50)
    print("ConnectU DB Migration ishga tushmoqda...")
    print("=" * 50)
    
    db_url = os.environ.get('DATABASE_URL', '')
    
    if db_url and ('postgresql' in db_url or 'postgres' in db_url):
        print("PostgreSQL aniqlandi:")
        run_migrations_postgres(db_url)
    else:
        # SQLite uchun fayl qidirish
        possible_paths = ['connectu.db', 'instance/connectu.db', 'database.db', 'app.db']
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                print(f"SQLite bazasi topildi: {path}")
                run_migrations_sqlite(path)
                found = True
                break
        if not found:
            print("SQLite bazasi topilmadi. Flask app.create_all() dan keyin ishga tushiring.")
    
    print("=" * 50)
    print("Migration tugadi.")
    print("=" * 50)


if __name__ == '__main__':
    run_migrations()