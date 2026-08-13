import json
import os
from database.connection import DatabaseConnection
from database.schema import DatabaseSchema
from dao.agricultor_dao import AgricultorDao
from dao.recepcion_pesaje_dao import RecepcionPesajeDao
from dao.sesion_dao import SesionDao
from services.scale_service import ScaleService
from services.print_service import PrintService
from services.sync_service import SyncService
from ui.app_window import AppWindow

def cargar_config_local():
    """Carga config.json o retorna valores por defecto."""
    config = {
        "balanza_port": "COM4",
        "balanza_baudrate": 9600,
        "impresora_recibo": "POS-80",
        "impresora_etiqueta": "Xprinter"
    }
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"Error leyendo config.json al arrancar: {e}")
    return config

def main():
    # 0. Cargar configuración de hardware
    cfg = cargar_config_local()

    # 1. Inicializar BD
    db_conn = DatabaseConnection()
    schema = DatabaseSchema(db_conn)
    schema.init_db()

    # 2. Inicializar DAOs
    agricultor_dao = AgricultorDao(db_conn)
    recepcion_dao = RecepcionPesajeDao(db_conn)
    sesion_dao = SesionDao(db_conn)

    # 3. Inicializar Servicios con la configuración cargada
    scale_service = ScaleService(port=cfg["balanza_port"], baudrate=cfg["balanza_baudrate"])
    scale_service.start()
    
    print_service = PrintService()
    sync_service = SyncService(
        api_url="https://stg.tierrafertil.com.pe/api",
        token="rsTU",
        agricultor_dao=agricultor_dao,
        recepcion_dao=recepcion_dao
    )

    # 4. Iniciar Interfaz Gráfica
    app = AppWindow(
        agricultor_dao=agricultor_dao,
        recepcion_dao=recepcion_dao,
        sesion_dao=sesion_dao,
        scale_service=scale_service,
        print_service=print_service,
        sync_service=sync_service
    )

    try:
        app.mainloop()
    finally:
        scale_service.stop()

if __name__ == "__main__":
    main()