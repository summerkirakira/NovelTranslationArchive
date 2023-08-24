from .converter_models import BookMeta, ChapterMeta, Chapter, Paragraph
from .converter import BasicChapterConverter
from .execeptions import UserCancelledException
from pathlib import Path
from typing import Optional
import json


class TranslationAnalyzer:
    def __init__(self, path: Path):
        self.path = path
        self.original_novel_path: Path = self.path / 'Original Novels'
        self.translated_novel_path: Path = self.path / 'Translated Novels'
        if not self.original_novel_path.exists():
            self.original_novel_path.mkdir()
        if not self.translated_novel_path.exists():
            self.translated_novel_path.mkdir()
        self.books: list[BookMeta] = self._validate_novels()
        self.converter = BasicChapterConverter()

    @classmethod
    def paragraph2md(cls, paragraph: Paragraph) -> str:
        if paragraph.type == Paragraph.ParagraphType.Image:
            return f'![{paragraph.content}]({paragraph.content})\n'
        if paragraph.type == Paragraph.ParagraphType.Title:
            return f'# {paragraph.content}\n'
        if paragraph.type == Paragraph.ParagraphType.HTML:
            f'{paragraph.content}\n'
        return f'{paragraph.content}\n'

    @classmethod
    def chapter2md(cls, chapter: Chapter) -> str:
        md = '---\n'
        for k, v in chapter.metadata.dict().items():
            if k == 'meta' and v is not None:
                for kk, vv in v.items():
                    md += f'{kk}: {vv}\n'
                continue
            if k == 'chapter_type':
                continue
            md += f'{k}: {v}\n'
        md += '---\n\n'
        for paragraph in chapter.paragraphs:
            md += cls.paragraph2md(paragraph)
        return md

    def _validate_novels(self) -> list[BookMeta]:
        novels = []
        for subdirectory in self.original_novel_path.glob('*'):
            if subdirectory.is_dir():
                book_meta_path = subdirectory / 'book_meta.json'
                if book_meta_path.exists():
                    with open(book_meta_path, 'r', encoding='utf-8') as f:
                        book_meta = BookMeta(**json.load(f))
                        book_meta.path = str(subdirectory)
                        novels.append(book_meta)
                else:
                    print(f"在{subdirectory}中找不到book_meta.json，跳过...")
        return novels

    def generate_empty_translated_chapters(self, path: Path, chapter_metas: list[ChapterMeta]):
        for chapter_meta in chapter_metas:
            chapter_prefix = str(chapter_meta.chapter_order).zfill(2)
            chapter_path = path / f'{chapter_prefix}-{chapter_meta.chapter_name}.md'
            if chapter_path.exists():
                print(f'{chapter_path}已存在，跳过...')
                continue
            chapter = Chapter(metadata=chapter_meta)
            chapter.metadata.status = 'translating'
            chapter.paragraphs.append(Paragraph(type=Paragraph.ParagraphType.Title, content=chapter_meta.chapter_name))
            chapter.paragraphs.append(Paragraph(type=Paragraph.ParagraphType.Text, content='待翻译...'))
            chapter_path.write_text(self.chapter2md(chapter), encoding='utf-8')
            print(f'已创建{chapter_path}')

    def _validate_chapters(self):
        for novel in self.books:
            original_novel_root_path = Path(novel.path)
            translated_novel_root_path = self.translated_novel_path / novel.chinese_title
            if not translated_novel_root_path.exists():
                user_input = input(f'在{self.translated_novel_path}中找不到{novel.chinese_title}，是否创建？(y/n):')
                if user_input != 'y':
                    raise UserCancelledException()
                translated_novel_root_path.mkdir(parents=True)
            book_meta_path = translated_novel_root_path / 'book_meta.json'

            if not book_meta_path.exists():
                user_input = input(f'在{translated_novel_root_path}中找不到book_meta.json，是否创建？(y/n):')
                if user_input != 'y':
                    raise UserCancelledException()
                book_meta_path.write_text(novel.model_dump_json(indent=4), encoding='utf-8')
                print(f'已创建{book_meta_path}')

            original_chapter_metas: list[ChapterMeta] = []
            translated_chapter_metas: list[ChapterMeta] = []
            for original_chapters in original_novel_root_path.glob('*.md'):
                if original_chapters.is_file():
                    original_chapter_metas.append(self.converter.convert_from_path(original_chapters)[1])
            for translated_chapters in translated_novel_root_path.glob('*.md'):
                if translated_chapters.is_file():
                    translated_chapter_metas.append(self.converter.convert_from_path(translated_chapters)[1])
            chapter_matched_list: list[ChapterMeta] = []
            for original_chapter_meta in original_chapter_metas:
                for translated_chapter_meta in translated_chapter_metas:
                    if translated_chapter_meta.chapter_order == original_chapter_meta.chapter_order:
                        chapter_matched_list.append(original_chapter_meta)
                        break
            chapter_not_matched_list: list[ChapterMeta] = []
            for original_chapter_meta in original_chapter_metas:
                if original_chapter_meta not in chapter_matched_list:
                    chapter_not_matched_list.append(original_chapter_meta)
            if len(chapter_not_matched_list) > 0:
                error_message = f'在{novel.chinese_title}中，以下章节没有找到对应的翻译：\n'
                error_message += '\n'.join([f'{str(chapter.chapter_order).zfill(2)}-{chapter.chapter_name}' for chapter in chapter_not_matched_list])
                error_message += '\n'
                error_message += '是否自动补全空章节？(y/n):'
                if input(error_message) != 'y':
                    raise UserCancelledException
                self.generate_empty_translated_chapters(translated_novel_root_path, chapter_not_matched_list)
            print(f'{novel.chinese_title}章节校验完毕')

    def validate_chapters(self):
        try:
            self._validate_chapters()
        except UserCancelledException:
            print('用户取消操作')
            return
        print('书籍校验完毕')


