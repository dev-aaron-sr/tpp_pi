import customtkinter as ctk
from typing import Dict, List, Optional
import uuid

class PesajeView(ctk.CTkFrame):
    def __init__(self, parent, agricultor_dao, recepcion_dao, scale_service, print_service):
        # Color base gris industrial (RAL 7035 / HMI Standard)
        super().__init__(parent, fg_color="#C0C0C0", corner_radius=0)

        self.agricultor_dao = agricultor_dao
        self.recepcion_dao = recepcion_dao
        self.scale_service = scale_service
        self.print_service = print_service

        # Estado del pesaje en curso
        self.agricultor_actual: Optional[Dict] = None
        self.parcela_actual: Optional[str] = None
        self.destino_actual = "MERCADO"
        
        # Almacenamiento local de bajadas por destino
        self.pesadas = {
            "MERCADO": [],
            "FABRICA": [],
            "EXPORTACION": []
        }

        self._build_ui()
        self._bind_shortcuts()

    def _build_ui(self):
        # ---------------------------------------------------------------------
        # PANEL IZQUIERDO: SOCIO, PARCELA Y TOTALES (Ancho: 380px, Borde Rígido)
        # ---------------------------------------------------------------------
        self.panel_left = ctk.CTkFrame(
            self, 
            fg_color="#D4D4D4", 
            border_width=2, 
            border_color="#808080", 
            width=380, 
            corner_radius=0
        )
        self.panel_left.pack(side="left", fill="y", padx=5, pady=5)
        self.panel_left.pack_propagate(False)

        # Encabezado
        ctk.CTkLabel(
            self.panel_left, 
            text="DATOS DE AGRICULTOR", 
            font=("Arial", 22, "bold"), 
            text_color="#000000"
        ).pack(anchor="w", padx=12, pady=(12, 4))

        # Código Padrón
        ctk.CTkLabel(
            self.panel_left, 
            text="Código padrón:", 
            font=("Arial", 20, "bold"), 
            text_color="#000000"
        ).pack(anchor="w", padx=12, pady=(8, 2))
        
        self.txt_padron = ctk.CTkEntry(
            self.panel_left, 
            font=("Arial", 22, "bold"), 
            fg_color="#FFFFFF", 
            text_color="#000000", 
            border_color="#000000",
            border_width=2,
            corner_radius=0,
            height=46
        )
        self.txt_padron.pack(fill="x", padx=12, pady=(0, 10))

        # Información del Socio
        ctk.CTkLabel(self.panel_left, text="Socio:", font=("Arial", 20, "bold"), text_color="#000000").pack(anchor="w", padx=12)
        self.lbl_socio_nombre = ctk.CTkLabel(
            self.panel_left, 
            text="-", 
            font=("Arial", 20, "bold"), 
            text_color="#1E293B", 
            wraplength=340, 
            justify="left"
        )
        self.lbl_socio_nombre.pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkLabel(self.panel_left, text="DNI/RUC:", font=("Arial", 20, "bold"), text_color="#000000").pack(anchor="w", padx=12)
        self.lbl_socio_doc = ctk.CTkLabel(self.panel_left, text="-", font=("Arial", 20, "bold"), text_color="#000000")
        self.lbl_socio_doc.pack(anchor="w", padx=12, pady=(0, 10))

        # Selector de Parcela
        ctk.CTkLabel(self.panel_left, text="Parcela:", font=("Arial", 20, "bold"), text_color="#000000").pack(anchor="w", padx=12)
        self.cmb_parcela = ctk.CTkOptionMenu(
            self.panel_left, 
            values=["---"], 
            fg_color="#FFFFFF", 
            text_color="#000000", 
            button_color="#808080",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#000000",
            corner_radius=0,
            height=42, 
            font=("Arial", 18, "bold")
        )
        self.cmb_parcela.pack(fill="x", padx=12, pady=(0, 12))

        # Divisor
        ctk.CTkFrame(self.panel_left, height=2, fg_color="#000000", corner_radius=0).pack(fill="x", padx=5, pady=5)

        # Totales por Destino
        ctk.CTkLabel(self.panel_left, text="TOTALES ACUMULADOS", font=("Arial", 22, "bold"), text_color="#000000").pack(anchor="w", padx=12, pady=5)
        
        frame_tot_m = ctk.CTkFrame(self.panel_left, fg_color="transparent")
        frame_tot_m.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(frame_tot_m, text="Mercado:", font=("Arial", 20, "bold"), text_color="#000000").pack(side="left")
        self.lbl_tot_mercado = ctk.CTkLabel(frame_tot_m, text="0.00kg", font=("Arial", 28, "bold"), text_color="#000000")
        self.lbl_tot_mercado.pack(side="right")

        frame_tot_f = ctk.CTkFrame(self.panel_left, fg_color="transparent")
        frame_tot_f.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(frame_tot_f, text="Fábrica:", font=("Arial", 20, "bold"), text_color="#000000").pack(side="left")
        self.lbl_tot_fabrica = ctk.CTkLabel(frame_tot_f, text="0.00kg", font=("Arial", 28, "bold"), text_color="#000000")
        self.lbl_tot_fabrica.pack(side="right")

        ctk.CTkFrame(self.panel_left, height=2, fg_color="#000000", corner_radius=0).pack(fill="x", padx=5, pady=10)

        # Botón Verde Gigante: FINALIZAR PESAJE
        self.btn_finalizar = ctk.CTkButton(
            self.panel_left, 
            text="FINALIZAR PESAJE\nSOCIO", 
            font=("Arial", 22, "bold"), 
            fg_color="#15803D", 
            hover_color="#166534",
            text_color="#FFFFFF",
            corner_radius=0,
            height=70,
            command=self._finalizar_pesaje_socio
        )
        self.btn_finalizar.pack(fill="x", side="bottom", padx=12, pady=12)

        # ---------------------------------------------------------------------
        # PANEL CENTRAL: BOTONES DE DESTINO, VISOR LCD, TABLAS Y PANEL OPERATIVO
        # ---------------------------------------------------------------------
        self.panel_center = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_center.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Selector de Destinos (F1, F2, F3)
        self.frame_tabs = ctk.CTkFrame(self.panel_center, fg_color="transparent", height=45)
        self.frame_tabs.pack(fill="x", side="top", pady=(0, 6))

        self.btn_f1 = ctk.CTkButton(
            self.frame_tabs, text="MERCADO [F1]", font=("Arial", 16, "bold"), 
            fg_color="#0284C7", hover_color="#0369A1", text_color="#FFFFFF", corner_radius=0, width=170, height=42,
            command=lambda: self._set_destino("MERCADO")
        )
        self.btn_f1.pack(side="left", padx=(0, 6))

        self.btn_f2 = ctk.CTkButton(
            self.frame_tabs, text="FÁBRICA [F2]", font=("Arial", 16, "bold"), 
            fg_color="#D97706", hover_color="#B45309", text_color="#FFFFFF", corner_radius=0, width=170, height=42,
            command=lambda: self._set_destino("FABRICA")
        )
        self.btn_f2.pack(side="left", padx=6)

        self.btn_f3 = ctk.CTkButton(
            self.frame_tabs, text="EXPORTACIÓN [F3]", font=("Arial", 16, "bold"), 
            fg_color="#059669", hover_color="#047857", text_color="#FFFFFF", corner_radius=0, width=190, height=42,
            command=lambda: self._set_destino("EXPORTACION")
        )
        self.btn_f3.pack(side="left", padx=6)

        # Visor Gigante de Peso
        self.frame_visor = ctk.CTkFrame(self.panel_center, fg_color="#000000", height=230, corner_radius=0, border_width=2, border_color="#808080")
        self.frame_visor.pack(fill="x", side="top", pady=(0, 8))
        self.frame_visor.pack_propagate(False)

        self.lbl_unit = ctk.CTkLabel(self.frame_visor, text="kg", font=("Arial", 40, "bold"), text_color="#00FF00")
        self.lbl_unit.pack(side="right", padx=(0, 20), pady=(40, 0))

        self.lbl_peso = ctk.CTkLabel(self.frame_visor, text="128.00", font=("Consolas", 180, "bold"), text_color="#00FF00")
        self.lbl_peso.pack(side="right", padx=(0, 10))

        # --- CONTENEDOR INFERIOR: TABLAS (IZQ) Y CONTROLES OPERATIVOS (DER) ---
        self.frame_bottom_grid = ctk.CTkFrame(self.panel_center, fg_color="transparent")
        self.frame_bottom_grid.pack(fill="both", expand=True)

        # Grilla de Tablas (MERCADO y FÁBRICA)
        self.frame_tables = ctk.CTkFrame(self.frame_bottom_grid, fg_color="transparent")
        self.frame_tables.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.panel_tabla_mercado = self._crear_estructura_tabla("MERCADO", self.frame_tables)
        self.panel_tabla_fabrica = self._crear_estructura_tabla("FABRICA", self.frame_tables)

        # Panel Operativo Derecho (Ubicado DEBAJO de la balanza, al lado de las tablas)
        self.panel_right = ctk.CTkFrame(self.frame_bottom_grid, fg_color="#D4D4D4", border_width=2, border_color="#808080", width=200, corner_radius=0)
        self.panel_right.pack(side="right", fill="y")
        self.panel_right.pack_propagate(False)

        ctk.CTkLabel(self.panel_right, text="Cant. de sacos", font=("Arial", 20, "bold"), text_color="#000000").pack(pady=(12, 4))
        self.txt_sacos = ctk.CTkEntry(
            self.panel_right, 
            font=("Arial", 30, "bold"), 
            justify="center", 
            fg_color="#FFFFFF", 
            text_color="#000000", 
            border_color="#000000",
            border_width=2,
            corner_radius=0,
            height=50
        )
        self.txt_sacos.pack(fill="x", padx=10, pady=(0, 12))
        self.txt_sacos.insert(0, "1")

        self.btn_registrar = ctk.CTkButton(
            self.panel_right, 
            text="REGISTRAR\n[ENTER]", 
            font=("Arial", 16, "bold"), 
            fg_color="#0284C7", 
            hover_color="#0369A1", 
            text_color="#FFFFFF",
            corner_radius=0,
            height=60, 
            command=self._registrar_bajada
        )
        self.btn_registrar.pack(fill="x", padx=10, pady=5)

        self.btn_eliminar = ctk.CTkButton(
            self.panel_right, 
            text="ELIMINAR\nÚLTIMO", 
            font=("Arial", 15, "bold"), 
            fg_color="#DC2626", 
            hover_color="#B91C1C", 
            text_color="#FFFFFF",
            corner_radius=0,
            height=52, 
            command=self._eliminar_ultimo
        )
        self.btn_eliminar.pack(fill="x", padx=10, pady=5)

        self.btn_reiniciar = ctk.CTkButton(
            self.panel_right, 
            text="REINICIAR\nPESAJE", 
            font=("Arial", 16, "bold"), 
            fg_color="#991B1B", 
            hover_color="#7F1D1D", 
            text_color="#FFFFFF",
            corner_radius=0,
            height=60, 
            command=self._reiniciar_pesaje
        )
        self.btn_reiniciar.pack(fill="x", side="bottom", padx=10, pady=10)

    def _crear_estructura_tabla(self, nombre_destino: str, contenedor_padre) -> Dict:
        """Construye el contenedor con cabecera fija, cuerpo dinámico y totales."""
        box = ctk.CTkFrame(contenedor_padre, fg_color="#FFFFFF", border_width=1, border_color="#000000", corner_radius=0)
        box.pack(side="left", fill="both", expand=True, padx=2)

        # Encabezado Destino
        lbl_header = ctk.CTkLabel(box, text=nombre_destino, font=("Arial", 18, "bold"), fg_color="#0055AA", text_color="#FFFFFF", height=36, corner_radius=0)
        lbl_header.pack(fill="x", side="top")

        # Subencabezados
        sub_head = ctk.CTkFrame(box, fg_color="#E2E8F0", height=30, corner_radius=0)
        sub_head.pack(fill="x", side="top")

        ctk.CTkLabel(sub_head, text="Peso", font=("Arial", 16, "bold"), text_color="#000000", width=110).pack(side="left", padx=5)
        ctk.CTkLabel(sub_head, text="Sacos", font=("Arial", 16, "bold"), text_color="#000000", width=60).pack(side="left", padx=5)
        ctk.CTkLabel(sub_head, text="", width=30).pack(side="right")

        # Área Scrollable
        scroll = ctk.CTkScrollableFrame(box, fg_color="#FFFFFF", corner_radius=0)
        scroll.pack(fill="both", expand=True)

        # Footer con totales
        footer = ctk.CTkFrame(box, fg_color="#E2E8F0", height=34, corner_radius=0, border_width=1, border_color="#94A3B8")
        footer.pack(fill="x", side="bottom")

        lbl_tot_peso = ctk.CTkLabel(footer, text="0.00 kg", font=("Arial", 18, "bold"), text_color="#000000", width=110)
        lbl_tot_peso.pack(side="left", padx=5)

        lbl_tot_sacos = ctk.CTkLabel(footer, text="0", font=("Arial", 18, "bold"), text_color="#000000", width=60)
        lbl_tot_sacos.pack(side="left", padx=5)

        ctk.CTkLabel(footer, text="total", font=("Arial", 16, "bold"), text_color="#000000").pack(side="right", padx=10)

        return {
            "header": lbl_header,
            "scroll": scroll,
            "lbl_peso": lbl_tot_peso,
            "lbl_sacos": lbl_tot_sacos
        }

    # ---------------------------------------------------------------------
    # LÓGICA Y TECLAS DE ACCESO RÁPIDO
    # ---------------------------------------------------------------------
    def _bind_shortcuts(self):
        self.txt_padron.bind("<Return>", lambda e: self._buscar_socio())
        self.txt_sacos.bind("<Return>", lambda e: self._registrar_bajada())

    def _set_destino(self, destino: str):
        self.destino_actual = destino

    def _flash_header(self, destino: str):
        """Genera un destello amarillo suave en la cabecera del destino para confirmar la entrada sin parpadeos."""
        panel = self.panel_tabla_mercado if destino == "MERCADO" else self.panel_tabla_fabrica
        lbl_header = panel["header"]
        color_original = "#0055AA"
        amarillo_suave = "#FACC15"

        lbl_header.configure(fg_color=amarillo_suave, text_color="#000000")
        self.after(250, lambda: lbl_header.configure(fg_color=color_original, text_color="#FFFFFF"))

    def _buscar_socio(self):
        padron = self.txt_padron.get().strip()
        if not padron:
            return

        ag = self.agricultor_dao.buscar_por_padron(padron)
        if ag:
            self.agricultor_actual = ag
            nombre = f"{ag['nombres']} {ag.get('apellidos', '')}".strip()
            self.lbl_socio_nombre.configure(text=nombre, text_color="#000000")
            self.lbl_socio_doc.configure(text=ag.get('numero_documento') or 'NO REGISTRADO')

            parcelas = [p['codigo_parcela'] for p in ag.get('parcelas', [])]
            if parcelas:
                self.cmb_parcela.configure(values=parcelas)
                self.cmb_parcela.set(parcelas[0])
            self.txt_sacos.focus_set()
            self.txt_sacos.select_range(0, 'end')
        else:
            self.lbl_socio_nombre.configure(text="❌ NO ENCONTRADO", text_color="#DC2626")
            self.lbl_socio_doc.configure(text="-")
            self.agricultor_actual = None

    def _registrar_bajada(self):
        try:
            peso_actual = float(self.lbl_peso.cget("text"))
            num_sacos = int(self.txt_sacos.get().strip())
        except ValueError:
            return

        if peso_actual <= 0 or num_sacos <= 0:
            return

        item = {
            "uuid": str(uuid.uuid4()),
            "peso": peso_actual,
            "sacos": num_sacos
        }

        dest = self.destino_actual if self.destino_actual in self.pesadas else "MERCADO"
        self.pesadas[dest].append(item)

        # Anexar fila directamente sin reconstruir la interfaz (Flicker-Free)
        if dest in ["MERCADO", "FABRICA"]:
            idx = len(self.pesadas[dest]) - 1
            self._agregar_fila_ui(dest, item, idx)
            self._actualizar_totales()
            self._flash_header(dest)

        self.txt_sacos.focus_set()
        self.txt_sacos.select_range(0, 'end')

    def _agregar_fila_ui(self, dest: str, item: Dict, idx: int):
        """Agrega una nueva fila al DOM de la tabla correspondiente sin renderizar todo nuevamente."""
        panel = self.panel_tabla_mercado if dest == "MERCADO" else self.panel_tabla_fabrica
        scroll = panel["scroll"]

        row = ctk.CTkFrame(scroll, fg_color="#F8FAFC", height=32, corner_radius=0)
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=f"{item['peso']:.2f} kg", font=("Arial", 16, "bold"), text_color="#000000", width=110).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=str(item['sacos']), font=("Arial", 16, "bold"), text_color="#000000", width=60).pack(side="left", padx=5)

        btn_del = ctk.CTkButton(
            row, text="✕", font=("Arial", 14, "bold"), fg_color="#EF4444", hover_color="#B91C1C", text_color="#FFFFFF",
            width=28, height=24, corner_radius=0,
            command=lambda d=dest, i=idx: self._eliminar_bajada_especifica(d, i)
        )
        btn_del.pack(side="right", padx=5)

    def _actualizar_totales(self):
        """Recalcula y actualiza los indicadores de totales en pantalla."""
        for dest, panel in [("MERCADO", self.panel_tabla_mercado), ("FABRICA", self.panel_tabla_fabrica)]:
            tot_peso = sum(x["peso"] for x in self.pesadas[dest])
            tot_sacos = sum(x["sacos"] for x in self.pesadas[dest])
            panel["lbl_peso"].configure(text=f"{tot_peso:.2f} kg")
            panel["lbl_sacos"].configure(text=str(tot_sacos))

        tot_m = sum(x["peso"] for x in self.pesadas["MERCADO"])
        tot_f = sum(x["peso"] for x in self.pesadas["FABRICA"])

        self.lbl_tot_mercado.configure(text=f"{tot_m:.2f}kg")
        self.lbl_tot_fabrica.configure(text=f"{tot_f:.2f}kg")

    def _eliminar_bajada_especifica(self, destino: str, index: int):
        if 0 <= index < len(self.pesadas[destino]):
            self.pesadas[destino].pop(index)
            self._renderizar_tablas()

    def _eliminar_ultimo(self):
        dest = self.destino_actual if self.destino_actual in self.pesadas else "MERCADO"
        if self.pesadas[dest]:
            self.pesadas[dest].pop()
            self._renderizar_tablas()

    def _renderizar_tablas(self):
        """Reconstruye las listas únicamente cuando se elimina un elemento o se reinicia la sesión."""
        for dest, panel in [("MERCADO", self.panel_tabla_mercado), ("FABRICA", self.panel_tabla_fabrica)]:
            scroll = panel["scroll"]
            for widget in scroll.winfo_children():
                widget.destroy()

            for idx, item in enumerate(self.pesadas[dest]):
                self._agregar_fila_ui(dest, item, idx)

        self._actualizar_totales()

    def _reiniciar_pesaje(self):
        self.pesadas = {"MERCADO": [], "FABRICA": [], "EXPORTACION": []}
        self.txt_padron.delete(0, 'end')
        self.lbl_socio_nombre.configure(text="-", text_color="#1E293B")
        self.lbl_socio_doc.configure(text="-")
        self.cmb_parcela.configure(values=["---"])
        self.cmb_parcela.set("---")
        self.agricultor_actual = None
        self._renderizar_tablas()
        self.txt_padron.focus_set()

    def _finalizar_pesaje_socio(self):
        if not self.agricultor_actual:
            return
        
        # Guarda las transacciones locales e imprime tickets/etiquetas
        self._reiniciar_pesaje()