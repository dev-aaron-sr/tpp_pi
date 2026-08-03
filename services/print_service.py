from typing import Dict, List

class PrintService:
    """Servicio de impresión para Epson LX350 (Recibos) y TSC TE200 (Etiquetas)."""

    def imprimir_recibo_epson(self, recepcion: Dict, detalles: List[Dict]) -> bool:
        """Genera e imprime el ticket matriz de puntos en la Epson LX350."""
        # TODO: Implementar envío de comandos ESC/P o texto raw a la impresora
        return True

    def imprimir_etiqueta_tsc(self, codigo_lote_origen: str, numero_saco: int, agricultor_nombre: str) -> bool:
        """Envía comandos TSPL a la impresora térmica TSC TE200 por saco."""
        # TODO: Implementar envío de comandos TSPL por puerto USB/Serie
        return True