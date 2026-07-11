# SQLite를 사용하여 자동 발행 성공 기록 및 일일 한도를 트래킹하는 데이터베이스 모듈

import os
import sqlite3
from datetime import datetime

# 데이터베이스 파일 경로
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db_connection():
    """
    SQLite 데이터베이스 연결을 생성하고 반환합니다.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    데이터베이스 테이블을 초기화합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # posts 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            folder_name TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            published_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("[DB] 데이터베이스가 정상적으로 초기화되었습니다.")

def get_today_post_count():
    """
    오늘 날짜(KST/로컬 날짜 YYYY-MM-DD 기준)에 성공적으로 발행된 글의 개수를 반환합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 오늘 날짜 구하기 (YYYY-MM-DD)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT COUNT(*) as cnt 
        FROM posts 
        WHERE status = 'success' AND published_at LIKE ?
    """, (f"{today_str}%",))
    
    row = cursor.fetchone()
    count = row["cnt"] if row else 0
    
    conn.close()
    return count

def is_already_published(folder_name):
    """
    해당 폴더의 백업 글이 이미 성공적으로 발행되었는지 확인합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT status 
        FROM posts 
        WHERE folder_name = ? AND status = 'success'
    """, (folder_name,))
    
    row = cursor.fetchone()
    conn.close()
    return row is not None

def record_publish_success(folder_name, title):
    """
    발행 성공 기록을 DB에 추가하거나 업데이트합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now_str = datetime.now().isoformat() # ISO 형식 (YYYY-MM-DDTHH:MM:SS.ffffff)
    
    cursor.execute("""
        INSERT INTO posts (folder_name, title, published_at, status)
        VALUES (?, ?, ?, 'success')
        ON CONFLICT(folder_name) DO UPDATE SET
            title = excluded.title,
            published_at = excluded.published_at,
            status = 'success'
    """, (folder_name, title, now_str))
    
    conn.commit()
    conn.close()
    print(f"[DB] 발행 성공 기록 완료: {folder_name} ({title})")

def record_publish_failure(folder_name, title):
    """
    발행 실패 기록을 DB에 추가하거나 업데이트합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now_str = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO posts (folder_name, title, published_at, status)
        VALUES (?, ?, ?, 'fail')
        ON CONFLICT(folder_name) DO UPDATE SET
            title = excluded.title,
            published_at = excluded.published_at,
            status = 'fail'
    """, (folder_name, title, now_str))
    
    conn.commit()
    conn.close()
    print(f"[DB] 발행 실패 기록 완료: {folder_name} ({title})")

# 단독 실행 시 DB 초기화 진행
if __name__ == "__main__":
    init_db()
    print(f"오늘 발행된 글 수: {get_today_post_count()}개")
