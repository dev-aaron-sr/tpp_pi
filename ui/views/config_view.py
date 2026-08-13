import json
import os
import threading
import time
import customtkinter as ctk
import serial
import serial.tools.list_ports


class ConfiguracionView(ctk.CTkFrame):

  def __init__(self, parent, on_guardar_cb=None):
    super().__init__(parent, fg_color="#CBD5E1", corner_radius=0)
    self.on_guardar_cb = on_guardar_cb
    self.config_path = "config.json"

    self._build_ui()
    self._cargar_configuracion()

  def _build_ui(self):
    card = ctk.CTkFrame(
        self,
        fg_color="#FFFFFF",
        border_width=2,
        border_color="#000000",
        corner_radius=0,
        width=580,
        height=520,
    )
    card.place(relx=0.5, rely=0.5, anchor="center")
    card.pack_propagate(False)

    ctk.CTkLabel(
        card,
        text="⚙️ CONFIGURACIÓN DE HARDWARE",
        font=("Arial", 18, "bold"),
        text_color="#000000",
    ).pack(pady=(15, 10))

    puertos_detectados = self._obtener_puertos_sistema()

    # ---------------------------------------------------------------------
    # 1. SECCIÓN BALANZA
    # ---------------------------------------------------------------------
    ctk.CTkLabel(
        card,
        text="1. Balanza Solo Peso (Serie/USB):",
        font=("Arial", 14, "bold"),
        text_color="#000000",
    ).pack(anchor="w", padx=25, pady=(5, 2))

    f_balanza = ctk.CTkFrame(card, fg_color="transparent")
    f_balanza.pack(fill="x", padx=25, pady=(0, 5))

    self.cmb_balanza_port = ctk.CTkComboBox(
        f_balanza,
        values=puertos_detectados,
        fg_color="#FFFFFF",
        text_color="#000000",
        button_color="#1E3A8A",
        corner_radius=0,
        height=32,
        width=200,
    )
    self.cmb_balanza_port.pack(side="left", padx=(0, 8))

    self.cmb_baudrate = ctk.CTkOptionMenu(
        f_balanza,
        values=["2400", "4800", "9600", "19200", "115200"],
        fg_color="#FFFFFF",
        text_color="#000000",
        button_color="#1E3A8A",
        corner_radius=0,
        height=32,
        width=110,
    )
    self.cmb_baudrate.pack(side="left")
    self.cmb_baudrate.set("9600")

    self.btn_test_balanza = ctk.CTkButton(
        f_balanza,
        text="Prob. Conexión",
        font=("Arial", 12, "bold"),
        fg_color="#0284C7",
        hover_color="#0369A1",
        text_color="#FFFFFF",
        corner_radius=0,
        height=32,
        width=120,
        command=self._testear_balanza,
    )
    self.btn_test_balanza.pack(side="right")

    # Status / Visor de prueba
    f_test_res = ctk.CTkFrame(card, fg_color="transparent")
    f_test_res.pack(fill="x", padx=25, pady=(0, 10))

    self.lbl_status_balanza = ctk.CTkLabel(
        f_test_res,
        text="Estado: Sin conexión",
        font=("Arial", 12, "bold"),
        text_color="#64748B",
    )
    self.lbl_status_balanza.pack(side="left")

    self.txt_peso_test = ctk.CTkEntry(
        f_test_res,
        font=("Arial", 14, "bold"),
        justify="center",
        width=100,
        height=30,
        fg_color="#F1F5F9",
        text_color="#000000",
        border_color="#94A3B8",
        state="disabled",
    )
    self.txt_peso_test.pack(side="right")

    # ---------------------------------------------------------------------
    # 2. IMPRESORA DE RECIBOS
    # ---------------------------------------------------------------------
    # ctk.CTkLabel(
    #     card,
    #     text="2. Puerto / Nombre Impresora de Recibos:",
    #     font=("Arial", 14, "bold"),
    #     text_color="#000000",
    # ).pack(anchor="w", padx=25, pady=(5, 2))

    # self.cmb_imp_recibo = ctk.CTkComboBox(
    #     card,
    #     values=puertos_detectados,
    #     fg_color="#FFFFFF",
    #     text_color="#000000",
    #     button_color="#1E3A8A",
    #     corner_radius=0,
    #     height=32,
    # )
    # self.cmb_imp_recibo.pack(fill="x", padx=25, pady=(0, 10))

    # # ---------------------------------------------------------------------
    # # 3. IMPRESORA DE ETIQUETAS
    # # ---------------------------------------------------------------------
    # ctk.CTkLabel(
    #     card,
    #     text="3. Puerto / Nombre Impresora de Etiquetas:",
    #     font=("Arial", 14, "bold"),
    #     text_color="#000000",
    # ).pack(anchor="w", padx=25, pady=(5, 2))

    # self.cmb_imp_etiqueta = ctk.CTkComboBox(
    #     card,
    #     values=puertos_detectados,
    #     fg_color="#FFFFFF",
    #     text_color="#000000",
    #     button_color="#1E3A8A",
    #     corner_radius=0,
    #     height=32,
    # )
    # self.cmb_imp_etiqueta.pack(fill="x", padx=25, pady=(0, 15))

    puertos_detectados = self._obtener_puertos_sistema()
    impresoras_detectadas = self._obtener_impresoras_sistema() # <--- LEER IMPRESORAS

    # ---------------------------------------------------------------------
    # 2. IMPRESORA DE RECIBOS (DEC / EPSON LX350)
    # ---------------------------------------------------------------------
    ctk.CTkLabel(card, text="2. Impresora de Recibos (Epson / Ticket):", font=("Arial", 14, "bold"), text_color="#000000").pack(anchor="w", padx=25, pady=(5, 2))

    f_imp_recibo = ctk.CTkFrame(card, fg_color="transparent")
    f_imp_recibo.pack(fill="x", padx=25, pady=(0, 5))

    self.cmb_imp_recibo = ctk.CTkComboBox(
        f_imp_recibo,
        values=impresoras_detectadas, # <--- AHORA MUESTRA LAS IMPRESORAS
        fg_color="#FFFFFF", text_color="#000000", button_color="#1E3A8A",
        corner_radius=0, height=32, width=330
    )
    self.cmb_imp_recibo.pack(side="left", padx=(0, 8))
    self.btn_test_recibo = ctk.CTkButton(
        f_imp_recibo, text="Prob. Impresión", font=("Arial", 12, "bold"),
        fg_color="#0284C7", hover_color="#0369A1", text_color="#FFFFFF",
        corner_radius=0, height=32, width=120,
        command=self._testear_impresora_recibo
    )
    self.btn_test_recibo.pack(side="right")
    self.lbl_status_recibo = ctk.CTkLabel(card, text="Estado: Listo", font=("Arial", 11, "bold"), text_color="#64748B")
    self.lbl_status_recibo.pack(anchor="w", padx=25, pady=(0, 10))

    # ---------------------------------------------------------------------
    # 3. IMPRESORA DE ETIQUETAS
    # ---------------------------------------------------------------------
    # ctk.CTkLabel(card, text="3. Impresora de Etiquetas (Trazabilidad):", font=("Arial", 14, "bold"), text_color="#000000").pack(anchor="w", padx=25, pady=(5, 2))

    # self.cmb_imp_etiqueta = ctk.CTkComboBox(
    #     card,
    #     values=impresoras_detectadas, # <--- AHORA MUESTRA LAS IMPRESORAS
    #     fg_color="#FFFFFF", text_color="#000000", button_color="#1E3A8A",
    #     corner_radius=0, height=32
    # )
    # self.cmb_imp_etiqueta.pack(fill="x", padx=25, pady=(0, 15))

    # ---------------------------------------------------------------------
    # 3. IMPRESORA DE ETIQUETAS (TSC TE200 / TSPL)
    # ---------------------------------------------------------------------
    ctk.CTkLabel(card, text="3. Impresora de Etiquetas (Trazabilidad):", font=("Arial", 14, "bold"), text_color="#000000").pack(anchor="w", padx=25, pady=(5, 2))

    f_imp_etiqueta = ctk.CTkFrame(card, fg_color="transparent")
    f_imp_etiqueta.pack(fill="x", padx=25, pady=(0, 5))

    self.cmb_imp_etiqueta = ctk.CTkComboBox(
        f_imp_etiqueta,
        values=impresoras_detectadas,
        fg_color="#FFFFFF", text_color="#000000", button_color="#1E3A8A",
        corner_radius=0, height=32, width=330
    )
    self.cmb_imp_etiqueta.pack(side="left", padx=(0, 8))

    self.btn_test_etiqueta = ctk.CTkButton(
        f_imp_etiqueta, text="Prob. Etiqueta", font=("Arial", 12, "bold"),
        fg_color="#0284C7", hover_color="#0369A1", text_color="#FFFFFF",
        corner_radius=0, height=32, width=120,
        command=self._testear_impresora_etiqueta
    )
    self.btn_test_etiqueta.pack(side="right")

    self.lbl_status_etiqueta = ctk.CTkLabel(card, text="Estado: Listo", font=("Arial", 11, "bold"), text_color="#64748B")
    self.lbl_status_etiqueta.pack(anchor="w", padx=25, pady=(0, 15))

    # ---------------------------------------------------------------------
    # BOTÓN GUARDAR
    # ---------------------------------------------------------------------
    self.btn_guardar = ctk.CTkButton(
        card,
        text="💾 GUARDAR CONFIGURACIÓN",
        font=("Arial", 14, "bold"),
        fg_color="#16A34A",
        hover_color="#15803D",
        text_color="#FFFFFF",
        corner_radius=0,
        height=45,
        command=self._guardar_configuracion,
    )
    self.btn_guardar.pack(fill="x", padx=25, side="bottom", pady=15)

  def _obtener_puertos_sistema(self):
    ports = serial.tools.list_ports.comports()
    lista = [p.device for p in ports]
    return lista if lista else ["COM1", "/dev/ttyUSB0"]

  def _obtener_impresoras_sistema(self):
        """Detecta las impresoras instaladas en el sistema operativo (Windows / Linux)."""
        impresoras = []
        import platform
        if platform.system() == "Windows":
            try:
                import win32print
                printers = win32print.EnumPrinters(
                    win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                )
                impresoras = [p[2] for p in printers]
            except Exception as e:
                print(f"Error enumerando impresoras en Windows: {e}")
        else:
            # Linux / Raspberry Pi (CUPS)
            import subprocess
            try:
                output = subprocess.check_output(["lpstat", "-a"], text=True)
                for line in output.splitlines():
                    if line.strip():
                        impresoras.append(line.split()[0])
            except Exception:
                pass

        return impresoras if impresoras else ["SIN IMPRESORAS INSTALADAS"]
  

  def _testear_balanza(self):
    puerto = self.cmb_balanza_port.get().strip()
    baudios = int(self.cmb_baudrate.get().strip())

    self.lbl_status_balanza.configure(
        text="Conectando...", text_color="#D97706"
    )
    self.btn_test_balanza.configure(state="disabled")

    def _hilo_test():
      try:
        ser = serial.Serial(puerto, baudios, timeout=1.5)
        time.sleep(0.2)
        lectura = ser.readline().decode("utf-8", errors="ignore").strip()
        ser.close()

        # Extraer números básicos
        import re

        match = re.search(r"\d+\.\d+|\d+", lectura)
        peso_leido = match.group(0) if match else "0.00"

        self.after(
            0,
            lambda: self._actualizar_ui_test(
                True, f"¡Éxito! Conectado", peso_leido
            ),
        )
      except Exception as e:
        self.after(
            0,
            lambda: self._actualizar_ui_test(
                False, f"Error: No conecta", "0.00"
            ),
        )

    threading.Thread(target=_hilo_test, daemon=True).start()

  def _actualizar_ui_test(self, exito: bool, msg: str, peso: str):
    self.btn_test_balanza.configure(state="normal")
    color = "#16A34A" if exito else "#DC2626"
    self.lbl_status_balanza.configure(text=msg, text_color=color)

    self.txt_peso_test.configure(state="normal")
    self.txt_peso_test.delete(0, "end")
    self.txt_peso_test.insert(0, f"{peso} kg")
    self.txt_peso_test.configure(state="disabled")

  def _cargar_configuracion(self):
    if os.path.exists(self.config_path):
      try:
        with open(self.config_path, "r") as f:
          data = json.load(f)
          if data.get("balanza_port"):
            self.cmb_balanza_port.set(data["balanza_port"])
          if data.get("balanza_baudrate"):
            self.cmb_baudrate.set(str(data["balanza_baudrate"]))
          if data.get("impresora_recibo"):
            self.cmb_imp_recibo.set(data["impresora_recibo"])
          if data.get("impresora_etiqueta"):
            self.cmb_imp_etiqueta.set(data["impresora_etiqueta"])
      except Exception as e:
        print(f"Error leyendo config.json: {e}")

  def _guardar_configuracion(self):
    data = {
        "balanza_port": self.cmb_balanza_port.get().strip(),
        "balanza_baudrate": int(self.cmb_baudrate.get().strip()),
        "impresora_recibo": self.cmb_imp_recibo.get().strip(),
        "impresora_etiqueta": self.cmb_imp_etiqueta.get().strip(),
    }

    with open(self.config_path, "w") as f:
      json.dump(data, f, indent=4)

    if self.on_guardar_cb:
      self.on_guardar_cb(data)

  def _testear_impresora_recibo(self):
      impresora_nombre = self.cmb_imp_recibo.get().strip()
      if not impresora_nombre or impresora_nombre.startswith("SIN"):
          self.lbl_status_recibo.configure(text="⚠ Seleccione una impresora válida", text_color="#DC2626")
          return

      self.lbl_status_recibo.configure(text="Enviando prueba a impresora...", text_color="#D97706")

      def _hilo_print():
          try:
              from services.print_service import PrintService
              ps = PrintService()
              
              # Payload sintético de prueba
              test_payload = {
                  "codigo_ticket": "TEST-0001",
                  "codigo_padron": "001",
                  "socio_nombre": "PRUEBA DE CONEXION EPSON",
                  "documento": "12345678",
                  "codigo_parcela": "P01",
                  "sector": "CENTRO",
                  "total_sacos": 1,
                  "fecha_pesaje": "2026-08-09 00:00:00",
                  "bajadas": [{"destino": "MERCADO", "peso": 50.0}]
              }
                
              exito = ps.imprimir_recibo_dec(test_payload)
              
              if exito:
                  self.after(0, lambda: self.lbl_status_recibo.configure(text="✅ Impresión enviada con éxito", text_color="#16A34A"))
              else:
                  self.after(0, lambda: self.lbl_status_recibo.configure(text="❌ Error al enviar a la impresora", text_color="#DC2626"))
          except Exception as e:
              self.after(0, lambda: self.lbl_status_recibo.configure(text=f"❌ Error: {e}", text_color="#DC2626"))

      threading.Thread(target=_hilo_print, daemon=True).start()
  

  def _testear_impresora_etiqueta(self):
        impresora_nombre = self.cmb_imp_etiqueta.get().strip()
        if not impresora_nombre or impresora_nombre.startswith("SIN"):
            self.lbl_status_etiqueta.configure(text="⚠ Seleccione una impresora válida", text_color="#DC2626")
            return

        self.lbl_status_etiqueta.configure(text="Enviando etiqueta de prueba...", text_color="#D97706")

        def _hilo_print():
            try:
                from services.print_service import PrintService
                import uuid
                ps = PrintService()

                # Payload de prueba para la TSC TE200
                test_detail = {
                    "uuid": str(uuid.uuid4()),
                    "codigo_trazabilidad": "A126080501-1-P00001-M-1",
                    "destino": "MERCADO",
                    "fecha_pesaje": "10/08/2026 01:30"
                }

                exito = ps.imprimir_etiquetas_trazabilidad([test_detail], nombre_impresora_override=impresora_nombre)

                if exito:
                    self.after(0, lambda: self.lbl_status_etiqueta.configure(text="✅ Etiqueta enviada con éxito", text_color="#16A34A"))
                else:
                    self.after(0, lambda: self.lbl_status_etiqueta.configure(text="❌ Error al enviar a la impresora", text_color="#DC2626"))
            except Exception as e:
                self.after(0, lambda: self.lbl_status_etiqueta.configure(text=f"❌ Error: {e}", text_color="#DC2626"))

        threading.Thread(target=_hilo_print, daemon=True).start()