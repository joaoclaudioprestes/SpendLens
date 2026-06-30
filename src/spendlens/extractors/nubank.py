from .generic import GenericCSVExtractor


class NubankExtractor(GenericCSVExtractor):
    """Extractor for Nubank CSV files (Data, Descrição, Valor)."""

    def __init__(self):
        super().__init__(
            accepted_fields=["Data", "Descrição", "Valor"],
            name="Nubank",
        )
