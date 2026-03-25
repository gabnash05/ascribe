from enum import Enum


class FileStatusEnum(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ValidFileTypesEnum(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    DOCX = "docx"
    TXT = "txt"
    NOTE = "note"

    @property
    def mime_type(self) -> str:
        """Get MIME type for file extension"""
        mapping = {
            "pdf": "application/pdf",
            "image": "image/*",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
            "note": "text/markdown",
        }
        return mapping[self.value]

    @property
    def allowed_extensions(self) -> list[str]:
        """Get file extensions"""
        mapping = {
            "pdf": [".pdf"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            "docx": [".docx"],
            "txt": [".txt", ".md"],
            "note": [".md", ".markdown", ".txt"],
        }
        return mapping[self.value]
