import threading
import customtkinter as ctk

class PadronView(ctk.CTkFrame):
    def __init__(self, parent, agricultor_dao, sync_service):
        super().__init__(parent, fg_color="#DCE0E5")
        self.agricultor_dao = agricultor_dao
        self.sync_service = sync_service

        # Control de selección
        self.agricultor_seleccionado_id = None
        self.filas_agricultores = {}  # {id_agricultor: frame_widget}

        self._build_ui()
        self.cargar_agricultores()

    def _build_ui(self):
        # ------------------------------------------------------------------
        # 1. ENCABEZADO SUPERIOR
        # ------------------------------------------------------------------
        self.top_panel = ctk.CTkFrame(self, fg_color="#D1D5DB", height=60)
        self.top_panel.pack(fill="x", padx=15, pady=(15, 10))
        self.top_panel.pack_propagate(False)

        ctk.CTkLabel(
            self.top_panel, 
            text="PADRÓN DE AGRICULTORES Y PARCELAS (SOLO LECTURA)", 
            font=("Segoe UI", 16, "bold"), 
            text_color="#000000"
        ).pack(side="left", padx=15)

        # Indicador de estado de sincronización
        self.lbl_status = ctk.CTkLabel(
            self.top_panel,
            text="",
            font=("Segoe UI", 12, "italic"),
            text_color="#1E3A8A"
        )
        self.lbl_status.pack(side="right", padx=(0, 15))

        # Botón de Sincronización
        self.btn_sync_maestros = ctk.CTkButton(
            self.top_panel, 
            text="🔄 SINCRONIZAR MAESTROS", 
            font=("Segoe UI", 13, "bold"),
            fg_color="#1E3A8A", 
            hover_color="#1E40AF",
            height=40,
            command=self._sincronizar_maestros
        )
        self.btn_sync_maestros.pack(side="right", padx=10)

        # ------------------------------------------------------------------
        # 2. CONTENEDOR PRINCIPAL SPLIT (IZQUIERDA Y DERECHA)
        # ------------------------------------------------------------------
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Grid de 2 columnas con igual peso (50% / 50%)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # ------------------------------------------------------------------
        # PANEL IZQUIERDO: AGRICULTORES (MASTER)
        # ------------------------------------------------------------------
        self.panel_left = ctk.CTkFrame(self.main_container, fg_color="#FFFFFF", border_width=1, border_color="#9CA3AF")
        self.panel_left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Barra de Búsqueda de Agricultores
        search_frame = ctk.CTkFrame(self.panel_left, fg_color="#F3F4F6", height=45)
        search_frame.pack(fill="x", side="top")
        search_frame.pack_propagate(False)

        ctk.CTkLabel(search_frame, text="🔍", font=("Segoe UI", 14)).pack(side="left", padx=(10, 2))
        self.txt_buscar = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Buscar por Cód. Padrón o Nombre...",
            font=("Segoe UI", 11),
            fg_color="#FFFFFF",
            border_color="#D1D5DB",
            height=30
        )
        self.txt_buscar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.txt_buscar.bind("<KeyRelease>", self._filtrar_agricultores)

        # Cabecera Tabla Agricultores
        headers_agri = ctk.CTkFrame(self.panel_left, fg_color="#E5E7EB", height=35)
        headers_agri.pack(fill="x", side="top")
        
        ctk.CTkLabel(headers_agri, text="Padrón", width=90, font=("Segoe UI", 12, "bold"), text_color="#000000").pack(side="left", padx=5)
        ctk.CTkLabel(headers_agri, text="Nombres y Apellidos", width=220, font=("Segoe UI", 12, "bold"), text_color="#000000", anchor="w").pack(side="left", padx=5)

        # Lista con Scroll
        self.scroll_agricultores = ctk.CTkScrollableFrame(self.panel_left, fg_color="transparent")
        self.scroll_agricultores.pack(fill="both", expand=True)

        # ------------------------------------------------------------------
        # PANEL DERECHO: PARCELAS (DETAIL)
        # ------------------------------------------------------------------
        self.panel_right = ctk.CTkFrame(self.main_container, fg_color="#FFFFFF", border_width=1, border_color="#9CA3AF")
        self.panel_right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Título Dinámico del Agricultor Seleccionado
        title_detail_frame = ctk.CTkFrame(self.panel_right, fg_color="#F3F4F6", height=45)
        title_detail_frame.pack(fill="x", side="top")
        title_detail_frame.pack_propagate(False)

        self.lbl_agri_seleccionado = ctk.CTkLabel(
            title_detail_frame, 
            text="SELECCIONE UN AGRICULTOR PARA VER SUS PARCELAS", 
            font=("Segoe UI", 12, "bold"), 
            text_color="#4B5563"
        )
        self.lbl_agri_seleccionado.pack(side="left", padx=10)

        # Cabecera Tabla Parcelas
        headers_parcelas = ctk.CTkFrame(self.panel_right, fg_color="#E5E7EB", height=35)
        headers_parcelas.pack(fill="x", side="top")

        ctk.CTkLabel(headers_parcelas, text="Cód. Parcela", width=100, font=("Segoe UI", 12, "bold"), text_color="#000000").pack(side="left", padx=5)
        ctk.CTkLabel(headers_parcelas, text="Nombre Parcela", width=150, font=("Segoe UI", 12, "bold"), text_color="#000000", anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_parcelas, text="Sector", width=100, font=("Segoe UI", 12, "bold"), text_color="#000000", anchor="w").pack(side="left", padx=5)

        # Lista con Scroll de Parcelas
        self.scroll_parcelas = ctk.CTkScrollableFrame(self.panel_right, fg_color="transparent")
        self.scroll_parcelas.pack(fill="both", expand=True)

    # ----------------------------------------------------------------------
    # LÓGICA Y MÉTODOS DE DATOS
    # ----------------------------------------------------------------------
    def cargar_agricultores(self, filtro: str = ""):
        """Carga los agricultores locales desde SQLite."""
        for widget in self.scroll_agricultores.winfo_children():
            widget.destroy()

        self.filas_agricultores.clear()
        agricultores = self.agricultor_dao.obtener_todos()  # O método equivalente en tu DAO

        filtro = filtro.lower().strip()

        for item in agricultores:
            nombre_completo = f"{item.get('nombres', '')} {item.get('apellidos', '')}".strip()
            padron = item.get('codigo_padron', '')

            # Aplicar Filtro de búsqueda
            if filtro and (filtro not in nombre_completo.lower() and filtro not in padron.lower()):
                continue

            row = ctk.CTkFrame(self.scroll_agricultores, fg_color="#F9FAFB", height=35, cursor="hand2")
            row.pack(fill="x", pady=2)

            # Guardar referencia para resaltar selección
            agri_id = item.get('id')
            self.filas_agricultores[agri_id] = row

            lbl_padron = ctk.CTkLabel(row, text=padron, width=90, font=("Segoe UI", 11, "bold"), text_color="#1E3A8A")
            lbl_padron.pack(side="left", padx=5)

            lbl_nombre = ctk.CTkLabel(row, text=nombre_completo, width=220, font=("Segoe UI", 11), anchor="w", text_color="#111827")
            lbl_nombre.pack(side="left", padx=5)

            # Eventos de clic para seleccionar (en el row y en sus labels)
            for widget in (row, lbl_padron, lbl_nombre):
                widget.bind("<Button-1>", lambda e, a=item: self._seleccionar_agricultor(a))

    def _seleccionar_agricultor(self, agricultor_data: dict):
        """Maneja la selección de un agricultor y despliega sus parcelas."""
        self.agricultor_seleccionado_id = agricultor_data.get('id')

        # Resaltar la fila seleccionada y restaurar las demás
        for agri_id, frame in self.filas_agricultores.items():
            if agri_id == self.agricultor_seleccionado_id:
                frame.configure(fg_color="#DBEAFE")  # Azul claro seleccionado
            else:
                frame.configure(fg_color="#F9FAFB")  # Fondo normal

        # Actualizar Título del Panel de Parcelas
        nombre_completo = f"{agricultor_data.get('nombres', '')} {agricultor_data.get('apellidos', '')}".strip()
        self.lbl_agri_seleccionado.configure(
            text=f"PARCELAS DE: {nombre_completo.upper()} ({agricultor_data.get('codigo_padron')})",
            text_color="#1E3A8A"
        )

        # Cargar Parcelas asociadas
        self._cargar_parcelas_de_agricultor(agricultor_data.get('id'))

    def _cargar_parcelas_de_agricultor(self, agricultor_id: int):
        """Limpia y lista las parcelas del agricultor seleccionado."""
        for widget in self.scroll_parcelas.winfo_children():
            widget.destroy()

        parcelas = self.agricultor_dao.obtener_parcelas_por_agricultor(agricultor_id)

        if not parcelas:
            row = ctk.CTkFrame(self.scroll_parcelas, fg_color="transparent")
            row.pack(fill="x", pady=10)
            ctk.CTkLabel(row, text="Este agricultor no tiene parcelas registradas.", font=("Segoe UI", 11, "italic"), text_color="#6B7280").pack()
            return

        for p in parcelas:
            row = ctk.CTkFrame(self.scroll_parcelas, fg_color="#F9FAFB", height=30)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=p.get('codigo_parcela', ''), width=100, font=("Segoe UI", 11, "bold"), text_color="#059669").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=p.get('nombre_parcela', ''), width=150, font=("Segoe UI", 11), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=p.get('sector', '-') or '-', width=100, font=("Segoe UI", 11), anchor="w", text_color="#4B5563").pack(side="left", padx=5)

    def _filtrar_agricultores(self, event=None):
        """Filtra la lista según lo digitado en la caja de texto."""
        texto = self.txt_buscar.get()
        self.cargar_agricultores(filtro=texto)

    # ----------------------------------------------------------------------
    # SINCRONIZACIÓN ASÍNCRONA (SIN BLOQUEAR LA UI)
    # ----------------------------------------------------------------------
    def _sincronizar_maestros(self):
        """Inicia el proceso de sincronización en un hilo secundario."""
        self.btn_sync_maestros.configure(state="disabled", text="⏳ SINCRONIZANDO...")
        self.lbl_status.configure(text="Conectando con el servidor Laravel...")

        # Ejecutar en segundo plano
        threading.Thread(target=self._hilo_sincronizacion, daemon=True).start()

    def _hilo_sincronizacion(self):
        """Función ejecutada fuera del hilo principal de UI."""
        exito = self.sync_service.descargar_maestros()

        # Retornar al hilo principal de CustomTkinter para actualizar widgets
        self.after(0, lambda: self._finalizar_sincronizacion(exito))

    def _finalizar_sincronizacion(self, exito: bool):
        """Restaura el botón y recarga los datos recién descargados."""
        self.btn_sync_maestros.configure(state="normal", text="🔄 SINCRONIZAR MAESTROS")

        if exito:
            self.lbl_status.configure(text="✓ Maestros actualizados correctamente.", text_color="#16A34A")
            self.cargar_agricultores()
            
            # Limpiar panel de parcelas derecho
            for widget in self.scroll_parcelas.winfo_children():
                widget.destroy()
            self.lbl_agri_seleccionado.configure(text="SELECCIONE UN AGRICULTOR PARA VER SUS PARCELAS", text_color="#4B5563")
        else:
            self.lbl_status.configure(text="⚠ Error de conexión con el servidor.", text_color="#DC2626")