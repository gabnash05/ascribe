import logging

from app.workers.exceptions import NonRetryableError

logger = logging.getLogger(__name__)


def _extract_pdf(file_path: str) -> str:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        TesseractCliOcrOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    # ── Attempt 1: Native text extraction (fast, no OCR) ──────────────────
    # Most digitally-created PDFs have embedded text — extract it directly.
    # This is the fastest and most accurate path.
    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(file_path)
        text = result.document.export_to_markdown(traverse_pictures=False)

        # If we got meaningful text, we're done
        if text and len(text.strip()) > 100:
            logger.info("PDF extracted via native text (no OCR needed)")
            return text

        logger.info("Native extraction yielded little text — falling back to OCR")
    except Exception as exc:
        logger.warning("Native PDF extraction failed (%s) — trying OCR", exc)

    # ── Attempt 2: OCR fallback (scanned/image-based PDFs) ────────────────
    # Used when the PDF is a scanned document with no embedded text.
    # Uses Tesseract which is reliable and doesn't require external downloads.
    try:
        ocr_options = TesseractCliOcrOptions(force_full_page_ocr=False)

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = ocr_options
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(file_path)
        text = result.document.export_to_markdown(traverse_pictures=False)

        if text and text.strip():
            logger.info("PDF extracted via Tesseract OCR")
            return text

        raise NonRetryableError(f"OCR produced no text for PDF at {file_path}")
    except NonRetryableError:
        raise
    except Exception as exc:
        raise NonRetryableError(
            f"PDF extraction failed after all attempts: {exc}"
        ) from exc


def _extract_docx(file_path: str) -> str:
    from docling.document_converter import DocumentConverter

    try:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        text = result.document.export_to_markdown(traverse_pictures=False)
        if text and text.strip():
            return text
        raise NonRetryableError(f"DOCX extraction yielded no text: {file_path}")
    except NonRetryableError:
        raise
    except Exception as exc:
        raise NonRetryableError(f"DOCX extraction failed: {exc}") from exc


def _extract_image(file_path: str) -> str:
    from docling.document_converter import DocumentConverter

    try:
        converter = DocumentConverter()
        result = converter.convert(file_path)
        text = result.document.export_to_markdown(traverse_pictures=False)
        if text and text.strip():
            return text
        raise NonRetryableError(f"Image OCR yielded no text: {file_path}")
    except NonRetryableError:
        raise
    except Exception as exc:
        raise NonRetryableError(f"Image extraction failed: {exc}") from exc
