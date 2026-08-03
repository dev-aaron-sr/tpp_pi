import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

class AdminView(ctk.CTkFrame):
    def __init__(self, parent, recepcion_dao, sync_service):
        super().__init__(parent, fg_color="#DCE0E5")
        self.recepcion_dao = recepcion_dao
        self.sync_service = sync_service

        # Control de selección
        self.recibo_seleccionado_uuid = None
        self.filas_recibos = {}

        self._build_ui()

    def _build_ui(self):
        # ------------------------------------------------------------------
        # 1. ENCABEZADO SUPERIOR CON SELECTOR DE FECHA Y BOTÓN SYNC
        # ------------------------------------------------------------------
        self.top_panel = ctk.CTkFrame(self, fg_color="#D1D5DB", height=60)
        self.top_panel.pack(fill="x", padx=15, pady=(15, 10))
        self.top_panel.pack_propagate(False)

        ctk.CTkLabel(
            self.top_panel, 
            text="HISTORIAL Y SINCRONIZACIÓN", 
            font=("Segoe UI", 15, "bold"), 
            text_color="#000000"
        ).pack(side="left", padx=(15, 20))

        # Selector de Fecha (YYYY-MM-DD)
        ctk.CTkLabel(self.top_panel, text="Fecha:", font=("Segoe UI", 12, "bold"), text_color="#374151").pack(side="left", padx=(0, 5))
        self.txt_fecha_filtro = ctk.CTkEntry(
            self.top_panel,
            font=("Segoe UI", 12, "bold"),
            width=110,
            height=32,
            justify="center"
        )
        self.txt_fecha_filtro.pack(side="left", padx=(0, 10))
        self.txt_fecha_filtro.insert(0, datetime.now().strftime("%Y-%m-%d"))

        btn_filtrar = ctk.CTkButton(
            self.top_panel,
            text="🔍 FILTRAR",
            font=("Segoe UI", 11, "bold"),
            fg_color="#475569",
            hover_color="#334155",
            width=80,
            height=32,
            command=self.cargar_datos_locales
        )
        btn_filtrar.pack(side="left", padx=5)

        # Estado de la Sincronización
        self.lbl_sync_status = ctk.CTkLabel(
            self.top_panel,
            text="",
            font=("Segoe UI", 11, "italic"),
            text_color="#1E3A8A"
        )
        self.lbl_sync_status.pack(side="right", padx=(0, 15))

        # Botón Sincronizar
        self.btn_sync_now = ctk.CTkButton(
            self.top_panel, 
            text="🔄 SINCRONIZAR DATOS", 
            font=("Segoe UI", 12, "bold"),
            fg_color="#1E3A8A", 
            hover_color="#1E40AF",
            height=36,
            command=self._sincronizar
        )
        self.btn_sync_now.pack(side="right", padx=10)

        # ------------------------------------------------------------------
        # 2. CONTENEDOR DIVIDIDO REAJUSTABLE (PANED WINDOW 50% / 50%)
        # ------------------------------------------------------------------
        # Estilo para el divisor (Sash)
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TPanedwindow", background="#DCE0E5")

        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # ------------------------------------------------------------------
        # PANEL IZQUIERDO: RECIBOS DEL DÍA (MASTER)
        # ------------------------------------------------------------------
        self.frame_master = ctk.CTkFrame(self.paned, fg_color="#FFFFFF", border_width=1, border_color="#9CA3AF")
        self.paned.add(self.frame_master, weight=1)

        # Header Master
        title_master = ctk.CTkFrame(self.frame_master, fg_color="#F1F5F9", height=32)
        title_master.pack(fill="x", side="top")
        ctk.CTkLabel(title_master, text="📋 RECIBOS DE ENTREGA GENERADOS", font=("Segoe UI", 11, "bold"), text_color="#1E3A8A").pack(side="left", padx=10)

        headers_master = ctk.CTkFrame(self.frame_master, fg_color="#E2E8F0", height=32)
        headers_master.pack(fill="x", side="top")

        cols_master = [("Recibo", 95), ("Padrón / Socio", 150), ("Destino", 75), ("Sacos", 50), ("Peso Neto", 85), ("Estado", 85)]
        for col_name, width in cols_master:
            ctk.CTkLabel(headers_master, text=col_name, font=("Segoe UI", 10, "bold"), width=width, text_color="#000000", anchor="w" if "Socio" in col_name else "center").pack(side="left", padx=2)

        self.scroll_master = ctk.CTkScrollableFrame(self.frame_master, fg_color="transparent")
        self.scroll_master.pack(fill="both", expand=True)

        # ------------------------------------------------------------------
        # PANEL DERECHO: BAJADAS DE BALANZA (DETAIL)
        # ------------------------------------------------------------------
        self.frame_detail = ctk.CTkFrame(self.paned, fg_color="#FFFFFF", border_width=1, border_color="#9CA3AF")
        self.paned.add(self.frame_detail, weight=1)

        title_detail = ctk.CTkFrame(self.frame_detail, fg_color="#F1F5F9", height=32)
        title_detail.pack(fill="x", side="top")
        
        self.lbl_detail_title = ctk.CTkLabel(
            title_detail, 
            text="⚖️ BAJADAS DE BALANZA (SELECCIONE UN RECIBO A LA IZQUIERDA)", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#475569"
        )
        self.lbl_detail_title.pack(side="left", padx=10)

        headers_detail = ctk.CTkFrame(self.frame_detail, fg_color="#E2E8F0", height=32)
        headers_detail.pack(fill="x", side="top")

        cols_detail = [("N°", 40), ("Destino", 90), ("Sacos", 55), ("Peso Bruto", 85), ("Tara", 65), ("Peso Neto", 85)]
        for col_name, width in cols_detail:
            ctk.CTkLabel(headers_detail, text=col_name, font=("Segoe UI", 10, "bold"), width=width, text_color="#000000").pack(side="left", padx=2)

        self.scroll_detail = ctk.CTkScrollableFrame(self.frame_detail, fg_color="transparent")
        self.scroll_detail.pack(fill="both", expand=True)

        self.cargar_datos_locales()

    # ----------------------------------------------------------------------
    # CARGA Y FILTRADO DE DATOS
    # ----------------------------------------------------------------------
    def cargar_datos_locales(self):
        """Carga el historial de recibos según la fecha filtrada."""
        for widget in self.scroll_master.winfo_children():
            widget.destroy()

        self.filas_recibos.clear()
        self._limpiar_tabla_detalles()

        fecha_filtro = self.txt_fecha_filtro.get().strip()
        historial = self.recepcion_dao.obtener_historial_por_fecha(fecha_filtro)

        if not historial:
            row = ctk.CTkFrame(self.scroll_master, fg_color="transparent")
            row.pack(fill="x", pady=10)
            ctk.CTkLabel(row, text=f"No hay recibos registrados en la fecha {fecha_filtro}", font=("Segoe UI", 11, "italic"), text_color="#6B7280").pack()
            return

        for item in historial:
            rec_uuid = item['uuid']
            row = ctk.CTkFrame(self.scroll_master, fg_color="#F9FAFB", height=32, cursor="hand2")
            row.pack(fill="x", pady=1)

            self.filas_recibos[rec_uuid] = row

            lbl_ticket = ctk.CTkLabel(row, text=item['codigo_ticket'], width=95, font=("Segoe UI", 10, "bold"), text_color="#1E3A8A")
            lbl_ticket.pack(side="left", padx=2)

            socio_txt = f"{item['codigo_padron']} - {item.get('socio_nombre') or ''}".strip()
            lbl_socio = ctk.CTkLabel(row, text=socio_txt, width=150, font=("Segoe UI", 10), anchor="w", text_color="#111827")
            lbl_socio.pack(side="left", padx=2)

            lbl_dest = ctk.CTkLabel(row, text=item['destino'], width=75, font=("Segoe UI", 10, "bold"), text_color="#0284C7" if item['destino'] == "MERCADO" else "#D97706")
            lbl_dest.pack(side="left", padx=2)

            lbl_sacos = ctk.CTkLabel(row, text=str(item['total_sacos']), width=50, font=("Segoe UI", 10))
            lbl_sacos.pack(side="left", padx=2)

            lbl_peso = ctk.CTkLabel(row, text=f"{item['peso_neto_total']:.2f}kg", width=85, font=("Segoe UI", 10, "bold"))
            lbl_peso.pack(side="left", padx=2)

            estado_txt = "PENDIENTE" if item['sincronizado'] == 0 else "SYNC"
            color_txt = "#D97706" if item['sincronizado'] == 0 else "#16A34A"
            lbl_estado = ctk.CTkLabel(row, text=estado_txt, width=85, font=("Segoe UI", 9, "bold"), text_color=color_txt)
            lbl_estado.pack(side="left", padx=2)

            # Eventos de Selección
            for w in (row, lbl_ticket, lbl_socio, lbl_dest, lbl_sacos, lbl_peso, lbl_estado):
                w.bind("<Button-1>", lambda e, r=item: self._seleccionar_recibo(r))

    def _seleccionar_recibo(self, recibo_data: dict):
        """Carga las bajadas de balanza del recibo seleccionado en la tabla derecha."""
        self.recibo_seleccionado_uuid = recibo_data['uuid']

        # Resaltar fila activa
        for uid, frame in self.filas_recibos.items():
            if uid == self.recibo_seleccionado_uuid:
                frame.configure(fg_color="#DBEAFE")
            else:
                frame.configure(fg_color="#F9FAFB")

        self.lbl_detail_title.configure(
            text=f"BAJADAS - {recibo_data['codigo_ticket']} | SOCIO: {recibo_data['codigo_padron']}",
            text_color="#1E3A8A"
        )

        self._cargar_detalles_recibo(self.recibo_seleccionado_uuid)

    def _cargar_detalles_recibo(self, recepcion_uuid: str):
        self._limpiar_tabla_detalles()

        detalles = self.recepcion_dao.obtener_detalles_por_recepcion_uuid(recepcion_uuid)

        for d in detalles:
            row = ctk.CTkFrame(self.scroll_detail, fg_color="#F8FAFC", height=28)
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(row, text=f"#{d['orden']}", width=40, font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)
            
            dest_color = "#0284C7" if d.get('destino') == "MERCADO" else "#D97706"
            ctk.CTkLabel(row, text=d.get('destino', 'MERCADO'), width=90, font=("Segoe UI", 10, "bold"), text_color=dest_color).pack(side="left", padx=2)

            ctk.CTkLabel(row, text=str(d['numero_sacos']), width=55, font=("Segoe UI", 10)).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"{d['peso_bruto']:.2f}kg", width=85, font=("Segoe UI", 10)).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"{d['tara']:.2f}kg", width=65, font=("Segoe UI", 10)).pack(side="left", padx=2)
            ctk.CTkLabel(row, text=f"{d['peso_neto']:.2f}kg", width=85, font=("Segoe UI", 10, "bold")).pack(side="left", padx=2)

    def _limpiar_tabla_detalles(self):
        for widget in self.scroll_detail.winfo_children():
            widget.destroy()

    # ----------------------------------------------------------------------
    # SINCRONIZACIÓN ASÍNCRONA CON FEEDBACK VISUAL
    # ----------------------------------------------------------------------
    def _sincronizar(self):
        """Inicia el proceso de envío en segundo plano."""
        self.btn_sync_now.configure(state="disabled", text="⏳ SINCRONIZANDO...")
        self.lbl_sync_status.configure(text="Conectando con Laravel...", text_color="#1E3A8A")

        threading.Thread(target=self._hilo_sincronizacion, daemon=True).start()

    def _hilo_sincronizacion(self):
        subidos = self.sync_service.subir_pesajes_pendientes()
        maestros_ok = self.sync_service.descargar_maestros()

        self.after(0, lambda: self._finalizar_sincronizacion(subidos, maestros_ok))

    def _finalizar_sincronizacion(self, subidos: int, maestros_ok: bool):
        self.btn_sync_now.configure(state="normal", text="🔄 SINCRONIZAR DATOS")

        if subidos > 0 or maestros_ok:
            msg = f"✅ Sincronización exitosa ({subidos} recibos enviados)."
            self.lbl_sync_status.configure(text=msg, text_color="#16A34A")
        else:
            self.lbl_sync_status.configure(text="ℹ️ No hay datos pendientes o sin conexión.", text_color="#D97706")

        self.cargar_datos_locales()