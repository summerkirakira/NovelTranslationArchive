from typing import Optional
from markdown2 import Markdown
from .converter_models import ConverterConfig, ChapterMeta, SectionDict, BookMeta
import requests
from lxml import etree
import xml.etree.ElementTree as ET
import abc
from ebooklib import epub
import pathlib
import json
from bs4 import BeautifulSoup


class BasicChapterConverter:
    """
    Basic Markdown converter
    """

    name: str = "Basic Chapter Converter"

    def __str__(self):
        return f"[{self.name}]"

    def __init__(self, config: ConverterConfig = ConverterConfig()):
        self.config = config
        self.markdown_converter: Markdown = Markdown(extras=['metadata'])
        pass

    def _convert_md_to_html(self, md_str: str) -> (str, ChapterMeta):
        html = self.markdown_converter.convert(md_str)
        if html.metadata is None:
            html.metadata = {}
        return html, ChapterMeta(**html.metadata)

    def convert_from_path(self, path: pathlib.Path) -> (str, ChapterMeta):
        with path.open('r', encoding='utf-8') as f:
            md_content: str = f.read()
        return self._convert_md_to_html(md_content)


class EPUBConverter:
    """
    Basic Chapter Converter
    """

    name: str = "EPUB Converter"

    def __str__(self):
        return f"[{self.name}]"

    def __init__(self, config: ConverterConfig, proxy: Optional[dict] = None):
        self.config = config
        self.epub_book = epub.EpubBook()
        self.section_dict: dict[str, SectionDict] = {
            'default': SectionDict(section_name='default', section_order=0, section_content={})
        }
        self.total_chapter_count = 1
        self.proxy = proxy

    def load_meta_from_file(self, book_meta: BookMeta, file_path: pathlib.Path) -> 'EPUBConverter':
        if book_meta.title is not None:
            self.set_title(book_meta.title)
        if book_meta.author is not None:
            for author in book_meta.author:
                self.add_author(author)
        if book_meta.description is not None:
            self.set_description(book_meta.description)
        if book_meta.language is not None:
            self.set_language(book_meta.language)
        if book_meta.cover is not None:
            if book_meta.cover.startswith('http'):
                try:
                    if self.proxy is not None:
                        self.set_cover("cover", requests.get(book_meta.cover, headers=self.config.download_headers, proxies=self.proxy).content)
                    else:
                        self.set_cover("cover", requests.get(book_meta.cover, headers=self.config.download_headers).content)
                except Exception as e:
                    print(e)
            else:
                cover_path = file_path.parent / book_meta.cover
                if cover_path.exists():
                    self.set_cover(file_path.name, cover_path.read_bytes())
                else:
                    print(f'Cover {book_meta.cover} not found')
        if book_meta.publisher is not None:
            self.set_publisher(book_meta.publisher)
        if book_meta.identifier is not None:
            self.set_identifier(book_meta.identifier)
        if book_meta.meta is not None:
            for key, value in book_meta.meta.items():
                self.add_metadata(key, value)
        return self

    def set_style(self, style: str) -> 'EPUBConverter':
        self.config.style = style
        return self

    def set_title(self, title: str) -> 'EPUBConverter':
        self.epub_book.set_title(title)
        return self

    def set_publisher(self, publisher: str) -> 'EPUBConverter':
        self.epub_book.add_metadata('DC', 'publisher', publisher)
        return self

    def set_identifier(self, identifier: str) -> 'EPUBConverter':
        self.epub_book.set_identifier(identifier)
        return self

    def add_author(self, author: str) -> 'EPUBConverter':
        self.epub_book.add_author(author)
        return self

    def set_language(self, language: str) -> 'EPUBConverter':
        self.epub_book.set_language(language)
        return self

    def set_cover(self, file_name, content, create_page=True) -> 'EPUBConverter':
        self.epub_book.set_cover(file_name=file_name, content=content, create_page=create_page)
        return self

    def set_description(self, description: str) -> 'EPUBConverter':
        self.epub_book.add_metadata('DC', 'description', description)
        return self

    def add_metadata(self, name: str, content: str) -> 'EPUBConverter':
        self.epub_book.add_metadata(None, 'meta', '', {'name': name, 'content': content})
        return self

    def add_section(self, section_name: str, section_order: Optional[int]) -> 'EPUBConverter':
        if section_name == '':
            section_name = 'default'
        if section_name not in self.section_dict:
            if section_order is None:
                self.section_dict[section_name] = SectionDict(section_name=section_name, section_order=len(self.section_dict), section_content={})
            else:
                self.section_dict[section_name] = SectionDict(section_name=section_name, section_order=section_order, section_content={})
        return self

    def add_chapter(self, section_name: str, chapter_content: str, chapter_meta: ChapterMeta, file_path: pathlib.Path) -> 'EPUBConverter':
        self.total_chapter_count += 1
        if section_name == '':
            section_name = 'default'
        if section_name not in self.section_dict:
            self.add_section(section_name, chapter_meta.section_order)
        new_chapter = epub.EpubHtml(title=chapter_meta.chapter_name, file_name=f'{chapter_meta.chapter_name}.xhtml', lang=self.config.lang, )
        chapter_content = self.process_html(chapter_content, file_path)
        new_chapter.set_content(chapter_content)
        self.section_dict[section_name].section_content[chapter_meta.chapter_order] = new_chapter
        return self

    @abc.abstractmethod
    def convert(self) -> epub.EpubBook:
        pass

    def process_html(self, html: str, file_path: pathlib.Path) -> str:
        html = "<html><body>" + html + "</body></html>"
        try:
            soup = BeautifulSoup(html, 'html.parser')
            root = ET.fromstring(str(soup.prettify()))
            return ET.tostring(self.download_image(root, file_path), encoding='utf-8')
        except Exception as e:
            print(e)
            return html

    def download_image(self, root: etree.Element, file_path: pathlib.Path) -> etree.Element:
        for img in root.findall('.//img'):
            img_url = img.get('src')
            if img_url is not None:
                img_url = img_url.strip()
                if img_url.startswith('http'):
                    if self.proxy is not None:
                        img_data = requests.get(img_url, headers=self.config.download_headers, proxies=self.proxy).content
                    else:
                        img_data = requests.get(img_url, headers=self.config.download_headers).content
                    img_name = img_url.split('/')[-1]
                    self.epub_book.add_item(epub.EpubItem(file_name=f"images/{img_name}", content=img_data, media_type='image/jpeg'))
                    img.set('src', f"images/{img_name}")
                else:
                    img_path = file_path / pathlib.Path(img.get('src'))
                    if img_path.exists():
                        img_data = img_path.read_bytes()
                        img_name = img_path.name
                        self.epub_book.add_item(epub.EpubItem(file_name=f"images/{img_name}", content=img_data, media_type='image/jpeg'))
                        img.set('src', f"images/{img_name}")
                    else:
                        raise FileNotFoundError(f"Image not found: {img_path}")
        return root


class Markdowns2EpubConverter(EPUBConverter):
    """
    Markdown to EPUB converter
    """

    def __init__(self, config: ConverterConfig = ConverterConfig(), proxy: Optional[dict] = None):
        super(Markdowns2EpubConverter, self).__init__(config, proxy)
        self.chapter_converter = BasicChapterConverter(self.config)
        self.md_path: Optional[pathlib.Path] = None

    def convert(self) -> 'Markdowns2EpubConverter':
        """
        Convert markdown to epub
        :return:
        """
        if self.md_path is None:
            raise ValueError("Path not set")
        for chapter_path in self.md_path.iterdir():
            if chapter_path.is_dir():
                continue
            if not chapter_path.suffix == '.md':
                continue
            chapter_content, chapter_meta = self.chapter_converter.convert_from_path(chapter_path)
            if chapter_meta.chapter_name is None:
                if chapter_meta.show_chapter_order:
                    chapter_meta.chapter_name = f"第{self.total_chapter_count}章 {chapter_path.stem}"
                else:
                    chapter_meta.chapter_name = chapter_path.stem
            if chapter_meta.status == "translating":
                chapter_meta.chapter_name = f"[翻译中]{chapter_meta.chapter_name}"
            if chapter_meta.chapter_order is None:
                chapter_meta.chapter_order = self.total_chapter_count
            if chapter_meta.section_order is None:
                chapter_meta.section_order = len(self.section_dict)
            if chapter_meta.section_name:
                self.add_chapter(chapter_meta.section_name, chapter_content, chapter_meta, chapter_path.parent)
            else:
                self.add_chapter("", chapter_content, chapter_meta, chapter_path.parent)

        section_list = [_ for key, _ in self.section_dict.items()]
        section_list.sort(key=lambda x: x.section_order)
        if len(section_list) == 1:
            chapter_list = [(key, value) for key, value in section_list[0].section_content.items()]
            chapter_list.sort(key=lambda x: x[0])
            chapters = [value for _, value in chapter_list]
            for chapter in chapters:
                self.epub_book.add_item(chapter)
            self.epub_book.toc = [(epub.Section('正文'), chapters)]
            self.epub_book.spine = chapters
        else:
            section_list.sort(key=lambda x: x.section_order)
            for section in section_list:
                if section.section_name == 'default':
                    continue
                chapter_list = [(key, value) for key, value in section.section_content.items()]
                chapter_list.sort(key=lambda x: x[0])
                chapters = [value for _, value in chapter_list]
                for chapter in chapters:
                    self.epub_book.add_item(chapter)
                self.epub_book.toc.append((epub.Section(section.section_name), chapters))
                self.epub_book.spine.extend(chapters)
        self.epub_book.add_item(epub.EpubNcx())
        self.epub_book.add_item(epub.EpubNav())
        return self

    def set_md_path(self, path: pathlib.Path) -> 'EPUBConverter':
        """
        Set markdown path
        :param path:
        :return:
        """
        if not path.exists():
            raise ValueError("Path not exists")
        if not path.is_dir():
            raise ValueError("Path is not a directory")
        self.md_path = path
        if (path / 'book_meta.json').exists():
            with (path / 'book_meta.json').open('r', encoding="utf-8") as f:
                book_meta = json.load(f)
            self.load_meta_from_file(BookMeta(**book_meta), path / 'book_meta.json')
        return self

    def _create_book(self) -> epub.EpubBook:
        return self.epub_book

    def save_to_file(self, file_path: pathlib.Path) -> 'EPUBConverter':
        """
        Save epub to file
        :param file_path:
        :return:
        """
        epub.write_epub(file_path.absolute(), self.epub_book, {"epub3_pages": False})
        return self

