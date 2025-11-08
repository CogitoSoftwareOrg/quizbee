from ..domain import (
    DocumentParserApp,
    DocumentParserProvider,
    ParsedDocument,
    DocumentParseCmd,
)


class DocumentParserAppImpl(DocumentParserApp):
    def __init__(self, parser_provider: DocumentParserProvider):
        self._parser_provider = parser_provider

    def parse(self, cmd: DocumentParseCmd) -> ParsedDocument:
        parser = self._parser_provider.get(cmd.file_name)
        return parser.parse(file_bytes=cmd.file_bytes, file_name=cmd.file_name)
