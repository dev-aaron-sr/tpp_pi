from typing import List, Dict
from database.connection import DatabaseConnection

class RecepcionPesajeDao:
    def __init__(self, db_conn: DatabaseConnection):
        self.db_conn = db_conn

    '''def guardar_pesaje_completo(self, recepcion_data: Dict, detalles: List[Dict]) -> bool:
        """Guarda la cabecera y el detalle del pesaje de forma atómica."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute("""
                INSERT INTO recepciones_pesaje (
                    uuid, lote_acopio_id, codigo_lote_origen, codigo_ticket,
                    codigo_padron, codigo_parcela, producto, destino,
                    total_sacos, peso_bruto_total, tara_total, peso_neto_total,
                    fecha_pesaje, observaciones, sincronizado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                recepcion_data['uuid'], recepcion_data.get('lote_acopio_id'),
                recepcion_data['codigo_lote_origen'], recepcion_data['codigo_ticket'],
                recepcion_data['codigo_padron'], recepcion_data['codigo_parcela'],
                recepcion_data.get('producto', 'MARACUYA'), recepcion_data['destino'],
                recepcion_data['total_sacos'], recepcion_data['peso_bruto_total'],
                recepcion_data['tara_total'], recepcion_data['peso_neto_total'],
                recepcion_data['fecha_pesaje'], recepcion_data.get('observaciones')
            ))

            for det in detalles:
                cursor.execute("""
                    INSERT INTO pesaje_detalles (
                        uuid, recepcion_pesaje_uuid, numero_sacos,
                        peso_bruto, tara, peso_neto, orden
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    det['uuid'], recepcion_data['uuid'], det['numero_sacos'],
                    det['peso_bruto'], det['tara'], det['peso_neto'], det['orden']
                ))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error en BD local: {e}")
            return False
        finally:
            conn.close()'''

    def obtener_pendientes_sincronizacion(self) -> List[Dict]:
        """Recupera pesajes guardados pendientes de subida."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM recepciones_pesaje WHERE sincronizado = 0")
        recepciones = [dict(r) for r in cursor.fetchall()]

        for rec in recepciones:
            cursor.execute("SELECT * FROM pesaje_detalles WHERE recepcion_pesaje_uuid = ?", (rec['uuid'],))
            rec['detalles'] = [dict(d) for d in cursor.fetchall()]

        conn.close()
        return recepciones

    def marcar_sincronizados(self, uuids: List[str]) -> None:
        """Actualiza el estado a sincronizado=1 para los UUIDs confirmados por Laravel."""
        if not uuids:
            return
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(uuids))
        cursor.execute(f"UPDATE recepciones_pesaje SET sincronizado = 1 WHERE uuid IN ({placeholders})", uuids)
        
        conn.commit()
        conn.close()
    
    def generar_siguiente_codigo_ticket(self, serie: str = "RE01") -> str:
        """Genera el número de recibo tipo factura/boleta (ej: RE01-000001)."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM recepciones_pesaje")
        total = cursor.fetchone()[0]
        conn.close()

        return f"{serie}-{total + 1:06d}"

    def guardar_pesaje_completo(self, recepcion_data: Dict, detalles: List[Dict]) -> bool:
        """Guarda la cabecera y el detalle de bajadas de balanza."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute("""
                INSERT INTO recepciones_pesaje (
                    uuid, lote_acopio_id, codigo_lote_origen, codigo_ticket,
                    codigo_padron, codigo_parcela, producto, destino,
                    total_sacos, peso_bruto_total, tara_total, peso_neto_total,
                    fecha_pesaje, observaciones, sincronizado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                recepcion_data['uuid'], recepcion_data.get('lote_acopio_id'),
                recepcion_data['codigo_lote_origen'], recepcion_data['codigo_ticket'],
                recepcion_data['codigo_padron'], recepcion_data['codigo_parcela'],
                recepcion_data.get('producto', 'MARACUYA'), recepcion_data['destino'],
                recepcion_data['total_sacos'], recepcion_data['peso_bruto_total'],
                recepcion_data['tara_total'], recepcion_data['peso_neto_total'],
                recepcion_data['fecha_pesaje'], recepcion_data.get('observaciones')
            ))

            for det in detalles:
                cursor.execute("""
                    INSERT INTO pesaje_detalles (
                        uuid, recepcion_pesaje_uuid, destino, numero_sacos,
                        peso_bruto, tara, peso_neto, orden
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    det['uuid'], recepcion_data['uuid'], det['destino'], det['numero_sacos'],
                    det['peso_bruto'], det['tara'], det['peso_neto'], det['orden']
                ))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error guardando recibo en SQLite: {e}")
            return False
        finally:
            conn.close()

    def obtener_historial_por_fecha(self, fecha_ymd: str) -> List[Dict]:
        """Recupera todos los recibos (sincronizados o no) registrados en una fecha específica (YYYY-MM-DD)."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.*, 
                   a.nombres || ' ' || COALESCE(a.apellidos, '') AS socio_nombre
            FROM recepciones_pesaje r
            LEFT JOIN agricultores a ON a.codigo_padron = r.codigo_padron
            WHERE DATE(r.fecha_pesaje) = ?
            ORDER BY r.id DESC
        """, (fecha_ymd,))

        recepciones = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return recepciones

    def obtener_detalles_por_recepcion_uuid(self, recepcion_uuid: str) -> List[Dict]:
        """Obtiene las bajadas de balanza individuales para el panel de detalle."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM pesaje_detalles 
            WHERE recepcion_pesaje_uuid = ? 
            ORDER BY orden ASC
        """, (recepcion_uuid,))

        detalles = [dict(d) for d in cursor.fetchall()]
        conn.close()
        return detalles