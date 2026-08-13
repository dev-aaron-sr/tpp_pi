import logging
import requests
from typing import Dict, List
from dao.agricultor_dao import AgricultorDao
from dao.recepcion_pesaje_dao import RecepcionPesajeDao

# Configuración del Logger para volcado en archivo local
logging.basicConfig(
    filename='sync_balanza.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

class SyncService:
    """Servicio encargado de la sincronización bidireccional con Laravel."""

    def __init__(self, api_url: str, token: str, agricultor_dao: AgricultorDao, recepcion_dao: RecepcionPesajeDao):
        self.api_url = api_url.rstrip('/')
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.agricultor_dao = agricultor_dao
        self.recepcion_dao = recepcion_dao

    def descargar_maestros(self) -> bool:
        """Descarga agricultores y parcelas desde Laravel y actualiza la BD local."""
        try:
            response = requests.get(f"{self.api_url}/v1/sync/maestros", headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json().get('data', {})
                self.agricultor_dao.guardar_maestros(data.get('agricultores', []))
                return True
            return False
        except Exception as e:
            print(f"Sin conexión para descargar maestros: {e}")
            return False

    # def subir_pesajes_pendientes(self) -> int:
    #     """Envía las recepciones locales no sincronizadas a Laravel."""
    #     pendientes = self.recepcion_dao.obtener_pendientes_sincronizacion()
    #     if not pendientes:
    #         return 0

    #     payload = {"recepciones": pendientes}
    #     try:
    #         response = requests.post(f"{self.api_url}/v1/sync/recepciones", json=payload, headers=self.headers, timeout=10)
    #         if response.status_code == 200:
    #             synced_uuids = response.json().get('synced_uuids', [])
    #             self.recepcion_dao.marcar_sincronizados(synced_uuids)
    #             return len(synced_uuids)
    #         return 0
    #     except Exception as e:
    #         print(f"Error durante sincronización de pesajes: {e}")
    #         return 0

    def subir_pesajes_pendientes(self) -> int:
        """Envía las recepciones locales no sincronizadas a Laravel escribiendo detalle en log."""
        pendientes = self.recepcion_dao.obtener_pendientes_sincronizacion()
        if not pendientes:
            logging.info("ℹ️ Sin pesajes pendientes por sincronizar.")
            return 0

        payload = {"recepciones": pendientes}
        logging.info(f"🚀 Iniciando envío de {len(pendientes)} pesaje(s) pendiente(s) a Laravel...")

        try:
            response = requests.post(f"{self.api_url}/v1/sync/recepciones", json=payload, headers=self.headers, timeout=10)

            if response.status_code == 200:
                synced_uuids = response.json().get('synced_uuids', [])
                
                if synced_uuids:
                    logging.info(f"✅ Sincronización Exitosa. UUIDs confirmados: {synced_uuids}")
                    self.recepcion_dao.marcar_sincronizados(synced_uuids)
                else:
                    logging.warning("⚠️ Servidor respondió HTTP 200 pero devolvió synced_uuids VACÍO. (Revisar logs de Laravel).")

                return len(synced_uuids)
            else:
                # VUELCO DETALLADO DEL ERROR QUE DEVUELVE LARAVEL
                logging.error(f"❌ RECHAZADO POR SERVIDOR (HTTP {response.status_code}): {response.text}")
                return 0

        except Exception as e:
            logging.exception(f"❌ ERROR DE RED O CONEXIÓN AL SINCRO: {e}")
            return 0