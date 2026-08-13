from typing import List, Dict, Optional
from database.connection import DatabaseConnection

class RecepcionPesajeDao:
    def __init__(self, db_conn: DatabaseConnection):
        self.db_conn = db_conn

    def obtener_pendientes_sincronizacion(self) -> List[Dict]:
        """Recupera pesajes COMPLETADOS pendientes de subir a Laravel."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        # Solo enviamos recibos finalizados (estado = 'COMPLETADO')
        cursor.execute("SELECT * FROM recepciones_pesaje WHERE sincronizado = 0 AND estado = 'COMPLETADO'")
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
        """Genera el número de recibo correlativo contando únicamente recibos completados."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM recepciones_pesaje WHERE estado = 'COMPLETADO'")
        total = cursor.fetchone()[0]
        conn.close()

        return f"{serie}-{total + 1:06d}"

    # -------------------------------------------------------------------------
    # OPERACIONES ANTI-CAÍDAS / EN PROCESO (BORRADORES)
    # -------------------------------------------------------------------------

    def obtener_recepcion_en_proceso(self, codigo_padron: str, codigo_lote_origen: str) -> Optional[Dict]:
        """Busca si el agricultor tiene un pesaje abierto/en proceso en la jornada activa."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM recepciones_pesaje 
            WHERE codigo_padron = ? AND codigo_lote_origen = ? AND estado = 'EN_PROCESO' 
            ORDER BY id DESC LIMIT 1
        """, (codigo_padron, codigo_lote_origen))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        recepcion = dict(row)
        cursor.execute("SELECT * FROM pesaje_detalles WHERE recepcion_pesaje_uuid = ? ORDER BY orden ASC", (recepcion['uuid'],))
        recepcion['detalles'] = [dict(d) for d in cursor.fetchall()]

        conn.close()
        return recepcion

    def registrar_bajada_individual(self, recepcion_data: Dict, detalle_data: Dict) -> bool:
        """
        Guarda o crea la cabecera en estado 'EN_PROCESO' e inserta la bajada al instante en SQLite.
        A prueba de cortes de energía.
        """
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION;")

            # 1. Crear cabecera si no existe aún
            cursor.execute("SELECT id FROM recepciones_pesaje WHERE uuid = ?", (recepcion_data['uuid'],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO recepciones_pesaje (
                        uuid, lote_acopio_id, codigo_lote_origen, codigo_ticket,
                        codigo_padron, codigo_parcela, producto,
                        total_sacos, peso_bruto_total, tara_total, peso_neto_total,
                        fecha_pesaje, observaciones, sincronizado, estado
                    ) VALUES (?, ?, ?, 'PENDIENTE', ?, ?, ?, 0, 0.0, 0.0, 0.0, ?, ?, 0, 'EN_PROCESO')
                """, (
                    recepcion_data['uuid'], recepcion_data.get('lote_acopio_id'),
                    recepcion_data['codigo_lote_origen'], recepcion_data['codigo_padron'],
                    recepcion_data['codigo_parcela'], recepcion_data.get('producto', 'MARACUYA'),
                    recepcion_data['fecha_pesaje'], recepcion_data.get('observaciones')
                ))

            # 2. Insertar el detalle de la bajada
            cursor.execute("""
                INSERT INTO pesaje_detalles (
                    uuid, recepcion_pesaje_uuid, codigo_trazabilidad, destino, numero_sacos,
                    peso_bruto, peso_contable, tara, peso_neto, orden
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                detalle_data['uuid'], recepcion_data['uuid'], detalle_data['codigo_trazabilidad'],
                detalle_data['destino'], detalle_data['numero_sacos'], detalle_data['peso_bruto'],
                detalle_data['peso_contable'], detalle_data['tara'], detalle_data['peso_neto'],
                detalle_data['orden']
            ))

            # 3. Actualizar totales acumulados en la cabecera
            cursor.execute("""
                UPDATE recepciones_pesaje 
                SET total_sacos = (SELECT COALESCE(SUM(numero_sacos), 0) FROM pesaje_detalles WHERE recepcion_pesaje_uuid = ?),
                    peso_bruto_total = (SELECT COALESCE(SUM(peso_contable), 0.0) FROM pesaje_detalles WHERE recepcion_pesaje_uuid = ?),
                    peso_neto_total = (SELECT COALESCE(SUM(peso_neto), 0.0) FROM pesaje_detalles WHERE recepcion_pesaje_uuid = ?)
                WHERE uuid = ?
            """, (recepcion_data['uuid'], recepcion_data['uuid'], recepcion_data['uuid'], recepcion_data['uuid']))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error registrando bajada individual en SQLite: {e}")
            return False
        finally:
            conn.close()

    def eliminar_bajada_individual(self, recepcion_uuid: str, detalle_uuid: str) -> bool:
        """Elimina una pesada específica en SQLite si el operador cometió un error."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION;")

            cursor.execute("DELETE FROM pesaje_detalles WHERE uuid = ? AND recepcion_pesaje_uuid = ?", (detalle_uuid, recepcion_uuid))

            # Recalcular totales
            cursor.execute("""
                UPDATE recepciones_pesaje 
                SET total_sacos = (SELECT COALESCE(SUM(numero_sacos), 0) FROM pesaje_detalles WHERE recepcion_pesaje_uuid = ?),
                    peso_bruto_total = (SELECT COALESCE(SUM(peso_contable), 0.0) FROM pesaje_detalles WHERE recepcion_pesaje_uuid = ?),
                    peso_neto_total = (SELECT COALESCE(SUM(peso_neto), 0.0) FROM pesaje_detalles WHERE recepcion_pesaje_uuid = ?)
                WHERE uuid = ?
            """, (recepcion_uuid, recepcion_uuid, recepcion_uuid, recepcion_uuid))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error eliminando bajada individual en SQLite: {e}")
            return False
        finally:
            conn.close()

    def finalizar_recepcion_en_proceso(self, recepcion_uuid: str, codigo_ticket: str, fecha_cierre: str) -> bool:
        """Marca el recibo como COMPLETADO asignando el número de ticket definitivo."""
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE recepciones_pesaje 
                SET estado = 'COMPLETADO',
                    codigo_ticket = ?,
                    fecha_pesaje = ?
                WHERE uuid = ?
            """, (codigo_ticket, fecha_cierre, recepcion_uuid))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error finalizando recepción en SQLite: {e}")
            return False
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # CONSULTAS DE HISTORIAL Y DETALLES
    # -------------------------------------------------------------------------

    def obtener_historial_por_fecha(self, fecha_ymd: str) -> List[Dict]:
        conn = self.db_conn.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.*, 
                   a.nombres || ' ' || COALESCE(a.apellidos, '') AS socio_nombre
            FROM recepciones_pesaje r
            LEFT JOIN agricultores a ON a.codigo_padron = r.codigo_padron
            LEFT JOIN parcelas p ON a.id = p.agricultor_id AND r.codigo_parcela = p.codigo_interno
            WHERE DATE(r.fecha_pesaje) = ? AND r.estado = 'COMPLETADO'
            ORDER BY r.id DESC
        """, (fecha_ymd,))

        recepciones = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return recepciones

    def obtener_detalles_por_recepcion_uuid(self, recepcion_uuid: str) -> List[Dict]:
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