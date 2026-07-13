# 티스토리 백업 게시글을 자동으로 파싱하여 이미지 업로드 및 포스팅을 실행하는 메인 엔진 스크립트

import os
import json
import sys
import time
import random
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import parser_utils
import db_utils

def ensure_login(page):
    """
    로그인 페이지로 리다이렉트된 경우, 카카오 로그인 버튼 및 간편로그인 프로필을 클릭하여 세션을 연동합니다.
    """
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
            
    if "kakao.com" in page.url and "simple" in page.url:
        print("[INFO] 카카오 간편로그인 화면 감지. 프로필 클릭을 시도합니다...")
        profile_btn = page.locator("a.wrap_profile").first
        if profile_btn.count() > 0:
            print("[INFO] 프로필 버튼을 클릭하여 간편 로그인을 완료합니다.")
            profile_btn.click()
            page.wait_for_timeout(8000)
        else:
            print("[WARNING] 간편로그인 프로필 버튼(a.wrap_profile)을 찾지 못했습니다.")

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        print(f"[ERROR] config.json 파일을 찾을 수 없습니다.")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def random_sleep(min_ms, max_ms):
    """지정한 범위 내에서 무작위로 대기합니다."""
    sleep_time = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
    time.sleep(sleep_time)

def human_type(locator, text, min_delay_ms=50, max_delay_ms=150):
    """사람이 직접 타이핑하는 것처럼 글자 단위로 딜레이를 주며 입력합니다."""
    locator.focus()
    locator.press("Control+A")
    locator.press("Delete")
    for char in text:
        locator.type(char)
        random_sleep(min_delay_ms, max_delay_ms)

def get_numeric_folders(workspace_dir):
    """작업 디렉토리 내에서 숫자로 된 백업 폴더 목록을 정렬하여 가져옵니다."""
    folders = []
    for item in os.listdir(workspace_dir):
        item_path = os.path.join(workspace_dir, item)
        if os.path.isdir(item_path) and re.match(r"^\d+$", item):
            folders.append(int(item))
    folders.sort()
    return [str(f) for f in folders]

def find_html_file(folder_path, folder_name):
    """백업 폴더 내에서 해당하는 HTML 파일을 찾습니다."""
    for file in os.listdir(folder_path):
        if file.startswith(f"{folder_name}-") and file.endswith(".html"):
            return os.path.join(folder_path, file)
    return None


def publish_one(page, config, selected_folder, folder_path, html_file):
    """하나의 백업 폴더를 발행합니다. 성공 시 True, 실패 시 False 반환."""
    blog_name = config.get("blog_name", "your-blog-name")
    write_url = f"https://{blog_name}.tistory.com/manage/post"
    
    delays = config.get("delays", {})
    action_min = delays.get("action_min_ms", 1000)
    action_max = delays.get("action_max_ms", 3000)
    
    # HTML 파싱
    try:
        parsed_data = parser_utils.parse_tistory_html(html_file)
    except Exception as e:
        print(f"[ERROR] HTML 파싱 실패: {e}")
        db_utils.record_publish_failure(selected_folder, f"파싱 실패: {e}")
        return False
        
    title = parsed_data["title"]
    category = parsed_data["category"]
    date_str = parsed_data.get("date", "")
    tags = parsed_data["tags"]
    content_html = parsed_data["content_html"]
    images = parsed_data["images"]
    
    # 날짜에서 연월일만 추출하여 제목 맨 뒤에 추가 (예: "제목 [2009-12-23]")
    if date_str:
        match = re.search(r"(\d{4}[-\./\s]\d{1,2}[-\./\s]\d{1,2})", date_str)
        if match:
            date_suffix = f" [{match.group(1).strip()}]"
        else:
            first_part = date_str.split()[0] if date_str else ""
            date_suffix = f" [{first_part}]" if first_part else ""
        
        if date_suffix:
            title = f"{title}{date_suffix}"
            
    print(f"  제목: {title}")
    print(f"  카테고리: {category}")
    print(f"  태그: {tags}")
    print(f"  이미지 개수: {len(images)}")
    
    print(f"  티스토리 에디터 이동 중: {write_url}")
    page.goto(write_url)
    page.wait_for_timeout(5000)
    
    ensure_login(page)
    page.wait_for_timeout(3000)
    
    if "login" in page.url or "auth" in page.url:
        print("[ERROR] 로그인 세션이 유효하지 않습니다. login.py를 먼저 실행해 주세요.")
        return False
        
    success = False
    try:
        # 5. 제목 입력
        print("제목 입력 중...")
        title_input = None
        title_selectors = [
            config.get("selectors", {}).get("title_textarea", "#post-title-inp"),
            "textarea.tf_title", 
            "input.tf_title", 
            "input[placeholder='제목을 입력하세요']", 
            "#tx_article_title"
        ]
        for sel in title_selectors:
            loc = page.locator(sel)
            if loc.count() > 0:
                title_input = loc.first
                break
        
        if title_input:
            human_type(title_input, title, delays.get("typing_min_ms", 50), delays.get("typing_max_ms", 150))
            title_input.blur()
        else:
            raise Exception("제목 입력 필드를 찾을 수 없습니다.")
            
        random_sleep(action_min, action_max)
        
        # 6. 이미지 업로드 (네트워크 인터셉트 설정)
        tistory_image_map = {}
        
        def handle_response(res):
            if "attach.json" in res.url and res.status == 200:
                try:
                    data = res.json()
                    orig_name = data.get("name")
                    cdn_url = data.get("url")
                    if orig_name and cdn_url:
                        tistory_image_map[orig_name] = cdn_url
                        print(f"  [네트워크 감지] 이미지 매핑 성공: {orig_name} -> {cdn_url[:60]}...")
                except Exception as e:
                    print(f"  [네트워크 감지 에러] {e}")
                    
        page.on("response", handle_response)
        
        if images:
            print(f"로컬 이미지 에디터에 업로드 진행 중 (총 {len(images)}개)...")
            for idx, img in enumerate(images):
                abs_path = img["absolute_path"]
                print(f"  [{idx+1}/{len(images)}] 이미지 업로드: {abs_path}")
                
                try:
                    page.evaluate("window.tinymce.activeEditor.focus()")
                    page.wait_for_timeout(500)
                    page.evaluate("document.querySelector('.mce-i-image').closest('button').click()")
                    page.wait_for_timeout(500)
                    
                    with page.expect_file_chooser() as fc_info:
                        page.evaluate("document.getElementById('attach-image').click()")
                    file_chooser = fc_info.value
                    file_chooser.set_files(abs_path)
                    page.wait_for_timeout(4000)
                except Exception as e:
                    print(f"  [{idx+1}/{len(images)}] 이미지 업로드 에러: {e}")
            
            random_sleep(action_min, action_max)
            
        # 7. 카테고리 선택 (완료 버튼 클릭 전에 수행)
        if category:
            cat_target = category.split("/")[-1].strip()
            print(f"카테고리 설정 시도: {cat_target}")
            
            category_btn = page.locator("#category-btn").first
            if category_btn.count() > 0:
                category_btn.click(force=True)
                page.wait_for_timeout(1000)
                
                cat_option = page.locator(f"div.mce-menu-item:has-text('{cat_target}'), li:has-text('{cat_target}'), .category-item:has-text('{cat_target}')").first
                if cat_option.count() > 0:
                    cat_option.click(force=True)
                    print(f"카테고리 '{cat_target}' 선택 성공.")
                else:
                    all_cats = page.locator("div.mce-menu-item, li.category-item").all()
                    cat_texts = [c.inner_text().strip() for c in all_cats[:20]]
                    print(f"[WARNING] 카테고리 '{cat_target}' 옵션을 찾을 수 없습니다. 사용 가능한 목록: {cat_texts}")
                    no_cat = page.locator("#category-item-0").first
                    if no_cat.count() > 0:
                        no_cat.click(force=True)
                    else:
                        page.keyboard.press("Escape")
            else:
                print("[WARNING] 카테고리 설정 버튼을 찾을 수 없어 건너뜁니다.")
                    
        page.wait_for_timeout(1000)
        
        # 8. 태그 입력 (완료 버튼 클릭 전에 수행)
        if tags:
            print("태그 입력 중...")
            tag_input = page.locator("#tagText").first
            if tag_input.count() == 0:
                tag_input = page.locator("input[name='tagText'], input.tf_g, .editor_tag input").first
            if tag_input.count() > 0:
                for tag in tags:
                    tag_input.click()
                    page.wait_for_timeout(200)
                    for char in tag:
                        tag_input.type(char)
                        random_sleep(50, 150)
                    tag_input.press("Enter")
                    random_sleep(500, 1000)
                print(f"태그 {len(tags)}개 입력 완료.")
            else:
                print("[WARNING] 태그 입력 요소를 찾을 수 없어 건너뜁니다.")
                
        # 9. 본문 HTML 가공 및 TinyMCE API를 통한 주입
        print("본문 HTML 가공 및 TinyMCE API 주입 진행...")
        processed_content = content_html
        
        for img in images:
            orig_src = img["original_src"]
            fname = os.path.basename(img["decoded_src"])
            if fname in tistory_image_map:
                cdn_url = tistory_image_map[fname]
                processed_content = processed_content.replace(orig_src, cdn_url)
                print(f"  [치환] {orig_src} -> {cdn_url[:60]}...")
            else:
                print(f"  [치환 실패] 매핑된 CDN URL 없음: {fname}")
        
        page.evaluate("""(content) => {
            const editor = window.tinymce.activeEditor;
            editor.setContent(content);
            editor.setDirty(true);
            editor.undoManager.add();
            editor.fire('change');
            editor.fire('input');
            editor.nodeChanged();
            
            const ta = document.getElementById('editor-tistory');
            if (ta) {
                ta.value = content;
                ta.dispatchEvent(new Event('input', { bubbles: true }));
                ta.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""", processed_content)
        print("에디터 본문 주입 및 이벤트 전파 완료.")
        random_sleep(action_min, action_max)
        
        # 10. 완료 버튼 클릭 및 설정 레이어 오픈
        print("완료 버튼 클릭 및 설정 레이어 진입...")
        publish_button_sel = config.get("selectors", {}).get("publish_button", "button:has-text('완료'), #publish-layer-btn")
        publish_trigger = page.locator(publish_button_sel).first
        if publish_trigger.count() > 0:
            publish_trigger.click()
        else:
            raise Exception("완료/발행 트리거 버튼을 찾을 수 없습니다.")
            
        page.wait_for_timeout(2000)
        
        # 11. 공개 설정 선택
        visibility = config.get("visibility", "private")
        visibility_kor = {"private": "비공개", "protected": "공개(보호)", "public": "공개"}.get(visibility, "비공개")
        
        print(f"공개설정 선택: {visibility_kor}")
        page.locator(f"button:has-text('{visibility_kor}')").first.click(force=True)
        page.wait_for_timeout(1000)
        
        # 12. 자동 저장 대기 및 DKAPTCHA 대응 루프
        print("발행 완료 대기 및 봇 방지 문자 감시 시작...")
        confirm_btn = page.locator("button#publish-btn").first
        button_enabled = False
        nav_success = False
        
        for attempt in range(60):  # 최대 2분 대기
            current_url = page.url
            if "/entry/" in current_url or "manage/posts" in current_url:
                nav_success = True
                print(f"  발행 성공 페이지로 이동 감지: {current_url}")
                break
            
            try:
                dkaptcha_detected = page.evaluate("""() => {
                    const text = document.body.innerText;
                    return text.includes('DKAPTCHA') || text.includes('지도에서') || text.includes('정답을 입력해주세요');
                }""")
                
                if dkaptcha_detected:
                    print(f"\a  [대기 {attempt*2}초] [WARN] 카카오 보안 문자(DKAPTCHA) 감지! 브라우저에서 인증을 완료해 주세요.")
                    page.wait_for_timeout(2000)
                    continue
                
                is_disabled = confirm_btn.evaluate("el => el.disabled")
                btn_text = confirm_btn.inner_text().strip()
                
                if not is_disabled and "저장중" not in btn_text:
                    button_enabled = True
                    print(f"  발행 버튼 활성화 상태 도달: '{btn_text}'")
                    break
                    
            except Exception as loop_err:
                print(f"  [루프 예외] {loop_err}")
                page.wait_for_timeout(2000)
                current_url = page.url
                if "/entry/" in current_url or "manage/posts" in current_url:
                    nav_success = True
                    print(f"  예외 후 발행 성공 URL 확인: {current_url}")
                break
                
            page.wait_for_timeout(2000)
            
        # 13. 최종 발행 처리
        if nav_success:
            db_utils.record_publish_success(selected_folder, title)
            print(f"[SUCCESS] {selected_folder} 폴더 글 발행 완료! 최종 URL: {page.url}")
            success = True
        elif button_enabled:
            print("최종 발행 진행...")
            try:
                confirm_btn.click(force=True)
                page.wait_for_timeout(8000)
            except Exception:
                page.wait_for_timeout(3000)
            
            current_url = page.url
            if "/entry/" in current_url or "manage/posts" in current_url or blog_name in current_url:
                db_utils.record_publish_success(selected_folder, title)
                print(f"[SUCCESS] {selected_folder} 폴더 글 발행 완료! 최종 URL: {current_url}")
                success = True
            else:
                raise Exception(f"발행 클릭 후 비정상 페이지 유지: {current_url}")
        else:
            raise Exception("발행 버튼이 활성화 상태에 도달하지 못했습니다 (캡차 미해결 또는 타임아웃).")
            
    except Exception as e:
        print(f"[ERROR] 자동 발행 중 오류 발생: {e}")
        db_utils.record_publish_failure(selected_folder, f"발행 중 에러: {e}")
        
    finally:
        # 응답 감시 리스너 제거로 메모리 누수 방지
        page.remove_listener("response", handle_response)
        print(f"  [{selected_folder}] 포스팅 단계 완료. (브라우저 유지)")
        
    return success


def main():
    config = load_config()
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. DB 초기화 및 일일 발행 개수 확인
    db_utils.init_db()
    today_count = db_utils.get_today_post_count()
    daily_limit = config.get("daily_limit", 10)
    min_delay_s = config.get("min_delay_seconds", 300)   # 기본 5분
    max_delay_s = config.get("max_delay_seconds", 900)   # 기본 15분
    
    print("=" * 60)
    print(f"티스토리 자동 업로드 엔진 시작 | 현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"오늘 발행 완료된 글: {today_count} / {daily_limit} 개")
    print("=" * 60)
    
    if today_count >= daily_limit:
        print(f"[INFO] 오늘 발행 제한 한도({daily_limit}개)에 이미 도달하였습니다. 프로그램을 종료합니다.")
        return
    
    # 1.2. 최근 24시간 이내 발행 수 제한 확인
    recent_24h_limit = config.get("recent_24h_limit", 50)
    posts_24h = db_utils.get_recent_24h_posts()
    recent_24h_count = len(posts_24h)
    
    print(f"최근 24시간 동안 발행 완료된 글: {recent_24h_count} / {recent_24h_limit} 개")
    print("=" * 60)
    
    if recent_24h_count >= recent_24h_limit:
        next_time = db_utils.get_next_available_time(posts_24h, recent_24h_limit)
        time_diff = next_time - datetime.now()
        hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        
        print(f"[WARNING] 최근 24시간 동안 {recent_24h_count}개의 글이 발행되어 제한 한도({recent_24h_limit}개)에 도달하였습니다.")
        print(f"[INFO] 다음 발행 가능 시간: {next_time.strftime('%Y-%m-%d %H:%M:%S')} (약 {hours}시간 {minutes}분 후)")
        print("[INFO] 프로그램을 종료합니다.")
        return
    
    # 2. 미발행 대상 폴더 수집
    all_folders = get_numeric_folders(workspace_dir)
    target_folders = [f for f in all_folders if not db_utils.is_already_published(f)]
    
    print(f"총 {len(all_folders)}개의 백업 폴더 중 미발행 폴더 {len(target_folders)}개 감지.")
    remaining = daily_limit - today_count
    print(f"이번 실행에서 최대 {min(remaining, len(target_folders))}개를 순차 발행합니다.")
    
    if not target_folders:
        print("[INFO] 새로 업로드할 백업 게시글이 없습니다.")
        return
    
    # 3. 브라우저 기동 및 발행 루프
    user_data_dir = os.path.abspath(config.get("user_data_dir", "user_data"))
    headless = config.get("headless", False)
    success_count = 0
    
    with sync_playwright() as p:
        print("[INFO] 브라우저를 기동합니다...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            viewport={"width": 1400, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.new_page()
        
        try:
            for i, selected_folder in enumerate(target_folders):
                current_today = db_utils.get_today_post_count()
                if current_today >= daily_limit:
                    print(f"\n[INFO] 오늘 발행 한도({daily_limit}개) 도달. 종료합니다.")
                    break
                
                folder_path = os.path.join(workspace_dir, selected_folder)
                html_file = find_html_file(folder_path, selected_folder)
                
                if not html_file:
                    print(f"[SKIP] 폴더 {selected_folder}: HTML 파일 없음, 건너뜁니다.")
                    db_utils.record_publish_failure(selected_folder, "HTML 파일 누락")
                    continue
                
                print(f"\n{'='*60}")
                print(f"[{i+1}번째 글] 발행 시작 | 현재 시각: {datetime.now().strftime('%H:%M:%S')}")
                
                ok = publish_one(page, config, selected_folder, folder_path, html_file)
                if ok:
                    success_count += 1
                
                # 마지막 글이 아니면 딜레이 (다음 글 발행 전 대기)
                next_today = db_utils.get_today_post_count()
                is_last = (i == len(target_folders) - 1) or (next_today >= daily_limit)
                if not is_last:
                    delay_s = random.randint(min_delay_s, max_delay_s)
                    eta = datetime.fromtimestamp(time.time() + delay_s).strftime('%H:%M:%S')
                    print(f"\n다음 글 발행까지 {delay_s // 60}분 {delay_s % 60}초 대기합니다... (예정: {eta})")
                    time.sleep(delay_s)
        finally:
            print("[INFO] 브라우저를 종료합니다...")
            context.close()
            
    print(f"\n{'='*60}")
    print(f"[완료] 오늘 총 발행: {db_utils.get_today_post_count()} / {daily_limit} 개")
    print(f"이번 실행 발행 성공: {success_count}개")


if __name__ == "__main__":
    main()
