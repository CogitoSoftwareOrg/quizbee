from .domain import DocumentParserProvider

from .adapters.out.concrete_parsers.pdf_parser import FitzPDFParser
from .adapters.out.concrete_parsers.docx_parser import DocxDocumentParser
from .adapters.out.concrete_parsers.pptx_parser import PptxDocumentParser
from .adapters.out.parser_factory import ParserProviderV1
from .app.usecases import DocumentParserAppImpl


def init_document_parser_deps() -> DocumentParserProvider:
    parsers = {
        "pdf": FitzPDFParser(),
        "docx": DocxDocumentParser(),
        "pptx": PptxDocumentParser(),
    }
    return ParserProviderV1(parsers=parsers)


def init_document_parser_app(parser_provider: DocumentParserProvider):
    return DocumentParserAppImpl(parser_provider=parser_provider)
