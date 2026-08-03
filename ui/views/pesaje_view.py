from datetime import datetime
import customtkinter as ctk
from typing import Dict, List, Optional
import uuid
from decimal import Decimal, InvalidOperation, ROUND_FLOOR

class PesajeView(ctk.CTkFrame):
    def __init__(self, parent, agricultor_dao, recepcion_dao, sesion_dao, scale_service, print_service, sesion_activa, on_cerrar_sesion_cb):
        super().__init__(parent, fg_color="#CBD5E1", corner_radius=0)

        self.agricultor_dao = agricultor_dao
        self.recepcion_dao = recepcion_dao
        self.sesion_dao = sesion_dao
        self.scale_service = scale_service
        self.print_service = print_service
        self.sesion_activa = sesion_activa
        self.on_cerrar_sesion_cb = on_cerrar_sesion_cb

        # Estado local
        self.agricultor_actual: Optional[Dict] = None
        self.destino_actual = "MERCADO"
        self.pesadas = {"MERCADO": [], "FABRICA": []}
        self.filas_ui = {"MERCADO": {}, "FABRICA": {}}

        self._build_ui()
        self._bind_shortcuts()
        self._iniciar_lectura_balanza()

    def _build_ui(self):
        # ---------------------------------------------------------------------
        # BARRA SUPERIOR INFORMATIVA DE SESIÓN
        # ---------------------------------------------------------------------
        self.top_session_bar = ctk.CTkFrame(self, fg_color="#1E293B", height=40, corner_radius=0)
        self.top_session_bar.pack(fill="x", side="top")
        self.top_session_bar.pack_propagate(False)

        cod_sesion = self.sesion_activa.get('codigo_sesion', 'S/N')
        f_apertura = self.sesion_activa.get('fecha_apertura', '')

        ctk.CTkLabel(
            self.top_session_bar,
            text=f"🟢 SESIÓN ACTIVA: {cod_sesion} | Inicio: {f_apertura}",
            font=("Segoe UI", 12, "bold"),
            text_color="#4ADE80"
        ).pack(side="left", padx=15)

        ctk.CTkButton(
            self.top_session_bar,
            text="🔒 CERRAR JORNADA",
            font=("Segoe UI", 11, "bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            width=130,
            height=28,
            command=self._ejecutar_cierre_jornada
        ).pack(side="right", padx=15)


        # ---------------------------------------------------------------------
        # PANEL IZQUIERDO: AGRICULTOR Y TOTALES (Ancho: 380px)
        # ---------------------------------------------------------------------
        self.panel_left = ctk.CTkFrame(
            self, 
            fg_color="#E2E8F0", 
            border_width=2, 
            border_color="#64748B", 
            width=380, 
            corner_radius=4
        )
        self.panel_left.pack(side="left", fill="y", padx=6, pady=6)
        self.panel_left.pack_propagate(False)

        # Código Padrón
        ctk.CTkLabel(
            self.panel_left, 
            text="codigo padron", 
            font=("Arial", 20, "bold"), 
            text_color="#0F172A"
        ).pack(anchor="w", padx=14, pady=(14, 2))
        
        self.txt_padron = ctk.CTkEntry(
            self.panel_left, 
            font=("Arial", 22, "bold"), 
            fg_color="#FFFFFF", 
            text_color="#000000", 
            border_color="#334155",
            border_width=2,
            corner_radius=2,
            height=46
        )
        self.txt_padron.pack(fill="x", padx=14, pady=(0, 10))

        # Socio
        ctk.CTkLabel(self.panel_left, text="Socio:", font=("Arial", 20, "bold"), text_color="#0F172A").pack(anchor="w", padx=14)
        self.lbl_socio_nombre = ctk.CTkLabel(
            self.panel_left, 
            text="[ingrese un codigo padron]", 
            font=("Arial", 20, "bold"), 
            text_color="#334155", 
            wraplength=340, 
            justify="left"
        )
        self.lbl_socio_nombre.pack(anchor="w", padx=14, pady=(0, 6))

        # DNI / RUC
        ctk.CTkLabel(self.panel_left, text="DNI/RUC:", font=("Arial", 20, "bold"), text_color="#0F172A").pack(anchor="w", padx=14)
        self.lbl_socio_doc = ctk.CTkLabel(self.panel_left, text="-", font=("Arial", 20, "bold"), text_color="#0F172A")
        self.lbl_socio_doc.pack(anchor="w", padx=14, pady=(0, 8))

        # Parcela
        ctk.CTkLabel(self.panel_left, text="Parcela:", font=("Arial", 20, "bold"), text_color="#0F172A").pack(anchor="w", padx=14)
        self.cmb_parcela = ctk.CTkOptionMenu(
            self.panel_left, 
            values=["---"], 
            fg_color="#FFFFFF", 
            text_color="#000000", 
            button_color="#1E3A8A",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="#000000",
            corner_radius=2,
            height=42, 
            font=("Arial", 20, "bold")
        )
        self.cmb_parcela.pack(fill="x", padx=14, pady=(0, 10))

        # Divisor de grilla
        ctk.CTkFrame(self.panel_left, height=2, fg_color="#64748B", corner_radius=0).pack(fill="x", padx=6, pady=8)

        # TOTALES ACUMULADOS
        ctk.CTkLabel(self.panel_left, text="TOTALES", font=("Arial", 22, "bold"), text_color="#0F172A").pack(anchor="w", padx=14, pady=4)
        
        frame_tot_m = ctk.CTkFrame(self.panel_left, fg_color="transparent")
        frame_tot_m.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(frame_tot_m, text="Mercado:", font=("Arial", 22, "bold"), text_color="#0F172A").pack(side="left")
        self.lbl_tot_mercado = ctk.CTkLabel(frame_tot_m, text="0.00kg", font=("Arial", 25, "bold"), text_color="#0284C7")
        self.lbl_tot_mercado.pack(side="right")

        frame_tot_f = ctk.CTkFrame(self.panel_left, fg_color="transparent")
        frame_tot_f.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(frame_tot_f, text="Fabrica:", font=("Arial", 22, "bold"), text_color="#0F172A").pack(side="left")
        self.lbl_tot_fabrica = ctk.CTkLabel(frame_tot_f, text="0.00kg", font=("Arial", 25, "bold"), text_color="#D97706")
        self.lbl_tot_fabrica.pack(side="right")

        ctk.CTkFrame(self.panel_left, height=2, fg_color="#64748B", corner_radius=0).pack(fill="x", padx=6, pady=10)

        # Botón Verde Finalizar Socio
        self.btn_finalizar = ctk.CTkButton(
            self.panel_left, 
            text="FINALIZAR PESAJE\nSOCIO", 
            font=("Arial", 20, "bold"), 
            fg_color="#16A34A", 
            hover_color="#15803D",
            text_color="#FFFFFF",
            corner_radius=2,
            height=65,
            command=self._finalizar_pesaje_socio
        )
        self.btn_finalizar.pack(fill="x", side="bottom", padx=14, pady=14)

        # ---------------------------------------------------------------------
        # PANEL CENTRAL: BOTONES DE DESTINO, VISOR LCD Y TABLAS
        # ---------------------------------------------------------------------
        self.panel_center = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_center.pack(side="left", fill="both", expand=True, padx=4, pady=6)

        # Pestañas de Selección [F1] Mercado / [F2] Fábrica
        self.frame_tabs = ctk.CTkFrame(self.panel_center, fg_color="transparent", height=42)
        self.frame_tabs.pack(fill="x", side="top", pady=(0, 6))

        self.btn_f1 = ctk.CTkButton(
            self.frame_tabs, text="MERCADO [F1]", font=("Arial", 20, "bold"), 
            fg_color="#0284C7", hover_color="#0369A1", text_color="#FFFFFF", corner_radius=2, width=200, height=42,
            command=lambda: self._set_destino("MERCADO")
        )
        self.btn_f1.pack(side="left", padx=(0, 6))

        self.btn_f2 = ctk.CTkButton(
            self.frame_tabs, text="FABRICA [F2]", font=("Arial", 20, "bold"), 
            fg_color="#E2E8F0", hover_color="#D97706", text_color="#000000", corner_radius=2, width=200, height=42,
            command=lambda: self._set_destino("FABRICA")
        )
        self.btn_f2.pack(side="left", padx=6)

        # Visor LCD Gigante de Peso (Black / Green Electric)
        self.frame_visor = ctk.CTkFrame(self.panel_center, fg_color="#000000", height=180, corner_radius=2, border_width=2, border_color="#475569")
        self.frame_visor.pack(fill="x", side="top", pady=(0, 8))
        self.frame_visor.pack_propagate(False)

        self.lbl_unit = ctk.CTkLabel(self.frame_visor, text="kg", font=("Arial", 40, "bold"), text_color="#00FF00")
        self.lbl_unit.pack(side="right", padx=(0, 20), pady=(40, 0))

        self.lbl_peso = ctk.CTkLabel(self.frame_visor, text="128.00", font=("Consolas", 180, "bold"), text_color="#00FF00")
        self.lbl_peso.pack(side="right", padx=(0, 10))

        # --- CONTENEDOR DE TABLAS (IZQ) Y CONTROLES OPERATIVOS (DER) ---
        self.frame_bottom_grid = ctk.CTkFrame(self.panel_center, fg_color="transparent")
        self.frame_bottom_grid.pack(fill="both", expand=True)

        # Tablas de Pesaje
        self.frame_tables = ctk.CTkFrame(self.frame_bottom_grid, fg_color="transparent")
        self.frame_tables.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.panel_tabla_mercado = self._crear_estructura_tabla("MERCADO", self.frame_tables, header_color="#0284C7")
        self.panel_tabla_fabrica = self._crear_estructura_tabla("FABRICA", self.frame_tables, header_color="#D97706")

        # Panel de Botones Operativos Derecha
        self.panel_right = ctk.CTkFrame(self.frame_bottom_grid, fg_color="#E2E8F0", border_width=2, border_color="#64748B", width=200, corner_radius=2)
        self.panel_right.pack(side="right", fill="y")
        self.panel_right.pack_propagate(False)

        ctk.CTkLabel(self.panel_right, text="cant de sacos", font=("Arial", 20, "bold"), text_color="#000000").pack(pady=(12, 4))
        self.txt_sacos = ctk.CTkEntry(
            self.panel_right, 
            font=("Arial", 30, "bold"), 
            justify="center", 
            fg_color="#FFFFFF", 
            text_color="#000000", 
            border_color="#000000",
            border_width=2,
            corner_radius=2,
            height=48
        )
        self.txt_sacos.pack(fill="x", padx=10, pady=(0, 10))
        self.txt_sacos.insert(0, "1")

        self.btn_registrar = ctk.CTkButton(
            self.panel_right, 
            text="REGISTRAR\n[ENTER]", 
            font=("Arial", 20, "bold"), 
            fg_color="#0284C7", 
            hover_color="#0369A1", 
            text_color="#FFFFFF",
            corner_radius=2,
            height=60, 
            command=self._registrar_bajada
        )
        self.btn_registrar.pack(fill="x", padx=10, pady=5)

        self.btn_eliminar = ctk.CTkButton(
            self.panel_right, 
            text="ELIMINAR\nULTIMO", 
            font=("Arial", 20, "bold"), 
            fg_color="#EF4444", 
            hover_color="#DC2626", 
            text_color="#FFFFFF",
            corner_radius=2,
            height=52, 
            command=self._eliminar_ultimo
        )
        self.btn_eliminar.pack(fill="x", padx=10, pady=5)

        self.btn_reiniciar = ctk.CTkButton(
            self.panel_right, 
            text="REINICIAR\nPESAJE", 
            font=("Arial", 20, "bold"), 
            fg_color="#991B1B", 
            hover_color="#7F1D1D", 
            text_color="#FFFFFF",
            corner_radius=2,
            height=58, 
            command=self._reiniciar_pesaje
        )
        self.btn_reiniciar.pack(fill="x", side="bottom", padx=10, pady=10)

    def _crear_estructura_tabla(self, nombre_destino: str, contenedor_padre, header_color: str) -> Dict:
        """Crea la tabla con diseño de grilla tipo Mettler Toledo y textos de 25px."""
        box = ctk.CTkFrame(contenedor_padre, fg_color="#FFFFFF", border_width=2, border_color="#000000", corner_radius=0)
        box.pack(side="left", fill="both", expand=True, padx=2)

        # Encabezado Destino
        lbl_header = ctk.CTkLabel(box, text=nombre_destino, font=("Arial", 20, "bold"), fg_color=header_color, text_color="#FFFFFF", height=38, corner_radius=0)
        lbl_header.pack(fill="x", side="top")

        # Subencabezados
        sub_head = ctk.CTkFrame(box, fg_color="#E2E8F0", height=45, corner_radius=0, border_width=1, border_color="#000000")
        sub_head.pack(fill="x", side="top")

        ctk.CTkLabel(sub_head, text="Peso", font=("Arial", 20, "bold"), text_color="#000000", width=140).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(sub_head, text="Sacos", font=("Arial", 20, "bold"), text_color="#000000", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(sub_head, text="", width=35).pack(side="right", padx=3)

        # Cuerpo Scrollable
        scroll = ctk.CTkScrollableFrame(box, fg_color="#FFFFFF", corner_radius=0)
        scroll.pack(fill="both", expand=True)

        # Pie con Totales (Fuentes de 25px)
        footer = ctk.CTkFrame(box, fg_color="#FFFFFF", height=42, corner_radius=0, border_width=1, border_color="#000000")
        footer.pack(fill="x", side="bottom")

        lbl_tot_peso = ctk.CTkLabel(footer, text="0.00 kg", font=("Arial", 25, "bold"), text_color="#000000", width=140)
        lbl_tot_peso.pack(side="left", padx=5, pady=5)

        lbl_tot_sacos = ctk.CTkLabel(footer, text="0", font=("Arial", 25, "bold"), text_color="#000000", width=80)
        lbl_tot_sacos.pack(side="left", padx=5)

        ctk.CTkLabel(footer, text="total", font=("Arial", 22, "bold"), text_color="#000000").pack(side="right", padx=10)

        return {
            "header": lbl_header,
            "scroll": scroll,
            "lbl_peso": lbl_tot_peso,
            "lbl_sacos": lbl_tot_sacos
        }

    # ---------------------------------------------------------------------
    # LÓGICA OPERATIVA Y TECLAS RÁPIDAS
    # ---------------------------------------------------------------------
    def _bind_shortcuts(self):
        self.txt_padron.bind("<Return>", lambda e: self._buscar_socio())
        self.txt_sacos.bind("<Return>", lambda e: self._registrar_bajada())

    def _set_destino(self, destino: str):
        self.destino_actual = destino
        
        # Conmutación de color visual en botones de pestaña
        self.btn_f1.configure(
            fg_color="#0284C7" if destino == "MERCADO" else "#E2E8F0", 
            text_color="#FFFFFF" if destino == "MERCADO" else "#000000"
        )
        self.btn_f2.configure(
            fg_color="#D97706" if destino == "FABRICA" else "#E2E8F0", 
            text_color="#FFFFFF" if destino == "FABRICA" else "#000000"
        )

    # def _buscar_socio(self):
    #     padron = self.txt_padron.get().strip()
    #     if not padron:
    #         return

    #     ag = self.agricultor_dao.buscar_por_padron(padron)
    #     if ag:
    #         self.agricultor_actual = ag
    #         nombre = f"{ag['nombres']} {ag.get('apellidos', '')}".strip()
    #         self.lbl_socio_nombre.configure(text=nombre, text_color="#000000")
    #         self.lbl_socio_doc.configure(text=ag.get('numero_documento') or 'NO REGISTRADO')

    #         parcelas = [p['codigo_parcela'] for p in ag.get('parcelas', [])]
    #         if parcelas:
    #             self.cmb_parcela.configure(values=parcelas)
    #             self.cmb_parcela.set(parcelas[0])
    #         self.txt_sacos.focus_set()
    #         self.txt_sacos.select_range(0, 'end')
    #     else:
    #         self.lbl_socio_nombre.configure(text="❌ NO ENCONTRADO", text_color="#EF4444")
    #         self.lbl_socio_doc.configure(text="-")
    #         self.agricultor_actual = None

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

            # Diccionario de mapeo: "Texto Visor" -> Objeto Parcela
            self.parcelas_map = {}
            opciones_combo = []

            for p in ag.get('parcelas', []):
                cod_int = p.get('codigo_interno') or 'P01'
                nombre_p = p.get('nombre_parcela', '')
                sector_p = f" ({p['sector']})" if p.get('sector') else ""
                
                # Etiqueta legible: "P01 - Monte de los olivos (Sector Norte)"
                label_vis = f"{cod_int} - {nombre_p}{sector_p}".strip()
                
                opciones_combo.append(label_vis)
                self.parcelas_map[label_vis] = p

            if opciones_combo:
                self.cmb_parcela.configure(values=opciones_combo)
                self.cmb_parcela.set(opciones_combo[0])
            else:
                self.cmb_parcela.configure(values=["---"])
                self.cmb_parcela.set("---")

            self.txt_sacos.focus_set()
            self.txt_sacos.select_range(0, 'end')
        else:
            self.lbl_socio_nombre.configure(text="❌ NO ENCONTRADO", text_color="#EF4444")
            self.lbl_socio_doc.configure(text="-")
            self.cmb_parcela.configure(values=["---"])
            self.cmb_parcela.set("---")
            self.agricultor_actual = None
            self.parcelas_map = {}
    
    def _obtener_parcela_seleccionada(self) -> Optional[Dict]:
        """Recupera la parcela completa desde el mapa usando la selección del combo."""
        val_combo = self.cmb_parcela.get()
        if hasattr(self, 'parcelas_map') and val_combo in self.parcelas_map:
            return self.parcelas_map[val_combo]
        return None


    # def _registrar_bajada(self):
    #     try:
    #         peso_actual = float(self.lbl_peso.cget("text"))
    #         num_sacos = int(self.txt_sacos.get().strip())
    #     except ValueError:
    #         return

    #     if peso_actual <= 0 or num_sacos <= 0:
    #         return

    #     item_id = str(uuid.uuid4())
    #     item = {
    #         "uuid": item_id,
    #         "peso": peso_actual,
    #         "sacos": num_sacos
    #     }

    #     dest = self.destino_actual if self.destino_actual in self.pesadas else "MERCADO"
    #     self.pesadas[dest].append(item)

    #     if dest in ["MERCADO", "FABRICA"]:
    #         self._crear_fila_ui(dest, item)
    #         self._actualizar_totales()

    #     self.txt_sacos.focus_set()
    #     self.txt_sacos.select_range(0, 'end')

    def _crear_fila_ui(self, dest: str, item: Dict):
        """Inserción de fila directa con fuentes de 25px y borde de grilla (Sin Flicker)."""
        panel = self.panel_tabla_mercado if dest == "MERCADO" else self.panel_tabla_fabrica
        scroll = panel["scroll"]

        row = ctk.CTkFrame(scroll, fg_color="#FFFFFF", height=40, corner_radius=0, border_width=1, border_color="#000000")
        row.pack(fill="x", pady=1)

        # VALORES DE TABLA EN 25PX
        ctk.CTkLabel(row, text=f"{item['peso']:.2f} kg", font=("Arial", 25, "bold"), text_color="#000000", width=140).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=str(item['sacos']), font=("Arial", 25, "bold"), text_color="#000000", width=80).pack(side="left", padx=5)

        item_id = item["uuid"]
        btn_del = ctk.CTkButton(
            row, text="x", font=("Arial", 20, "bold"), fg_color="#EF4444", hover_color="#DC2626", text_color="#FFFFFF",
            width=32, height=28, corner_radius=0,
            command=lambda d=dest, uid=item_id: self._eliminar_bajada_por_uuid(d, uid)
        )
        btn_del.pack(side="right", padx=5)

        self.filas_ui[dest][item_id] = row

    def _eliminar_bajada_por_uuid(self, destino: str, item_id: str):
        """Elimina el registro sin tocar el resto de la interfaz (Zero Flicker)."""
        self.pesadas[destino] = [x for x in self.pesadas[destino] if x["uuid"] != item_id]

        if item_id in self.filas_ui[destino]:
            widget = self.filas_ui[destino].pop(item_id)
            widget.destroy()

        self._actualizar_totales()

    def _eliminar_ultimo(self):
        dest = self.destino_actual if self.destino_actual in self.pesadas else "MERCADO"
        if self.pesadas[dest]:
            ultimo_item = self.pesadas[dest][-1]
            self._eliminar_bajada_por_uuid(dest, ultimo_item["uuid"])

    def _actualizar_totales(self):
        """Actualización directa de acumulados."""
        for dest, panel in [("MERCADO", self.panel_tabla_mercado), ("FABRICA", self.panel_tabla_fabrica)]:
            tot_peso = sum(x["peso"] for x in self.pesadas[dest])
            tot_sacos = sum(x["sacos"] for x in self.pesadas[dest])
            panel["lbl_peso"].configure(text=f"{tot_peso:.2f} kg")
            panel["lbl_sacos"].configure(text=str(tot_sacos))

        tot_m = sum(x["peso"] for x in self.pesadas["MERCADO"])
        tot_f = sum(x["peso"] for x in self.pesadas["FABRICA"])

        self.lbl_tot_mercado.configure(text=f"{tot_m:.2f}kg")
        self.lbl_tot_fabrica.configure(text=f"{tot_f:.2f}kg")

    # def _reiniciar_pesaje(self):
    #     for dest in ["MERCADO", "FABRICA"]:
    #         self.pesadas[dest].clear()
    #         for widget in self.filas_ui[dest].values():
    #             widget.destroy()
    #         self.filas_ui[dest].clear()

    #     self.txt_padron.delete(0, 'end')
    #     self.lbl_socio_nombre.configure(text="[ingrese un codigo padron]", text_color="#374151")
    #     self.lbl_socio_doc.configure(text="-")
    #     self.cmb_parcela.configure(values=["---"])
    #     self.cmb_parcela.set("---")
    #     self.agricultor_actual = None
    #     self._actualizar_totales()
    #     self.txt_padron.focus_set()


    def _reiniciar_pesaje(self):
        for dest in ["MERCADO", "FABRICA"]:
            self.pesadas[dest].clear()
            for widget in self.filas_ui[dest].values():
                widget.destroy()
            self.filas_ui[dest].clear()

        self.txt_padron.delete(0, 'end')
        self.lbl_socio_nombre.configure(text="[ingrese un codigo padron]", text_color="#374151")
        self.lbl_socio_doc.configure(text="-")
        self.cmb_parcela.configure(values=["---"])
        self.cmb_parcela.set("---")
        self.agricultor_actual = None
        self.parcelas_map = {}  # Limpieza de parcelas mapeadas
        self._actualizar_totales()
        self.txt_padron.focus_set()

    '''def _finalizar_pesaje_socio(self):
        if not self.agricultor_actual:
            return
        
        # Guarda las transacciones locales en SQLite e imprime comprobantes
        self._reiniciar_pesaje()'''

    def _iniciar_lectura_balanza(self):
        """Consulta el peso actual en Decimal y actualiza el visor sin congelar la UI."""
        if hasattr(self, 'scale_service') and self.scale_service:
            peso = self.scale_service.get_weight() # Retorna Decimal
            #peso_texto = f"{peso:.2f}"
            peso_texto = peso
            #print(peso)
            
            if self.lbl_peso.cget("text") != peso_texto:
                self.lbl_peso.configure(text=peso_texto)

        # Refresco cada 30 milisegundos (33 FPS)
        self.after(30, self._iniciar_lectura_balanza)

    def _registrar_bajada(self):
        try:
            # Captura directa usando Decimal
            peso_actual = Decimal(self.lbl_peso.cget("text"))
            num_sacos = int(self.txt_sacos.get().strip())
        except (ValueError, InvalidOperation):
            return

        if peso_actual <= Decimal('0.00') or num_sacos <= 0:
            return

        item_id = str(uuid.uuid4())
        item = {
            "uuid": item_id,
            "peso": peso_actual,  # Almacenado como Decimal
            "sacos": num_sacos
        }

        dest = self.destino_actual if self.destino_actual in self.pesadas else "MERCADO"
        self.pesadas[dest].append(item)

        if dest in ["MERCADO", "FABRICA"]:
            self._crear_fila_ui(dest, item)
            self._actualizar_totales()

        self.txt_sacos.focus_set()
        self.txt_sacos.select_range(0, 'end')

    def _actualizar_totales(self):
        """Calcula los totales exactos usando Decimal."""
        for dest, panel in [("MERCADO", self.panel_tabla_mercado), ("FABRICA", self.panel_tabla_fabrica)]:
            tot_peso = sum((x["peso"] for x in self.pesadas[dest]), Decimal('0.00'))
            tot_sacos = sum(x["sacos"] for x in self.pesadas[dest])
            panel["lbl_peso"].configure(text=f"{tot_peso:.2f} kg")
            panel["lbl_sacos"].configure(text=str(tot_sacos))

        tot_m = sum((x["peso"] for x in self.pesadas["MERCADO"]), Decimal('0.00'))
        tot_f = sum((x["peso"] for x in self.pesadas["FABRICA"]), Decimal('0.00'))

        self.lbl_tot_mercado.configure(text=f"{tot_m:.2f}kg")
        self.lbl_tot_fabrica.configure(text=f"{tot_f:.2f}kg")

    def _ejecutar_cierre_jornada(self):
        """Cierra la sesión en BD y notifica para volver a la pantalla de Apertura."""
        self.sesion_dao.cerrar_sesion_activa()
        if self.on_cerrar_sesion_cb:
            self.on_cerrar_sesion_cb()

    # def _finalizar_pesaje_socio(self):
    #     """Genera 1 ÚNICO RECIBO (RE01-000001) guardando Mercado y Fábrica juntos."""
    #     if not self.agricultor_actual or not self.sesion_activa:
    #         return

    #     bajadas_m = self.pesadas["MERCADO"]
    #     bajadas_f = self.pesadas["FABRICA"]

    #     if not bajadas_m and not bajadas_f:
    #         return

    #     parcela_codigo = self.cmb_parcela.get()
    #     if parcela_codigo == "---":
    #         return

    #     # Destino predominante o Mixto
    #     if bajadas_m and bajadas_f:
    #         destino_cabecera = "MIXTO"
    #     elif bajadas_m:
    #         destino_cabecera = "MERCADO"
    #     else:
    #         destino_cabecera = "FABRICA"

    #     todas_bajadas = bajadas_m + bajadas_f
    #     peso_bruto_total = sum((b["peso"] for b in todas_bajadas), Decimal('0.00'))
    #     tara_total = Decimal('0.00')
    #     peso_neto_total = peso_bruto_total - tara_total
    #     total_sacos = sum(b["sacos"] for b in todas_bajadas)

    #     rec_uuid = str(uuid.uuid4())
    #     codigo_ticket = self.recepcion_dao.generar_siguiente_codigo_ticket("RE01")
    #     codigo_lote_origen = self.sesion_activa['codigo_sesion']
    #     fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #     # Cabecera del Recibo
    #     recepcion_data = {
    #         "uuid": rec_uuid,
    #         "lote_acopio_id": None,
    #         "codigo_lote_origen": codigo_lote_origen,
    #         "codigo_ticket": codigo_ticket,
    #         "codigo_padron": self.agricultor_actual['codigo_padron'],
    #         "codigo_parcela": parcela_codigo,
    #         "producto": "MARACUYA",
    #         "destino": destino_cabecera,
    #         "total_sacos": total_sacos,
    #         "peso_bruto_total": float(peso_bruto_total),
    #         "tara_total": float(tara_total),
    #         "peso_neto_total": float(peso_neto_total),
    #         "fecha_pesaje": fecha_actual,
    #         "observaciones": None
    #     }

    #     # 1. Obtenemos el Año y Día Juliano actual (Ej: 26214)
    #     now = datetime.now()
    #     juliano = f"{now.strftime('%y')}{now.timetuple().tm_yday:03d}"

    #     # Detalles con Destino por bajada
    #     detalles_data = []
    #     orden = 1
    #     for dest in ["MERCADO", "FABRICA"]:
    #         for b in self.pesadas[dest]:
    #             # Estructura: [JULIANO]-[PADRON]-[PARCELA]-[ORDEN]
    #             codigo_trazabilidad = f"{juliano}-{self.agricultor_actual['codigo_padron']}-{parcela_codigo}-{orden}"
                
    #             detalles_data.append({
    #                 "uuid": str(uuid.uuid4()),
    #                 "codigo_trazabilidad": codigo_trazabilidad,
    #                 "destino": dest,
    #                 "numero_sacos": b["sacos"],
    #                 "peso_bruto": float(b["peso"]),
    #                 "tara": 0.0,
    #                 "peso_neto": float(b["peso"]),
    #                 "orden": orden
    #             })
    #             orden += 1

    #     exito = self.recepcion_dao.guardar_pesaje_completo(recepcion_data, detalles_data)
    #     #if exito and hasattr(self, 'print_service') and self.print_service:
    #     #    self.print_service.imprimir_recibo(recepcion_data, detalles_data)
    #     # 2. Intentar imprimir de forma segura (sin bloquear el flujo)
    #     if hasattr(self, 'print_service') and self.print_service:
    #         try:
    #             self.print_service.imprimir_recibo(recepcion_data, detalles_data)
    #         except Exception as e:
    #             print(f"⚠ [ADVERTENCIA IMPRESORA]: No se pudo imprimir el recibo: {e}")
            
    #     # 3. Notificación visual en consola o estado
    #     print(f"✅ Recibo {codigo_ticket} guardado correctamente.")    

    #     self._reiniciar_pesaje()

    def _finalizar_pesaje_socio(self):
        if not self.agricultor_actual or not self.sesion_activa:
            return

        bajadas_m = self.pesadas["MERCADO"]
        bajadas_f = self.pesadas["FABRICA"]

        if not bajadas_m and not bajadas_f:
            return

        # Recupera el objeto parcela mediante el mapa visual
        parcela_obj = self._obtener_parcela_seleccionada()
        if not parcela_obj:
            return
            
        codigo_parcela_corta = parcela_obj.get('codigo_interno', 'P01')
        codigo_parcela_oficial = parcela_obj.get('codigo_parcela')

        # Determinar destino cabecera para SQLite
        if bajadas_m and bajadas_f:
            destino_cabecera = "MIXTO"
        elif bajadas_m:
            destino_cabecera = "MERCADO"
        else:
            destino_cabecera = "FABRICA"

        rec_uuid = str(uuid.uuid4())
        codigo_ticket = self.recepcion_dao.generar_siguiente_codigo_ticket("RE01")
        
        # Nivel 1: Código Macro (Ej: A1260803-01)
        codigo_sesion = self.sesion_activa['codigo_sesion']
        padron = self.agricultor_actual['codigo_padron']
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        detalles_data = []
        peso_bruto_total_real = Decimal('0.00')
        peso_bruto_total_contable = Decimal('0.00')
        total_sacos_acumulado = 0

        # Bucle para procesar bajadas
        for dest in ["MERCADO", "FABRICA"]:
            letra_destino = "M" if dest == "MERCADO" else "F"
            
            for orden_bajada, b in enumerate(self.pesadas[dest], start=1):
                peso_real = b["peso"]  # Decimal de balanza
                peso_contable = self._calcular_peso_contable(peso_real)
                num_sacos = b["sacos"]

                # NIVEL 3: Cadena de Etiqueta (Ej: A1260803-01-M-042-P01-1)
                codigo_trazabilidad = f"{codigo_sesion}-{letra_destino}-{padron}-{codigo_parcela_corta}-{orden_bajada}"

                detalles_data.append({
                    "uuid": str(uuid.uuid4()),
                    "codigo_trazabilidad": codigo_trazabilidad,
                    "destino": dest,
                    "numero_sacos": num_sacos,
                    "peso_bruto_real": float(peso_real),
                    "peso_contable": float(peso_contable),
                    "peso_bruto": float(peso_contable),
                    "tara": 0.0,
                    "peso_neto": float(peso_contable),
                    "orden": orden_bajada
                })

                peso_bruto_total_real += peso_real
                peso_bruto_total_contable += peso_contable
                total_sacos_acumulado += num_sacos

        recepcion_data = {
            "uuid": rec_uuid,
            "lote_acopio_id": None,
            "codigo_lote_origen": codigo_sesion,
            "codigo_ticket": codigo_ticket,
            "codigo_padron": padron,
            "codigo_parcela": codigo_parcela_oficial,
            "producto": "MARACUYA",
            "destino": destino_cabecera,
            "total_sacos": total_sacos_acumulado,
            "peso_bruto_real": float(peso_bruto_total_real),
            "peso_bruto_total": float(peso_bruto_total_contable),
            "tara_total": 0.0,
            "peso_neto_total": float(peso_bruto_total_contable),
            "fecha_pesaje": fecha_actual,
            "observaciones": None
        }

        exito = self.recepcion_dao.guardar_pesaje_completo(recepcion_data, detalles_data)

        if exito and hasattr(self, 'print_service') and self.print_service:
            try:
                self.print_service.imprimir_etiquetas_trazabilidad(detalles_data)
            except Exception as e:
                print(f"⚠ [IMPRESORA]: Error imprimiendo etiquetas: {e}")

        self._reiniciar_pesaje()
    
    def _calcular_peso_contable(self, peso_real):
        entero = int(peso_real)
        if (peso_real - entero) >= Decimal('0.90'):
            return Decimal(entero + 1)
        return Decimal(entero)