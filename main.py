from utils import TranslationAnalyzer, NovelPacker
from pathlib import Path


class Archive:
    def __init__(self, archive_path: Path = Path.cwd()):
        self.archive_path = archive_path
        self.translation_analyzer = TranslationAnalyzer(archive_path)

    def validate(self) -> 'Archive':
        self.translation_analyzer.validate_chapters()
        return self

    def release(self, release_original: bool = False):
        if release_original:
            novel_packer = NovelPacker(self.archive_path / 'Original Novels', self.archive_path / 'Output')
            novel_packer.pack()
        novel_packer = NovelPacker(self.archive_path / 'Translated Novels', self.archive_path / 'Output')
        novel_packer.pack()


if __name__ == '__main__':
    Archive().validate().release(release_original=True)
