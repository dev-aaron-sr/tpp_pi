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

    def abrir_nueva_sesion(self, codigo_acopio: str = "A1") -> Dict:
        """Crea una nueva sesión de pesaje correlativa por fecha (ej: A126080401)."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        # Formato YYMMDD (Ej: 260804)
        fecha_yymmdd = datetime.now().strftime("%y%m%d")
        fecha_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Conteo de jornadas del día para el centro de acopio
        patron_busqueda = f"{codigo_acopio}{fecha_yymmdd}%"
        cursor.execute("SELECT COUNT(*) FROM sesiones_pesaje WHERE codigo_sesion LIKE ?", (patron_busqueda,))
        count = cursor.fetchone()[0] + 1

        # Estructura final: [ACOPIO][YYMMDD][JORNADA] -> A1 + 260804 + 01 = A126080401
        codigo_sesion = f"{codigo_acopio}{fecha_yymmdd}{count:02d}"

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