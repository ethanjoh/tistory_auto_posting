# SQLite를 사용하여 자동 발행 성공 기록 및 일일 한도를 트래킹하는 데이터베이스 모듈

import os
import sqlite3
from datetime import datetime, timedelta

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

def get_recent_24h_posts():
    """
    최근 24시간 이내에 성공적으로 발행된 모든 글의 published_at 값을 오름차순 정렬된 리스트로 반환합니다.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 24시간 전 시각 계산
    limit_time = (datetime.now() - timedelta(hours=24)).isoformat()
    
    cursor.execute("""
        SELECT published_at 
        FROM posts 
        WHERE status = 'success' AND published_at >= ?
        ORDER BY published_at ASC
    """, (limit_time,))
    
    rows = cursor.fetchall()
    posts_24h = [row["published_at"] for row in rows]
    conn.close()
    return posts_24h

def get_next_available_time(posts_24h, limit=50):
    """
    24시간 내 발행 글 개수 제한이 풀려 다음 글 발행이 가능한 시점을 계산하여 반환합니다.
    posts_24h: 오름차순 정렬된 published_at(str) 리스트
    """
    if len(posts_24h) < limit:
        return datetime.now()
    
    # limit개 이상의 글 중 가장 오래된 글(또는 limit번째 글)의 발행일시 + 24시간
    target_idx = len(posts_24h) - limit
    target_time_str = posts_24h[target_idx]
    
    try:
        target_time = datetime.fromisoformat(target_time_str)
    except ValueError:
        try:
            target_time = datetime.strptime(target_time_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            target_time = datetime.now()
            
    return target_time + timedelta(hours=24)

# 단독 실행 시 DB 초기화 진행
if __name__ == "__main__":
    init_db()
    print(f"오늘 발행된 글 수: {get_today_post_count()}개")
