from utils import TranslationAnalyzer
from pathlib import Path


class ArchiveValidater:
    def __init__(self, archive_path: Path = Path.cwd()):
        self.archive_path = archive_path
        self.translation_analyzer = TranslationAnalyzer(archive_path)

    def validate(self):
        self.translation_analyzer.validate_chapters()


if __name__ == '__main__':
    ArchiveValidater().validate()
