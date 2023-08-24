from pathlib import Path
from .converter import Markdowns2EpubConverter


class NovelPacker:
    def __init__(self, novel_path: Path, output_path: Path):
        self.converter = Markdowns2EpubConverter()
        self.novel_path = novel_path
        self.output_path = output_path
        if not self.output_path.exists():
            self.output_path.mkdir()

    def pack(self):
        for subdirectory in self.novel_path.glob('*'):
            if subdirectory.is_dir():
                if (subdirectory / 'book_meta.json').exists():
                    self.converter.set_md_path(subdirectory)
                    self.converter.convert().save_to_file(self.output_path / f'{subdirectory.name}.epub')
                else:
                    print(f"在{subdirectory.name}中找不到book_meta.json，跳过...")
            print(f"书籍：{subdirectory.name}生成epub完成...")
