from database.connection import DatabaseConnection
from database.schema import DatabaseSchema
from dao.agricultor_dao import AgricultorDao
from dao.recepcion_pesaje_dao import RecepcionPesajeDao
from dao.sesion_dao import SesionDao
from services.scale_service import ScaleService
from services.print_service import PrintService
from services.sync_service import SyncService
from ui.app_window import AppWindow

def main():
    # 1. Inicializar Base de Datos
    db_conn = DatabaseConnection()
    schema = DatabaseSchema(db_conn)
    schema.init_db()

    # 2. Inicializar DAOs
    agricultor_dao = AgricultorDao(db_conn)
    recepcion_dao = RecepcionPesajeDao(db_conn)
    sesion_dao = SesionDao(db_conn)  # <--- 2. NUEVO DAO

    # 3. Inicializar Servicios
    scale_service = ScaleService(port="COM4", baudrate=9600)
    scale_service.start()
    print_service = PrintService()
    sync_service = SyncService(
        api_url="http://localhost:8000/api",
        token="rsTU",
        agricultor_dao=agricultor_dao,
        recepcion_dao=recepcion_dao
    )

    # 4. Iniciar Interfaz Gráfica CustomTkinter
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
        # 4. Apagado limpio al cerrar la ventana
        scale_service.stop()

    #app.mainloop()

if __name__ == "__main__":
    main()