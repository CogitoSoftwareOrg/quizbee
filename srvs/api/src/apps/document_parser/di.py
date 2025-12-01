from langfuse import Langfuse

from .domain import DocumentParserProvider

from .adapters.out.concrete_parsers.pdf_parser import FitzPDFParser
from .adapters.out.concrete_parsers.docx_parser import DocxDocumentParser
from .adapters.out.concrete_parsers.pptx_parser import PptxDocumentParser
from .adapters.out.parser_factory import ParserProviderV1
from .app.usecases import DocumentParserAppImpl
from src.lib.settings import settings


def init_document_parser_deps(
    lf: Langfuse,
) -> DocumentParserProvider:
    parsers = {
        "pdf": FitzPDFParser(),
        "docx": DocxDocumentParser(),
        "pptx": PptxDocumentParser(),
    }
    return ParserProviderV1(parsers=parsers)


def init_document_parser_app(parser_provider: DocumentParserProvider):
    return DocumentParserAppImpl(parser_provider=parser_provider)
