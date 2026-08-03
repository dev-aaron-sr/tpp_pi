from typing import List, Dict, Optional
from database.connection import DatabaseConnection

class AgricultorDao:
    def __init__(self, db_conn: DatabaseConnection):
        self.db_conn = db_conn
    
    def obtener_todos(self) -> List[Dict]:
        """Obtiene la lista completa de agricultores activos registrados en SQLite."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agricultores WHERE activo = 1 ORDER BY nombres ASC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(r) for r in rows]

    def obtener_parcelas_por_agricultor(self, agricultor_id: int) -> List[Dict]:
        """Obtiene todas las parcelas pertenecientes a un agricultor por su ID local."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM parcelas WHERE agricultor_id = ?", (agricultor_id,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(r) for r in rows]
    
    def buscar_por_padron(self, codigo_padron: str) -> Optional[Dict]:
        """Busca un agricultor y sus parcelas asociadas por su código padrón."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agricultores WHERE codigo_padron = ? AND activo = 1", (codigo_padron,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        agricultor = dict(row)
        cursor.execute("SELECT * FROM parcelas WHERE agricultor_id = ?", (agricultor['id'],))
        agricultor['parcelas'] = [dict(p) for p in cursor.fetchall()]

        conn.close()
        return agricultor

    def guardar_maestros(self, agricultores_data: List[Dict]) -> None:
        """Guarda o actualiza la lista maestra descargada desde Laravel."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        for ag in agricultores_data:
            cursor.execute("""
                INSERT INTO agricultores (codigo_padron, nombres, apellidos, activo)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(codigo_padron) DO UPDATE SET
                    nombres = excluded.nombres,
                    apellidos = excluded.apellidos,
                    activo = excluded.activo
            """, (ag['codigo_padron'], ag['nombres'], ag.get('apellidos'), 1 if ag.get('activo', True) else 0))

            ag_id = cursor.lastrowid or cursor.execute("SELECT id FROM agricultores WHERE codigo_padron = ?", (ag['codigo_padron'],)).fetchone()['id']

            for parc in ag.get('parcelas', []):
                cursor.execute("""
                    INSERT INTO parcelas (agricultor_id, codigo_parcela, nombre_parcela, sector)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(codigo_parcela) DO UPDATE SET
                        nombre_parcela = excluded.nombre_parcela,
                        sector = excluded.sector
                """, (ag_id, parc['codigo_parcela'], parc['nombre_parcela'], parc.get('sector')))

        conn.commit()
        conn.close()