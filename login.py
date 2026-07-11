# 티스토리 세션 관리를 위한 최초 로그인 및 Persistent Context 저장 스크립트

import os
import json
import sys
import time
from playwright.sync_api import sync_playwright

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.", flush=True)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run():
    config = load_config()
    user_data_dir = os.path.abspath(config.get("user_data_dir", "user_data"))
    
    print("=" * 60, flush=True)
    print("티스토리 자동화 프로그램 - 최초 로그인 세션 생성", flush=True)
    print(f"세션 저장 경로: {user_data_dir}", flush=True)
    print("=" * 60, flush=True)
    print("1. 브라우저가 열리면 카카오/티스토리 계정으로 로그인해 주세요.", flush=True)
    print("2. 로그인이 완료된 후 브라우저 창을 완전히 닫아주시면 세션이 저장되고 프로그램이 종료됩니다.", flush=True)
    print("=" * 60, flush=True)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.new_page()
        page.goto("https://www.tistory.com/auth/login")
        
        # 페이지가 닫힐 때까지 대기 (가장 안정적인 방식)
        try:
            print("로그인 완료 후 브라우저를 닫을 때까지 대기 중...", flush=True)
            page.wait_for_event("close", timeout=0)
        except Exception as e:
            print(f"\n대기 중 브라우저 연결 종료: {e}", flush=True)
        finally:
            context.close()
            print("브라우저가 닫혔습니다. 세션 정보가 성공적으로 저장되었습니다.", flush=True)

if __name__ == "__main__":
    run()
