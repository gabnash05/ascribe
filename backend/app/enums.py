from enum import Enum


class FileStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class ValidFileTypesEnum(str, Enum):
    PDF = "PDF"
    IMAGE = "IMAGE"
    DOCX = "DOCX"
    TXT = "TXT"
    NOTE = "NOTE"

    @property
    def mime_type(self) -> str:
        mapping = {
            "PDF": "application/pdf",
            "IMAGE": "image/*",
            "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "TXT": "text/plain",
            "NOTE": "text/markdown",
        }
        return mapping[self.value]

    @property
    def allowed_extensions(self) -> list[str]:
        mapping = {
            "PDF": [".pdf"],
            "IMAGE": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            "DOCX": [".docx"],
            "TXT": [".txt", ".md"],
            "NOTE": [".md", ".markdown", ".txt"],
        }
        return mapping[self.value]
