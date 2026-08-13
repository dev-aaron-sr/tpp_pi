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
                INSERT INTO agricultores (codigo_padron, dni, nombres, apellidos, activo)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(codigo_padron) DO UPDATE SET
                    dni = excluded.dni,
                    nombres = excluded.nombres,
                    apellidos = excluded.apellidos,
                    activo = excluded.activo
            """, (
                ag['codigo_padron'], 
                ag.get('numero_documento'),  # Captura el DNI desde el payload que envía Laravel
                ag['nombres'], 
                ag.get('apellidos'), 
                1 if ag.get('activo', True) else 0
            ))

            cursor.execute("SELECT id FROM agricultores WHERE codigo_padron = ?", (ag['codigo_padron'],))
            row = cursor.fetchone()
            if not row:
                continue
            ag_id = row['id'] if isinstance(row, dict) else row[0]

            for parc in ag.get('parcelas', []):
                cursor.execute("""
                    INSERT INTO parcelas (agricultor_id, codigo_interno, codigo_parcela, nombre_parcela, sector)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(agricultor_id, codigo_interno) DO UPDATE SET
                        codigo_parcela = excluded.codigo_parcela,
                        nombre_parcela = excluded.nombre_parcela,
                        sector = excluded.sector
                """, (
                    ag_id, 
                    parc['codigo_interno'], 
                    parc.get('codigo_parcela'), 
                    parc['nombre_parcela'], 
                    parc.get('sector')
                ))

        conn.commit()
        conn.close()
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

            cursor.execute("SELECT id FROM agricultores WHERE codigo_padron = ?", (ag['codigo_padron'],))
            row = cursor.fetchone()
            if not row:
                continue
            ag_id = row['id'] if isinstance(row, dict) else row[0]

            for parc in ag.get('parcelas', []):
                cursor.execute("""
                    INSERT INTO parcelas (agricultor_id, codigo_interno, codigo_parcela, nombre_parcela, sector)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(agricultor_id, codigo_interno) DO UPDATE SET
                        codigo_parcela = excluded.codigo_parcela,
                        nombre_parcela = excluded.nombre_parcela,
                        sector = excluded.sector
                """, (
                    ag_id, 
                    parc['codigo_interno'], 
                    parc.get('codigo_parcela'), 
                    parc['nombre_parcela'], 
                    parc.get('sector')
                ))

        conn.commit()
        conn.close()