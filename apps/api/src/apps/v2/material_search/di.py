from typing import Annotated
from fastapi import Depends, Request, FastAPI

from src.lib.clients.meilisearch import MeilisearchClient
from src.lib.clients.pb import AdminPB

from .domain.ports import (
    Chunker,
    MaterialRepository,
    PdfParser,
    Tokenizer,
    ImageTokenizer,
    Indexer,
)
from .adapters.out.simple_chunker import SimpleChunker
from .adapters.out.pb_repository import PBMaterialRepository
from .adapters.out.fitz_pdf_parser import FitzPDFParser
from .adapters.out.tiktoken_tokenizer import TiktokenTokenizer
from .adapters.out.openai_image_tokens import OpenAIImageTokenizer
from .adapters.out.meili_indexer import MeiliIndexer

from .app.usecases import MaterialSearchApp


# TOKENIZER
def set_tokenizer(app: FastAPI):
    app.state.tokenizer = TiktokenTokenizer()


def get_tokenizer(request: Request) -> Tokenizer:
    return request.app.state.tokenizer


TokenizerDep = Annotated[Tokenizer, Depends(get_tokenizer)]


def set_image_tokenizer(app: FastAPI):
    app.state.image_tokenizer = OpenAIImageTokenizer()


def get_image_tokenizer(request: Request) -> ImageTokenizer:
    return request.app.state.image_tokenizer


ImageTokenizerDep = Annotated[ImageTokenizer, Depends(get_image_tokenizer)]


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


# CHUNKER
def set_chunker(app: FastAPI, tokenizer: Tokenizer):
    app.state.chunker = SimpleChunker(tokenizer)


def get_chunker(request: Request) -> Chunker:
    return request.app.state.chunker


ChunkerDep = Annotated[Chunker, Depends(get_chunker)]


# INDEXER
async def aset_indexer(app: FastAPI, chunker: Chunker, meili: MeilisearchClient):
    app.state.indexer = await MeiliIndexer.ainit(chunker, meili)


def get_indexer(request: Request) -> Indexer:
    return request.app.state.indexer


IndexerDep = Annotated[Indexer, Depends(get_indexer)]


# APP
def set_material_search_app(
    app: FastAPI,
    material_repository: MaterialRepository,
    pdf_parser: PdfParser,
    tokenizer: Tokenizer,
    image_tokenizer: ImageTokenizer,
    indexer: Indexer,
):
    app.state.material_search_app = MaterialSearchApp(
        material_repository, pdf_parser, tokenizer, image_tokenizer, indexer
    )


def get_material_search_app(request: Request) -> MaterialSearchApp:
    return request.app.state.material_search_app


MaterialSearchAppDep = Annotated[MaterialSearchApp, Depends(get_material_search_app)]
