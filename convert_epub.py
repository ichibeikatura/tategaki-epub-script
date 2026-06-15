#!/usr/bin/env python3
"""
Markdown to EPUB converter for vertical Japanese text.

Usage:
    cat input.md | python convert_epub.py
    python convert_epub.py < input.md
"""
import sys
import re
import subprocess
import os
import shutil
import zipfile
import time
from pathlib import Path

# --- デフォルト設定 ---
SCRIPT_DIR = Path(__file__).parent.resolve()

# 設定ファイルがあれば読み込む
CONFIG = {
    "css_path": SCRIPT_DIR / "epub.css",
    "output_dir": SCRIPT_DIR / "output",
    "temp_epub": SCRIPT_DIR / "temp.epub",
    # Bibi連携（Noneで無効化）
    "bibi_dir": None,      # 例: "/Library/WebServer/Documents/bibi-bookshelf/epub"
    "app_name": None,      # 例: "epub"
}

# config.py があれば上書き
_config_path = SCRIPT_DIR / "config.py"
if _config_path.exists():
    exec(_config_path.read_text(), CONFIG)


def convert_content(content: str) -> tuple[str, str]:
    """コンテンツを整形し、タイトルを抽出する。"""
    title_match = re.search(r'^#title:\s*(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "No Title"
    content = re.sub(r'^#title:.*$\n?', '', content, flags=re.MULTILINE)

    book_info_re = re.compile(r'^.+\s\d{4}$')
    timestamp_re = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:')
    url_re = re.compile(r'^https?://')
    page_re = re.compile(r'^p\d+')

    output_lines = []
    for line in content.split('\n'):
        s = line.rstrip()
        if not s:
            output_lines.append('')
        elif url_re.match(s):
            output_lines.append(f'<{s}>')
            output_lines.append('')
        elif timestamp_re.match(s):
            output_lines.append(s)
            output_lines.append('')
        elif page_re.match(s):
            m = page_re.match(s)
            page_num = m.group(0)
            rest = s[len(page_num):].strip()
            line = f'（{page_num}）{rest}' if rest else f'（{page_num}）'
            output_lines.append(line)
            output_lines.append('')
        elif book_info_re.match(s):
            output_lines.append(f'\n**{s}**\n')
        else:
            output_lines.append(s)

    return title, '\n'.join(output_lines)


def generate_epub(content: str, title: str, css_path: Path, output_path: Path) -> None:
    """PandocでEPUBを生成する。"""
    cmd = [
        "pandoc",
        "-t", "epub3",
        "-o", str(output_path),
        "--css", str(css_path),
        "--metadata", f"title={title}",
        "--metadata", "lang=ja",
        "--metadata", "page-progression-direction=rtl",
        "--toc",
        "--toc-depth=2"
    ]

    try:
        subprocess.run(cmd, input=content, text=True, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Pandoc Error:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: pandoc not found. Please install pandoc.", file=sys.stderr)
        sys.exit(1)


def deploy_to_bibi(epub_path: Path, target_dir: Path) -> None:
    """EPUBをBibi用ディレクトリに展開する。"""
    print(f"Deploying to {target_dir} ...")

    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    try:
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        print("Done.")
    except Exception as e:
        print(f"Deployment Error: {e}", file=sys.stderr)
        sys.exit(1)


def restart_app(app_name: str) -> None:
    """macOSアプリを再起動する。"""
    print(f"Restarting '{app_name}' app...")
    try:
        subprocess.run(["osascript", "-e", f'quit app "{app_name}"'], 
                       check=False, capture_output=True)
    except FileNotFoundError:
        pass  # macOS以外では無視
    
    time.sleep(0.1)
    
    try:
        subprocess.run(["open", "-a", app_name], check=False, capture_output=True)
    except FileNotFoundError:
        pass


def main():
    content = sys.stdin.read()
    title, content = convert_content(content)
    
    css_path = Path(CONFIG["css_path"])
    temp_epub = Path(CONFIG["temp_epub"])
    output_dir = Path(CONFIG["output_dir"])
    
    if not css_path.exists():
        print(f"Error: CSS file not found: {css_path}", file=sys.stderr)
        sys.exit(1)
    
    # EPUB生成
    generate_epub(content, title, css_path, temp_epub)

    # Bibi連携が設定されている場合は展開（+アプリ再起動）
    bibi_dir = CONFIG.get("bibi_dir")
    app_name = CONFIG.get("app_name")

    if bibi_dir:
        deploy_to_bibi(temp_epub, Path(bibi_dir))
        if app_name:
            restart_app(app_name)

    # Bibi連携の有無にかかわらず、output に .epub を残す（iBooks等で使える）
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{title}.epub"
    shutil.move(temp_epub, output_file)
    print(f"Created: {output_file}")


if __name__ == "__main__":
    main()
