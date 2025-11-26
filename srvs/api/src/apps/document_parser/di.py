from langfuse import Langfuse

from .domain import DocumentParserProvider

from .adapters.out.concrete_parsers.pdf_parser import FitzPDFParser
from .adapters.out.concrete_parsers.docx_parser import DocxDocumentParser
from .adapters.out.concrete_parsers.pptx_parser import PptxDocumentParser
from .adapters.out.parser_factory import ParserProviderV1
from .adapters.out.image_describer import GeminiImageDescriber
from .app.usecases import DocumentParserAppImpl
from src.lib.settings import settings


def init_image_describer(lf: Langfuse) -> GeminiImageDescriber:
    return GeminiImageDescriber(
        lf=lf,
        model=settings.gemini_image_model,
    )


def init_document_parser_deps(
    lf: Langfuse,
    image_describer: GeminiImageDescriber | None = None,
) -> DocumentParserProvider:
    describer = image_describer or init_image_describer(lf)
    parsers = {
        "pdf": FitzPDFParser(image_describer=describer),
        "docx": DocxDocumentParser(),
        "pptx": PptxDocumentParser(image_describer=describer),
    }
    return ParserProviderV1(parsers=parsers)


def init_document_parser_app(parser_provider: DocumentParserProvider):
    return DocumentParserAppImpl(parser_provider=parser_provider)
