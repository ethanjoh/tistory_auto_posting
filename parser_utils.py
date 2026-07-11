# 티스토리 백업 HTML 파일 및 로컬 이미지를 파싱하는 유틸리티

import os
from bs4 import BeautifulSoup

def parse_tistory_html(html_file_path):
    """
    티스토리 백업 HTML 파일을 파싱하여 메타데이터와 본문을 추출합니다.
    """
    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML 파일을 찾을 수 없습니다: {html_file_path}")

    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")

    # 1. 제목 (Title)
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text().strip()
    else:
        title_h2 = soup.find("h2", class_="title-article")
        if title_h2:
            title = title_h2.get_text().strip()

    # 2. 카테고리 (Category)
    category = ""
    category_tag = soup.find("p", class_="category")
    if category_tag:
        category = category_tag.get_text().strip()

    # 3. 발행일 (Date)
    date_str = ""
    date_tag = soup.find("p", class_="date")
    if date_tag:
        date_str = date_tag.get_text().strip()

    # 4. 태그 (Tags)
    tags = []
    tags_tag = soup.find("div", class_="tags")
    if tags_tag:
        tags_text = tags_tag.get_text()
        tags = [t.strip() for t in tags_text.split("#") if t.strip()]

    # 5. 본문 (Content HTML) - contents_style 클래스를 갖는 div 추출
    content_div = soup.find("div", class_="contents_style")
    content_html = ""
    if content_div:
        # contents_style 내부의 HTML만 문자열로 획득
        content_html = "".join([str(child) for child in content_div.contents])
    else:
        # 혹시 contents_style이 없으면 article-view 추출 시도
        article_view = soup.find("div", class_="article-view")
        if article_view:
            # tags 영역은 제외하고 본문만 추출하기 위해 tags div 제거
            tags_div = article_view.find("div", class_="tags")
            if tags_div:
                tags_div.decompose()
            content_html = "".join([str(child) for child in article_view.contents])

    # 6. 이미지 목록 추출
    # 본문 내의 모든 img 태그에서 src 속성을 추출하여 로컬 파일 경로 확인
    images = []
    html_dir = os.path.dirname(html_file_path)
    
    # 임시 수프 객체로 본문 분석
    content_soup = BeautifulSoup(content_html, "lxml")
    for img in content_soup.find_all("img"):
        src = img.get("src")
        if src:
            # 로컬 상대 경로인 경우 (예: ./img/SI853000-1.jpg, img/SI853000-1.jpg)
            # URL 형식 (http, https)이 아닌 경우만 처리
            if not src.startswith("http://") and not src.startswith("https://"):
                # URL 디코딩 처리 (한글 경로 등이 %로 인코딩되어 있을 수 있음)
                import urllib.parse
                decoded_src = urllib.parse.unquote(src)
                
                # 파일 경로 생성
                abs_img_path = os.path.normpath(os.path.join(html_dir, decoded_src))
                if os.path.exists(abs_img_path):
                    images.append({
                        "original_src": src,          # HTML 소스에 기재된 원래 문자열 (치환용)
                        "decoded_src": decoded_src,    # 디코딩된 상대 경로
                        "absolute_path": abs_img_path  # 실제 로컬 파일의 절대 경로 (업로드용)
                    })
                else:
                    print(f"[WARNING] 이미지 파일이 존재하지 않습니다: {abs_img_path}")

    return {
        "title": title,
        "category": category,
        "date": date_str,
        "tags": tags,
        "content_html": content_html,
        "images": images
    }

# 파서 단독 테스트용 코드
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        try:
            res = parse_tistory_html(test_path)
            print("=== PARSER TEST ===")
            print(f"Title: {res['title']}")
            print(f"Category: {res['category']}")
            print(f"Date: {res['date']}")
            print(f"Tags: {res['tags']}")
            print(f"Number of images: {len(res['images'])}")
            for idx, img in enumerate(res['images']):
                print(f"  Img {idx}: original_src={img['original_src']} -> path={img['absolute_path']}")
            print("Content Snippet:")
            print(res['content_html'][:200] + "...")
        except Exception as e:
            print(f"Error parsing: {e}")
    else:
        print("Usage: python parser_utils.py <path_to_html_file>")
