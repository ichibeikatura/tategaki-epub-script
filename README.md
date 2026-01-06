# convert_epub

Markdown を縦書き日本語 EPUB に変換するスクリプト。[Bibi](https://bibi.epub.link) との連携に対応。

日本語長文を執筆する際に、縦書き表示で推敲のために思索するためのツール。以下の根拠でこのようになっている。

- ページめくりができること(テキストは止まる)
- いかに推敲するか思索する際に編集をする必要がない(エディタは見えなくていい)
- リアルタイム更新はいらない(横向きで書いている際に縦書き表示は必要ない)

## 必要環境

- Python 3.10+
- [Pandoc](https://pandoc.org/)

```bash
# macOS
brew install pandoc

# Ubuntu/Debian
sudo apt install pandoc
```

## 使い方

```bash
cat input.md | python convert_epub.py
# または
python convert_epub.py < input.md
```

デフォルトでは `output/` ディレクトリに EPUB ファイルが生成される。

### 入力フォーマット

```markdown
#title: タイトル

2024年1月1日 | 著者名
本文がここに入る。

2024年1月2日 | 著者名
別の日の本文。
```

`#title:` 行でタイトルを指定。`YYYY年M月D日 | 名前` 形式の行は自動的に見出し（H2）に変換される。

## 設定

`config.py.example` を `config.py` にコピーして編集：

```python
# Bibi連携を使う場合
bibi_dir = "/Library/WebServer/Documents/bibi-bookshelf/epub"
app_name = "epub"  # 再起動するアプリ名

```

再起動をするのはデータの再読み込みをさせるため、ここは Epub リーダの挙動に依存する。

設定可能な項目：

| 変数 | 説明 | デフォルト |
|------|------|------------|
| `css_path` | CSS ファイルのパス | スクリプトと同じディレクトリの `epub.css` |
| `output_dir` | 出力ディレクトリ | スクリプトと同じディレクトリの `output/` |
| `temp_epub` | 一時ファイル | スクリプトと同じディレクトリの `temp.epub` |
| `bibi_dir` | Bibi 展開先（設定すると Bibi 連携有効） | `None` |
| `app_name` | 再起動するアプリ名 | `None` |

## Emacs から使う

```elisp
(defun my/epub-convert ()
  "現在のバッファ内容を EPUB 化する。"
  (interactive)
  (when (buffer-modified-p)
    (save-buffer))
  (let ((script-path (expand-file-name "~/Documents/github/convert_epub/convert_epub.py")))
    (message "Generating EPUB...")
    (shell-command-on-region 
     (point-min) (point-max) 
     script-path)
    (message "EPUB generation complete.")))

(global-set-key (kbd "C-q") #'my/epub-convert)
```

## ライセンス

MIT
