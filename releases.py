from main import Archive
import sys
import os
from pathlib import Path

if __name__ == '__main__':
    sys.stdout = open(os.devnull, 'w')
    archive = Archive()
    release_info = archive.validate()
    archive.release(release_original=False)
    release_text = '## 书籍发布信息\n\n'
    for index, novel in enumerate(release_info.novels):
        release_text += f'{index + 1}. {novel.chinese_title}({novel.title}) 翻译进度{novel.translated_chapter}/{novel.total_chapter}\n\n'
    release_text += f'### **Translated by Summerkirakira**'
    sys.stdout = sys.__stdout__
    current_path = Path.cwd()
    release_path = current_path / 'releases'
    for file in release_path.glob('*.epub'):
        file.rename(release_path / "test1.epub")
    print(release_text)
