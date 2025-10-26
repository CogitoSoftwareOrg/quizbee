from typing import Annotated
from fastapi import Depends, Request, FastAPI

from src.lib.clients.pb import AdminPB

from .domain.ports import MaterialRepository, PdfParser, Tokenizer
from .adapters.out.pb_repository import PBMaterialRepository
from .adapters.out.fitz_pdf_parser import FitzPDFParser
from .adapters.out.tiktoken_tokenizer import TiktokenTokenizer
from .app.usecases import MaterialSearchApp


# TOKENIZER
def set_tokenizer(app: FastAPI):
    app.state.tokenizer = TiktokenTokenizer()


def get_tokenizer(request: Request) -> Tokenizer:
    return request.app.state.tokenizer


# PDF PARSER
def set_pdf_parser(app: FastAPI):
    app.state.pdf_parser = FitzPDFParser()


def get_pdf_parser(request: Request) -> PdfParser:
    return request.app.state.pdf_parser


PdfParserDep = Annotated[PdfParser, Depends(get_pdf_parser)]


# REPOSITORY
def set_material_repository(app: FastAPI, admin_pb: AdminPB):
    app.state.material_repository = PBMaterialRepository(admin_pb)


def get_material_repository(request: Request) -> MaterialRepository:
    return request.app.state.material_repository


MaterialRepositoryDep = Annotated[MaterialRepository, Depends(get_material_repository)]


# APP
def set_material_search_app(
    app: FastAPI, material_repository: MaterialRepositoryDep, pdf_parser: PdfParserDep
):
    app.state.material_search_app = MaterialSearchApp(material_repository, pdf_parser)


def get_material_search_app(request: Request) -> MaterialSearchApp:
    return request.app.state.material_search_app


MaterialSearchAppDep = Annotated[MaterialSearchApp, Depends(get_material_search_app)]
