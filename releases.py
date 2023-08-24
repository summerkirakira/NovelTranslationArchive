from main import Archive
import time
import os
import sys

if __name__ == '__main__':
    sys.stdout = open(os.devnull, 'w')
    archive = Archive()
    release_info = archive.validate()
    archive.release(release_original=False)
    release_text = 'RELEASE_TEXT=# 书籍发布信息\n\n'
    for index, novel in enumerate(release_info.novels):
        release_text += f'## {index + 1}. {novel.chinese_title}({novel.title}) 翻译进度{novel.translated_chapter}/{novel.total_chapter}\n\n'
    release_text += '## **Translated by Summerkirakira**'
    release_text += f'TAG={time.time()}'
    sys.stdout = sys.__stdout__
    print(release_text)
