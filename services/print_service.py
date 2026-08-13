from datetime import datetime
import json
import os
import platform
import subprocess
from typing import Dict, List
from PIL import Image
import qrcode

IF_WINDOWS = platform.system() == "Windows"


class PrintService:

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path

    def _obtener_nombre_impresora(self, clave_config: str) -> str:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    return data.get(clave_config, "")
            except Exception:
                pass
        return ""

    def _enviar_raw_a_impresora(
        self, nombre_impresora: str, buffer_bytes: bytes
    ) -> bool:
      if not nombre_impresora or nombre_impresora.startswith("SIN"):
        print("⚠ No hay impresora configurada.")
        return False

      nombre_limpio = nombre_impresora.strip()

      if IF_WINDOWS:
        try:
          import win32print

          h_printer = win32print.OpenPrinter(nombre_limpio)
          try:
            h_job = win32print.StartDocPrinter(
                h_printer, 1, ("Impresion_RAW", None, "RAW")
            )
            win32print.StartPagePrinter(h_printer)
            win32print.WritePrinter(h_printer, buffer_bytes)
            win32print.EndPagePrinter(h_printer)
            win32print.EndDocPrinter(h_printer)
            return True
          finally:
            win32print.ClosePrinter(h_printer)
        except Exception as e:
          print(f"Error imprimiendo en Windows: {e}")
          return False
      else:
        # ENVÍO DIRECTO RAW EN LINUX / RASPBERRY PI
        try:
          p = subprocess.Popen(
              ["lpr", "-P", nombre_limpio, "-o", "raw"],
              stdin=subprocess.PIPE,
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE,
          )
          stdout, stderr = p.communicate(input=buffer_bytes)

          if p.returncode == 0:
            return True

          err = stderr.decode("utf-8", errors="ignore")
          print(f"⚠ Error enviando a {nombre_limpio} vía lpr: {err}")
          return False
        except Exception as e:
          print(f"⚠ Error de ejecución en Linux: {e}")
          return False

    # =========================================================================
    # 1. MÓDULO DE IMPRESIÓN DE RECIBOS (EPSON LX-350 / ESC/P) - SIN CAMBIOS
    # =========================================================================
    def imprimir_recibo_dec(
        self, recibo_data: Dict, nombre_impresora_override: str = None
    ) -> bool:
        """Genera e imprime el DEC en formato ESC/P para Epson matricial."""
        nombre_imp = (
            nombre_impresora_override
            or self._obtener_nombre_impresora("impresora_recibo")
        )
        if not nombre_imp or nombre_imp.startswith("SIN"):
            print("⚠ No hay impresora de recibos configurada.")
            return False

        INIT = b"\x1b\x40"
        CONDENSED_ON = b"\x0f"
        PAGE_LEN_5_5 = b"\x1b\x43\x21"  # 33 líneas (~5.5 pulgadas)
        FORM_FEED = b"\x0c"
        DOUBLE_ON = b"\x1b\x57\x01\x1b\x77\x01"
        DOUBLE_OFF = b"\x1b\x57\x00\x1b\x77\x00"
        BOLD_ON = b"\x1b\x45"
        BOLD_OFF = b"\x1b\x46"

        bajadas = recibo_data.get("bajadas", [])
        tot_mercado = sum(
            b.get("peso", 0) for b in bajadas if b.get("destino") == "MERCADO"
        )
        tot_fab_local = sum(
            b.get("peso", 0) for b in bajadas if b.get("destino") == "FABRICA_LOCAL"
        )
        tot_fab_planta = sum(
            b.get("peso", 0) for b in bajadas if b.get("destino") == "FABRICA_PLANTA"
        )
        tot_general = recibo_data.get(
            "peso_total", sum(b.get("peso", 0) for b in bajadas)
        )

        txt_header = []
        txt_header.append(
            f" No RECIBO: {recibo_data.get('codigo_ticket', 'PENDIENTE')}"
        )
        txt_header.append(" DOCUMENTO DE ENTREGA COOPERATIVO (DEC)")
        txt_header.append(
            "-----------------------------------------------------------"
        )

        titulo_coop = "COOPERATIVA TIERRA FERTIL"

        txt_body = []
        txt_body.append(
            "PUNTO DE LLEGADA : ACOPIO               TIPO SACO  : SACO"
        )
        txt_body.append(
            "COD COOPERATIVA  : 695-2025             CANT SACOS :"
            f" {recibo_data.get('total_sacos', 0)}"
        )
        txt_body.append(
            f"COD PARCELA      : {recibo_data.get('codigo_parcela', '-'):<20}"
            f" SECTOR     : {recibo_data.get('sector', '-')}"
        )
        txt_body.append(
            f"PRODUCTOR        : {recibo_data.get('socio_nombre', '-'):<20} MARGEN"
            f"     : {recibo_data.get('margen', '-')}"
        )
        txt_body.append(
            "COD SOCIO (PADRON):"
            f" {recibo_data.get('codigo_padron', '-'):<19} DNI/RUC    :"
            f" {recibo_data.get('documento', '-')}"
        )
        txt_body.append(
            f"FECHA ENTREGA    : {recibo_data.get('fecha_pesaje', '-'):<20} HORA"
            "       : -"
        )
        txt_body.append(
            "-----------------------------------------------------------"
        )
        txt_body.append("KG RECIBIDOS POR DESTINO:")
        txt_body.append(f"  - MERCADO        : {tot_mercado:>8.2f} kg")
        txt_body.append(f"  - FABRICA LOCAL  : {tot_fab_local:>8.2f} kg")
        txt_body.append(f"  - FABRICA PLANTA*: {tot_fab_planta:>8.2f} kg")
        txt_body.append(f"TOTAL PESADO ORIGEN: {tot_general:>8.2f} kg")
        txt_body.append(
            "-----------------------------------------------------------"
        )
        txt_body.append(
            "* Pesos de Fabrica Planta sujetos a ajuste por merma en balanza"
        )
        txt_body.append("  de destino.")
        txt_body.append("")
        txt_body.append("")
        txt_body.append(
            "_____________________               _____________________"
        )
        txt_body.append(
            "      GERENTE                                PRODUCTOR   "
        )

        bytes_titulo = (
            INIT
            + BOLD_ON
            + DOUBLE_ON
            + titulo_coop.encode("latin-1", errors="replace")
            + BOLD_OFF
            + DOUBLE_OFF
            + b"\r\n"
        )
        bytes_header = (
            CONDENSED_ON
            + "\r\n".join(txt_header).encode("latin-1", errors="replace")
            + b"\r\n"
        )
        bytes_body = "\r\n".join(txt_body).encode("latin-1", errors="replace")

        buffer_final = (
            INIT + PAGE_LEN_5_5 + bytes_titulo + bytes_header + bytes_body + FORM_FEED
        )
        return self._enviar_raw_a_impresora(nombre_imp, buffer_final)

    # =========================================================================
    # 2. MÓDULO DE ETIQUETAS (TSC TE200 / TSPL) - BITMAPS LIMPIOS SINO BORDES
    # =========================================================================
    def _imagen_a_tspl_bitmap(self, img: Image.Image, x: int, y: int) -> bytes:
        """Convierte cualquier imagen PIL a comando BITMAP de TSPL sin bordes ni tramado."""
        gray = img.convert("L")
        w, h = gray.size
        bytes_por_fila = (w + 7) // 8

        bitmap_bytes = bytearray()
        for r in range(h):
            for c in range(bytes_por_fila):
                byte_val = 0
                for bit in range(8):
                    px_x = c * 8 + bit
                    if px_x < w:
                        if gray.getpixel((px_x, r)) < 128:  # Negro en TSPL
                            byte_val |= 1 << (7 - bit)
                bitmap_bytes.append(byte_val)

        header = f"BITMAP {x},{y},{bytes_por_fila},{h},0,".encode("latin-1")
        return header + bytes(bitmap_bytes) + b"\r\n"

    def _obtener_logo_bitmap(
        self,
        logo_path: str,
        x: int = 35,
        y: int = 15,
        max_w: int = 130,
        max_h: int = 75,
    ) -> bytes:
        """Procesa el logo fusionando transparencias sobre un lienzo blanco puro."""
        if not os.path.exists(logo_path):
            return b""
        try:
            raw = Image.open(logo_path)
            bg = Image.new("RGB", raw.size, (255, 255, 255))
            if raw.mode in ("RGBA", "LA") or (
                raw.mode == "P" and "transparency" in raw.info
            ):
                rgba = raw.convert("RGBA")
                bg.paste(rgba, mask=rgba.split()[3])
            else:
                bg.paste(raw)

            bg.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            return self._imagen_a_tspl_bitmap(bg, x, y)
        except Exception as e:
            print(f"⚠ Error procesando logo: {e}")
            return b""

    def _obtener_qr_bitmap(
        self, texto: str, x: int = 370, y: int = 170, box_size: int = 5
    ) -> bytes:
        """Genera el QR como matriz limpia sobre fondo blanco."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=box_size,
                border=1,
            )
            qr.add_data(texto)
            qr.make(fit=True)

            qr_img = qr.make_image(
                fill_color="black", back_color="white"
            ).convert("RGB")
            return self._imagen_a_tspl_bitmap(qr_img, x, y)
        except Exception as e:
            print(f"⚠ Error generando QR: {e}")
            return b""

    def imprimir_etiquetas_trazabilidad(
        self, detalles: List[Dict], nombre_impresora_override: str = None
    ) -> bool:
        """Imprime etiquetas TSPL2 de 76x51mm para destino MERCADO."""
        nombre_imp = (
            nombre_impresora_override
            or self._obtener_nombre_impresora("impresora_etiqueta")
        )
        if not nombre_imp or nombre_imp.startswith("SIN"):
            print("⚠ No hay impresora de etiquetas configurada.")
            return False

        detalles_mercado = [d for d in detalles if d.get("destino") == "MERCADO"]
        if not detalles_mercado:
            return True

        buffer_final = bytearray()
        logo_path = (
            "assets/logo.png" if os.path.exists("assets/logo.png") else "logo.png"
        )

        cmd_logo = self._obtener_logo_bitmap(
            logo_path, x=35, y=15, max_w=130, max_h=75
        )

        for d in detalles_mercado:
            cod_traza = d.get("codigo_trazabilidad", "S/N")
            item_uuid = d.get("uuid", "")
            num_sacos = int(d.get("numero_sacos", 1)) or 1
            acopio = (
                cod_traza.split("-")[0] if "-" in cod_traza else "A126080501"
            )

            raw_fecha = d.get("fecha_pesaje", "")
            if raw_fecha:
                try:
                    dt_obj = datetime.strptime(str(raw_fecha), "%Y-%m-%d %H:%M:%S")
                    fecha_hora = dt_obj.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    fecha_hora = str(raw_fecha)
            else:
                fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

            pos_x_texto = 180 if cmd_logo else 35
            cmd_qr = self._obtener_qr_bitmap(item_uuid, x=370, y=170, box_size=5)

            tspl_init = (
                "SIZE 76 mm, 51 mm\r\n"
                "GAP 3 mm, 0 mm\r\n"
                "DIRECTION 1\r\n"
                "CLS\r\n"
                "DENSITY 6\r\n"
                "SPEED 4\r\n"
            ).encode("latin-1")

            buffer_final.extend(tspl_init)

            if cmd_logo:
                buffer_final.extend(cmd_logo)

            if cmd_qr:
                buffer_final.extend(cmd_qr)

            tspl_body = f"""
; --- ENCABEZADO ---
TEXT {pos_x_texto},22,"2",0,1,1,"COOP. AGRARIA DE USUARIOS"
TEXT {pos_x_texto},52,"3",0,1,1,"TIERRA FERTIL"

; --- CINTA NEGRA DE TRAZABILIDAD ---
TEXT 50, 115, "3", 0, 1, 1, "{cod_traza}"
REVERSE 35, 105, 538, 48

; --- DATOS DEL PESAJE ---
TEXT 35, 175, "3", 0, 1, 1, "ACOPIO: {acopio}"
TEXT 35, 215, "3", 0, 1, 1, "PRODUCTO: MARACUYA"
TEXT 35, 255, "3", 0, 1, 1, "{fecha_hora}"
TEXT 35, 310, "4", 0, 1, 1, "MERCADO"

; --- COPIAS POR SACO ---
PRINT 1, {num_sacos}
"""
            buffer_final.extend(tspl_body.encode("latin-1", errors="replace"))

        return self._enviar_raw_a_impresora(nombre_imp, bytes(buffer_final))