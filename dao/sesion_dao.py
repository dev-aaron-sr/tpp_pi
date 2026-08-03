from typing import Optional, Dict
from datetime import datetime
from database.connection import DatabaseConnection

class SesionDao:
    def __init__(self, db_conn: DatabaseConnection):
        self.db_conn = db_conn

    def obtener_sesion_activa(self) -> Optional[Dict]:
        """Devuelve la sesión de pesaje actualmente ABIERTA, si existe."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sesiones_pesaje WHERE estado = 'ABIERTA' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def abrir_nueva_sesion(self) -> Dict:
        """Crea una nueva sesión de pesaje correlativa por fecha (ej: SES-20260731-01)."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        fecha_str = datetime.now().strftime("%Y%m%d")
        fecha_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT COUNT(*) FROM sesiones_pesaje WHERE codigo_sesion LIKE ?", (f"SES-{fecha_str}-%",))
        count = cursor.fetchone()[0] + 1
        codigo_sesion = f"SES-{fecha_str}-{count:02d}"

        cursor.execute("""
            INSERT INTO sesiones_pesaje (codigo_sesion, fecha_apertura, estado)
            VALUES (?, ?, 'ABIERTA')
        """, (codigo_sesion, fecha_full))

        conn.commit()
        conn.close()
        return self.obtener_sesion_activa()

    def cerrar_sesion_activa(self) -> bool:
        """Cierra la sesión de pesaje actual."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        fecha_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE sesiones_pesaje 
            SET estado = 'CERRADA', fecha_cierre = ? 
            WHERE estado = 'ABIERTA'
        """, (fecha_full,))

        conn.commit()
        conn.close()
        return True