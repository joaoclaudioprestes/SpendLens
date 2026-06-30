from .generic import GenericCSVExtractor


class ItauExtractor(GenericCSVExtractor):
    """Extractor for Itau CSV files (data_lancamento, historico, valor, tipo)."""

    def __init__(self):
        super().__init__(
            accepted_fields=["data_lancamento", "historico", "valor", "tipo"],
            name="Itau",
        )
