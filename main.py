from utils import TranslationAnalyzer, NovelPacker, ReleaseInfo
from pathlib import Path


class Archive:
    def __init__(self, archive_path: Path = Path('.')):
        self.archive_path = archive_path
        self.translation_analyzer = TranslationAnalyzer(archive_path)

    def validate(self) -> ReleaseInfo:
        return self.translation_analyzer.validate_chapters()

    def release(self, release_original: bool = False):
        if release_original:
            novel_packer = NovelPacker(self.archive_path / 'Original Novels', self.archive_path / 'Output')
            novel_packer.pack()
        novel_packer = NovelPacker(self.archive_path / 'Translated Novels', self.archive_path / 'Output')
        novel_packer.pack()


if __name__ == '__main__':
    archive = Archive()
    archive.validate()
    archive.release(release_original=True)
