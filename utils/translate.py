from .converter import BasicChapterConverter
from pathlib import Path
from bs4 import BeautifulSoup
from novel_translator.translator import Translator
from typing import Optional


md_converter = BasicChapterConverter()
translator = None


def extract_text_from_markdown(file: Path) -> str:
    html, chapter_meta = md_converter.convert_from_path(file)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()


message_limit = 3000


def split_message(message: str) -> list[str]:
    message_list = []
    offset = 0
    current_message = ''

    for char in message:
        current_message += char
        offset += 1
        if offset >= message_limit and char == '\n':
            message_list.append(current_message)
            current_message = ''
            offset = 0
    if current_message:
        message_list.append(current_message)
    return message_list


async def translate_md(file: Path, cache_path: Optional[Path]) -> str:
    global translator
    if not translator:
        translator = Translator(cache_path, is_advanced=True)
    message = extract_text_from_markdown(file)
    message_list = split_message(message)
    translated_list = []
    for message in message_list:
        translated_list.append(await translator.translate(message))
    return "".join(translated_list)