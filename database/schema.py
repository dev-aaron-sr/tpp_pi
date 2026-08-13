from database.connection import DatabaseConnection

class DatabaseSchema:
    """Inicializa la estructura de tablas locales en SQLite."""
    
    def __init__(self, db_conn: DatabaseConnection):
        self.db_conn = db_conn

    def init_db(self) -> None:
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        # Tabla Agricultores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agricultores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_padron TEXT UNIQUE NOT NULL,
                nombres TEXT NOT NULL,
                apellidos TEXT,
                activo INTEGER DEFAULT 1
            );
        """)

        # Tabla Parcelas (codigo_interno Obligatorio | codigo_parcela Opcional)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parcelas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agricultor_id INTEGER NOT NULL,
                codigo_interno TEXT NOT NULL,
                codigo_parcela TEXT,
                nombre_parcela TEXT NOT NULL,
                sector TEXT,
                FOREIGN KEY (agricultor_id) REFERENCES agricultores(id),
                UNIQUE(agricultor_id, codigo_interno)
            );
        """)

        # Tabla Sesiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones_pesaje (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_sesion TEXT UNIQUE NOT NULL,
                fecha_apertura TEXT NOT NULL,
                fecha_cierre TEXT,
                estado TEXT DEFAULT 'ABIERTA'
            );
        """)

        # Cabecera de Recibo (Sin columna 'destino')
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
                total_sacos INTEGER NOT NULL,
                peso_bruto_total REAL NOT NULL,
                tara_total REAL NOT NULL,
                peso_neto_total REAL NOT NULL,
                fecha_pesaje TEXT NOT NULL,
                observaciones TEXT,
                sincronizado INTEGER DEFAULT 0,
                sincronizado_at TEXT,
                estado TEXT DEFAULT 'EN_PROCESO'  -- 'EN_PROCESO' o 'COMPLETADO'
            );
        """)

        # Detalles de Bajadas (peso_bruto = Real | peso_contable = Redondeado)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pesaje_detalles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                recepcion_pesaje_uuid TEXT NOT NULL,
                codigo_trazabilidad TEXT NOT NULL,  -- A1260803-01-M-042-P01-1
                destino TEXT NOT NULL,              -- MERCADO / FABRICA
                numero_sacos INTEGER NOT NULL,
                peso_bruto REAL NOT NULL,           -- Peso Real de Balanza
                peso_contable REAL NOT NULL,        -- Peso Redondeado (Regla >= 0.90)
                tara REAL DEFAULT 0.0,
                peso_neto REAL NOT NULL,            -- Peso Neto Contable
                orden INTEGER NOT NULL,
                FOREIGN KEY (recepcion_pesaje_uuid) REFERENCES recepciones_pesaje(uuid)
            );
        """)

        # Agregar columna dni a la tabla existente sin borrar datos
        try:
            cursor.execute("ALTER TABLE agricultores ADD COLUMN dni TEXT;")
        except Exception:
            pass  # Ignorar si la columna ya existe
        conn.commit()
        conn.close()