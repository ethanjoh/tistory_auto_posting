# 에디터 DOM 구조 및 셀렉터 분석을 위한 디버그 스크립트

import os
import json
import sys
import time
import re
from playwright.sync_api import sync_playwright

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("[CONFIG] config.json 파일이 업데이트되었습니다.")

def ensure_login(page):
    """
    로그인 페이지로 리다이렉트된 경우, 카카오 로그인 버튼 및 간편로그인 프로필을 클릭하여 세션을 연동합니다.
    """
    # 1. 티스토리 로그인 페이지 처리
    current_url = page.url
    if "login" in current_url or "auth" in current_url:
        print("[INFO] 로그인 페이지로 리다이렉트되었습니다. 카카오 로그인 버튼 클릭을 시도합니다...")
        
        kakao_selectors = [
            "a.link_kakao",
            ".btn_login",
            "span.txt_login:has-text('카카오계정 로그인')",
            "button:has-text('카카오계정 로그인')",
            "a:has-text('카카오계정 로그인')"
        ]
        
        button_clicked = False
        for sel in kakao_selectors:
            btn = page.locator(sel)
            if btn.count() > 0:
                print(f"[INFO] 카카오 로그인 버튼 발견: {sel}. 클릭합니다.")
                btn.first.click()
                button_clicked = True
                break
                
        if button_clicked:
            print("[INFO] 버튼 클릭 후 리다이렉션을 대기합니다...")
            page.wait_for_timeout(5000)
            
    # 2. 카카오 간편로그인 페이지 처리
    if "kakao.com" in page.url and "simple" in page.url:
        print("[INFO] 카카오 간편로그인 화면 감지. 프로필 클릭을 시도합니다...")
        profile_btn = page.locator("a.wrap_profile").first
        if profile_btn.count() > 0:
            print("[INFO] 프로필 버튼을 클릭하여 간편 로그인을 완료합니다.")
            profile_btn.click()
            page.wait_for_timeout(8000)
        else:
            print("[WARNING] 간편로그인 프로필 버튼(a.wrap_profile)을 찾지 못했습니다.")

def run():
    config = load_config()
    user_data_dir = os.path.abspath(config.get("user_data_dir", "user_data"))
    blog_name = config.get("blog_name", "your-blog-name")
    headless = config.get("headless", True)
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            viewport={"width": 1400, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.new_page()
        
        # blog_name이 기본값이면 계정 관리 페이지로 가서 블로그명 탐색
        if blog_name == "your-blog-name":
            print("[INFO] 블로그명이 설정되지 않았습니다. 계정 정보에서 블로그명을 자동으로 검색합니다...")
            page.goto("https://www.tistory.com/member/blog")
            page.wait_for_timeout(4000)
            
            # 로그인 체크 및 자동 로그인 시도
            ensure_login(page)
            
            # 페이지 URL 다시 검사
            if "login" in page.url or "auth" in page.url:
                print("[ERROR] 로그인 정보가 없거나 세션이 만료되었습니다. terminal에서 .\.venv\Scripts\python login.py를 다시 실행해 주세요.")
                context.close()
                return
                
            # 블로그 관리 혹은 링크에서 블로그 주소 추출
            links = page.locator("a").all()
            detected_blogs = []
            for link in links:
                href = link.get_attribute("href") or ""
                match = re.search(r"https://([^.]+)\.tistory\.com(?!/auth/login)(?!/member/blog)(/|$)", href)
                if match:
                    name = match.group(1)
                    if name not in ["www", "manager", "notice"] and name not in detected_blogs:
                        detected_blogs.append(name)
                        
            if detected_blogs:
                blog_name = detected_blogs[0]
                print(f"[SUCCESS] 감지된 블로그명: {blog_name} (검색된 후보군: {detected_blogs})")
                config["blog_name"] = blog_name
                save_config(config)
            else:
                print("[WARNING] 계정에서 블로그명을 자동으로 감지하지 못했습니다.")
                context.close()
                return

        write_url = f"https://{blog_name}.tistory.com/manage/post"
        print(f"글쓰기 페이지 접속 시도: {write_url}")
        page.goto(write_url)
        
        # 로딩 대기 후 로그인 체크 및 자동 로그인 시도
        page.wait_for_timeout(5000)
        ensure_login(page)
        
        # 최종 확인을 위해 5초 대기
        page.wait_for_timeout(5000)
        
        # 스크린샷 저장
        screenshot_path = os.path.abspath("editor_debug.png")
        page.screenshot(path=screenshot_path)
        print(f"현재 에디터 화면 스크린샷 저장 완료: {screenshot_path}")
        
        current_url = page.url
        print(f"현재 URL: {current_url}")
        
        if "login" in current_url or "auth" in current_url:
            print("[ERROR] 로그인 세션이 만료되었거나 로그인되어 있지 않습니다.")
            context.close()
            return
            
        print("\n--- 주요 요소 탐색 결과 ---")
        
        # 1. iframe 탐색
        iframes = page.frames
        print(f"발견된 iframe 개수: {len(iframes)}")
        for idx, frame in enumerate(iframes):
            print(f"  Frame {idx}: name={frame.name}, url={frame.url[:80]}...")
            
        # 2. 제목 입력란 후보군 확인
        title_selectors = [
            "textarea.tf_title",
            "input.tf_title",
            "input[placeholder='제목을 입력하세요']",
            "input#tx_article_title",
            "#post-title-inp"
        ]
        for sel in title_selectors:
            elem = page.locator(sel)
            if elem.count() > 0:
                print(f"[FOUND] 제목 입력 셀렉터 후보: {sel}")
                
        # 3. 기본모드/HTML 모드 전환 버튼 후보군 확인
        mode_btn = page.locator("button:has-text('기본모드'), span:has-text('기본모드')")
        if mode_btn.count() > 0:
            print(f"[FOUND] 모드 전환 드롭다운 버튼 후보 발견! (텍스트: 기본모드)")
        
        # 4. 완료/발행 버튼 후보군 확인
        publish_btn = page.locator("button:has-text('완료'), button:has-text('발행'), #publish-btn, .btn_publish")
        if publish_btn.count() > 0:
            print(f"[FOUND] 완료/발행 버튼 후보: {publish_btn.first.evaluate('el => el.outerHTML')[:100]}...")
            
        print("--------------------------")
        
        print("분석이 완료되었습니다. 5초 대기 후 브라우저를 자동 종료합니다...")
        time.sleep(5)
        context.close()

if __name__ == "__main__":
    run()
