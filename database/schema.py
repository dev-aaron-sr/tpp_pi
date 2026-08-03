from database import connection
from database.connection import DatabaseConnection

class DatabaseSchema:
    """Inicializa la estructura de tablas locales en SQLite."""
    
    def __init__(self, db_conn: DatabaseConnection):
        self.db_conn = db_conn

    def init_db(self) -> None:
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        # Tabla Maestros (Sincronizada desde Laravel para bajar los agricultores y sus detalles)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agricultores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_padron TEXT UNIQUE NOT NULL,
                nombres TEXT NOT NULL,
                apellidos TEXT,
                activo INTEGER DEFAULT 1
            );
        """)

        # 1. Tabla parcelas (se agrega codigo_interno)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parcelas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agricultor_id INTEGER NOT NULL,
                codigo_interno TEXT,               -- P01, P02...
                codigo_parcela TEXT UNIQUE NOT NULL,
                nombre_parcela TEXT NOT NULL,
                sector TEXT,
                FOREIGN KEY (agricultor_id) REFERENCES agricultores(id)
            );
        """)


        # Tabla de Sesiones de Pesaje (Jornadas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones_pesaje (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_sesion TEXT UNIQUE NOT NULL,
                fecha_apertura TEXT NOT NULL,
                fecha_cierre TEXT,
                estado TEXT DEFAULT 'ABIERTA'
            );
        """)

        # Cabecera de Recibo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recepciones_pesaje (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                lote_acopio_id INTEGER,
                codigo_lote_origen TEXT NOT NULL,
                codigo_ticket TEXT NOT NULL,
                codigo_padron TEXT NOT NULL,
                codigo_parcela TEXT NOT NULL,
                producto TEXT DEFAULT 'MARACUYA',
                destino TEXT NOT NULL,
                total_sacos INTEGER NOT NULL,
                peso_bruto_total REAL NOT NULL,
                tara_total REAL NOT NULL,
                peso_neto_total REAL NOT NULL,
                fecha_pesaje TEXT NOT NULL,
                observaciones TEXT,
                sincronizado INTEGER DEFAULT 0,
                sincronizado_at TEXT
            );
        """)

        # Detalles de Bajadas (Ahora incluye columna destino individual)
        
        # 2. Tabla pesaje_detalles (se agregan campos de trazabilidad y peso contable)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pesaje_detalles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                recepcion_pesaje_uuid TEXT NOT NULL,
                codigo_trazabilidad TEXT NOT NULL,  -- A1260803-01-M-1-P01-1
                destino TEXT NOT NULL,              -- MERCADO / FABRICA
                numero_sacos INTEGER NOT NULL,
                peso_bruto_real REAL NOT NULL,      -- Ej: 108.76
                peso_contable REAL NOT NULL,        -- Ej: 108.00 (o 109.00 si >= 0.90)
                tara REAL DEFAULT 0.0,
                peso_neto REAL NOT NULL,
                orden INTEGER NOT NULL,
                FOREIGN KEY (recepcion_pesaje_uuid) REFERENCES recepciones_pesaje(uuid)
            );
        """)
        conn.commit()
        conn.close()