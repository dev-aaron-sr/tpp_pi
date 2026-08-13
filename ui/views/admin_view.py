from datetime import datetime
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import pandas as pd


class AdminView(ctk.CTkFrame):

  def __init__(
      self,
      parent,
      recepcion_dao,
      sync_service,
      print_service=None,
  ):
    super().__init__(parent, fg_color="#F1F5F9")
    self.recepcion_dao = recepcion_dao
    self.sync_service = sync_service
    self.print_service = print_service

    self.recibo_seleccionado_uuid = None
    self.mapa_recibos = {}  # {item_id_treeview: dict_data_recibo}

    self._configurar_estilos_tabla()
    self._build_ui()
    self.cargar_datos_locales()

  def _configurar_estilos_tabla(self):
    """Configura un estilo de tabla industrial de alto contraste sin decoraciones."""
    style = ttk.Style()
    style.theme_use("clam")

    # Configuración de Filas y Fuente
    style.configure(
        "Industrial.Treeview",
        background="#FFFFFF",
        foreground="#000000",
        fieldbackground="#FFFFFF",
        rowheight=36,
        font=("Arial", 10, "bold"),
        borderwidth=1,
        relief="solid",
    )

    # Configuración de Encabezados
    style.configure(
        "Industrial.Treeview.Heading",
        background="#0F172A",
        foreground="#FFFFFF",
        font=("Arial", 10, "bold"),
        relief="flat",
        padding=4,
    )

    # Resaltado de Selección
    style.map(
        "Industrial.Treeview",
        background=[("selected", "#1E3A8A")],
        foreground=[("selected", "#FFFFFF")],
    )

  def _build_ui(self):
    # ------------------------------------------------------------------
    # 1. BARRA SUPERIOR (FILTRO, REIMPRESIÓN Y EXPORTACIÓN)
    # ------------------------------------------------------------------
    self.top_panel = ctk.CTkFrame(
        self,
        fg_color="#CBD5E1",
        height=55,
        corner_radius=0,
        border_width=1,
        border_color="#000000",
    )
    self.top_panel.pack(fill="x", padx=8, pady=(8, 4))
    self.top_panel.pack_propagate(False)

    ctk.CTkLabel(
        self.top_panel,
        text="HISTORIAL Y REPORTES",
        font=("Arial", 15, "bold"),
        text_color="#000000",
    ).pack(side="left", padx=12)

    ctk.CTkLabel(
        self.top_panel,
        text="Fecha:",
        font=("Arial", 13, "bold"),
        text_color="#000000",
    ).pack(side="left", padx=(10, 4))

    self.txt_fecha_filtro = ctk.CTkEntry(
        self.top_panel,
        font=("Arial", 13, "bold"),
        text_color="#000000",
        fg_color="#FFFFFF",
        border_color="#000000",
        border_width=2,
        width=120,
        height=34,
        justify="center",
        corner_radius=0,
    )
    self.txt_fecha_filtro.pack(side="left", padx=(0, 6))
    self.txt_fecha_filtro.insert(0, datetime.now().strftime("%Y-%m-%d"))

    btn_filtrar = ctk.CTkButton(
        self.top_panel,
        text="FILTRAR",
        font=("Arial", 12, "bold"),
        fg_color="#334155",
        hover_color="#1E293B",
        text_color="#FFFFFF",
        corner_radius=0,
        width=85,
        height=34,
        command=self.cargar_datos_locales,
    )
    btn_filtrar.pack(side="left", padx=4)

    # Botones de Acción (Lado Derecho)
    self.btn_sync_now = ctk.CTkButton(
        self.top_panel,
        text="SINCRONIZAR",
        font=("Arial", 12, "bold"),
        fg_color="#1E3A8A",
        hover_color="#1E40AF",
        text_color="#FFFFFF",
        corner_radius=0,
        height=36,
        command=self._sincronizar,
    )
    self.btn_sync_now.pack(side="right", padx=8)

    btn_excel = ctk.CTkButton(
        self.top_panel,
        text="EXPORTAR EXCEL",
        font=("Arial", 12, "bold"),
        fg_color="#15803D",
        hover_color="#166534",
        text_color="#FFFFFF",
        corner_radius=0,
        height=36,
        command=self.exportar_excel,
    )
    btn_excel.pack(side="right", padx=4)

    btn_reimprimir = ctk.CTkButton(
        self.top_panel,
        text="🖨️ REIMPRIMIR RECIBO",
        font=("Arial", 12, "bold"),
        fg_color="#0284C7",
        hover_color="#0369A1",
        text_color="#FFFFFF",
        corner_radius=0,
        height=36,
        command=self._reimprimir_recibo_seleccionado,
    )
    btn_reimprimir.pack(side="right", padx=4)

    self.lbl_sync_status = ctk.CTkLabel(
        self.top_panel,
        text="",
        font=("Arial", 12, "bold"),
        text_color="#1E3A8A",
    )
    self.lbl_sync_status.pack(side="right", padx=8)

    # ------------------------------------------------------------------
    # 1.5. CINTA DE KPIS Y RESUMEN
    # ------------------------------------------------------------------
    self.totales_panel = ctk.CTkFrame(
        self,
        fg_color="#0F172A",
        height=38,
        corner_radius=0,
        border_width=1,
        border_color="#000000",
    )
    self.totales_panel.pack(fill="x", padx=8, pady=(0, 6))
    self.totales_panel.pack_propagate(False)

    self.lbl_totales = ctk.CTkLabel(
        self.totales_panel,
        text="TOTALES -> REAL: 0.00 kg | CONTABLE: 0 kg  ||  SIN REGISTROS",
        font=("Arial", 12, "bold"),
        text_color="#FACC15",
        anchor="w",
    )
    self.lbl_totales.pack(side="left", padx=12, fill="both", expand=True)

    # ------------------------------------------------------------------
    # 2. CONTENEDOR PRINCIPAL DE TABLAS
    # ------------------------------------------------------------------
    self.main_container = ctk.CTkFrame(self, fg_color="transparent")
    self.main_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    self.main_container.grid_columnconfigure(0, weight=7)
    self.main_container.grid_columnconfigure(1, weight=3)
    self.main_container.grid_rowconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # TABLA IZQUIERDA: RECIBOS EMITIDOS (SUBDIVIDIDO EN REAL Y CONTABLE)
    # ------------------------------------------------------------------
    self.frame_master = ctk.CTkFrame(
        self.main_container,
        fg_color="#FFFFFF",
        border_width=1,
        border_color="#000000",
        corner_radius=0,
    )
    self.frame_master.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

    lbl_title_m = ctk.CTkLabel(
        self.frame_master,
        text="RECIBOS DE ENTREGA EMITIDOS",
        font=("Arial", 13, "bold"),
        fg_color="#0F172A",
        text_color="#FFFFFF",
        height=32,
        corner_radius=0,
    )
    lbl_title_m.pack(fill="x", side="top")

    cols_m = (
        "ticket",
        "lote",
        "socio",
        "parcela",
        "sacos",
        "m_real",
        "m_cont",
        "fl_real",
        "fl_cont",
        "fp_real",
        "fp_cont",
        "total",
        "total_cont",
        "estado",
    )
    self.tree_master = ttk.Treeview(
        self.frame_master,
        columns=cols_m,
        show="headings",
        style="Industrial.Treeview",
        selectmode="browse",
    )

    # Configuración de Encabezados
    self.tree_master.heading("ticket", text="Recibo")
    self.tree_master.heading("lote", text="Cod. Lote")
    self.tree_master.heading("socio", text="Titular / Socio")
    self.tree_master.heading("parcela", text="Parc.")
    self.tree_master.heading("sacos", text="Sacos")
    self.tree_master.heading("m_real", text="Merc. Real")
    self.tree_master.heading("m_cont", text="Merc. Cont")
    self.tree_master.heading("fl_real", text="Fab.Loc Real")
    self.tree_master.heading("fl_cont", text="Fab.Loc Cont")
    self.tree_master.heading("fp_real", text="Fab.Pta Real")
    self.tree_master.heading("fp_cont", text="Fab.Pta Cont")
    self.tree_master.heading("total", text="Total")
    self.tree_master.heading("total_cont", text="Total Cont")
    self.tree_master.heading("estado", text="Estado")

    # Anchos de columnas
    self.tree_master.column("ticket", width=80, anchor="center")
    self.tree_master.column("lote", width=80, anchor="center")
    self.tree_master.column("socio", width=140, anchor="w")
    self.tree_master.column("parcela", width=45, anchor="center")
    self.tree_master.column("sacos", width=45, anchor="center")
    self.tree_master.column("m_real", width=75, anchor="e")
    self.tree_master.column("m_cont", width=70, anchor="e")
    self.tree_master.column("fl_real", width=75, anchor="e")
    self.tree_master.column("fl_cont", width=70, anchor="e")
    self.tree_master.column("fp_real", width=75, anchor="e")
    self.tree_master.column("fp_cont", width=70, anchor="e")
    self.tree_master.column("total", width=85, anchor="e")
    self.tree_master.column("total_cont", width=80, anchor="e")
    self.tree_master.column("estado", width=60, anchor="center")

    # Configurar estilo visual para la fila de totales al inicio
    self.tree_master.tag_configure(
        "total_row", background="#FEF08A", foreground="#000000"
    )

    sb_m = ttk.Scrollbar(
        self.frame_master, orient="vertical", command=self.tree_master.yview
    )
    self.tree_master.configure(yscrollcommand=sb_m.set)

    sb_m.pack(side="right", fill="y")
    self.tree_master.pack(fill="both", expand=True)
    self.tree_master.bind("<<TreeviewSelect>>", self._on_recibo_selected)

    # ------------------------------------------------------------------
    # TABLA DERECHA: BAJADAS DE BALANZA (DESGLOSE REAL Y CONTABLE)
    # ------------------------------------------------------------------
    self.frame_detail = ctk.CTkFrame(
        self.main_container,
        fg_color="#FFFFFF",
        border_width=1,
        border_color="#000000",
        corner_radius=0,
    )
    self.frame_detail.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

    self.lbl_detail_title = ctk.CTkLabel(
        self.frame_detail,
        text="DESGLOSE DE BAJADAS DE BALANZA",
        font=("Arial", 13, "bold"),
        fg_color="#0F172A",
        text_color="#FFFFFF",
        height=32,
        corner_radius=0,
    )
    self.lbl_detail_title.pack(fill="x", side="top")

    cols_d = (
        "orden",
        "trazabilidad",
        "destino",
        "sacos",
        "peso_real",
        "peso_contable",
    )
    self.tree_detail = ttk.Treeview(
        self.frame_detail,
        columns=cols_d,
        show="headings",
        style="Industrial.Treeview",
        selectmode="none",
    )

    self.tree_detail.heading("orden", text="N°")
    self.tree_detail.heading("trazabilidad", text="Cod. Trazabilidad")
    self.tree_detail.heading("destino", text="Destino")
    self.tree_detail.heading("sacos", text="Sacos")
    self.tree_detail.heading("peso_real", text="P. Real")
    self.tree_detail.heading("peso_contable", text="P. Contable")

    self.tree_detail.column("orden", width=35, anchor="center")
    self.tree_detail.column("trazabilidad", width=150, anchor="w")
    self.tree_detail.column("destino", width=85, anchor="center")
    self.tree_detail.column("sacos", width=50, anchor="center")
    self.tree_detail.column("peso_real", width=75, anchor="e")
    self.tree_detail.column("peso_contable", width=80, anchor="e")

    sb_d = ttk.Scrollbar(
        self.frame_detail, orient="vertical", command=self.tree_detail.yview
    )
    self.tree_detail.configure(yscrollcommand=sb_d.set)

    sb_d.pack(side="right", fill="y")
    self.tree_detail.pack(fill="both", expand=True)

  # ----------------------------------------------------------------------
  # CARGA DE DATOS LOCALES Y FILA DE TOTALES EN ENCABEZADO
  # ----------------------------------------------------------------------
  def cargar_datos_locales(self):
    """Carga recibos, subdivide cada destino en Real y Contable, e inserta una fila de totales al inicio de la tabla."""
    for item in self.tree_master.get_children():
      self.tree_master.delete(item)

    self._limpiar_tabla_detalles()
    self.mapa_recibos.clear()
    self.recibo_seleccionado_uuid = None

    fecha_filtro = self.txt_fecha_filtro.get().strip()
    historial = self.recepcion_dao.obtener_historial_por_fecha(fecha_filtro)

    # Acumuladores para la fila superior de totales
    tot_sacos_gen = 0
    tot_m_real_gen, tot_m_cont_gen = 0.0, 0.0
    tot_fl_real_gen, tot_fl_cont_gen = 0.0, 0.0
    tot_fp_real_gen, tot_fp_cont_gen = 0.0, 0.0
    tot_general_real, tot_general_cont = 0.0, 0.0

    filas_a_insertar = []

    for item in historial:
      socio_txt = (
          f"{item['codigo_padron']} - {item.get('socio_nombre') or ''}".strip()
      )
      estado_txt = "PENDIENTE" if item["sincronizado"] == 0 else "SYNC"

      detalles = self.recepcion_dao.obtener_detalles_por_recepcion_uuid(
          item["uuid"]
      )

      # Calcular pesos por destino (Real y Contable) para este recibo
      m_real = sum(
          float(d.get("peso_bruto", 0.0))
          for d in detalles
          if d.get("destino") == "MERCADO"
      )
      m_cont = sum(
          float(d.get("peso_contable", 0.0))
          for d in detalles
          if d.get("destino") == "MERCADO"
      )

      fl_real = sum(
          float(d.get("peso_bruto", 0.0))
          for d in detalles
          if d.get("destino") == "FABRICA_LOCAL"
      )
      fl_cont = sum(
          float(d.get("peso_contable", 0.0))
          for d in detalles
          if d.get("destino") == "FABRICA_LOCAL"
      )

      fp_real = sum(
          float(d.get("peso_bruto", 0.0))
          for d in detalles
          if d.get("destino") == "FABRICA_PLANTA"
      )
      fp_cont = sum(
          float(d.get("peso_contable", 0.0))
          for d in detalles
          if d.get("destino") == "FABRICA_PLANTA"
      )

      total_recibo_real = m_real + fl_real + fp_real
      total_recibo_cont = m_cont + fl_cont + fp_cont
      sacos_recibo = item.get("total_sacos", 0)

      # Acumular globales
      tot_sacos_gen += sacos_recibo
      tot_m_real_gen += m_real
      tot_m_cont_gen += m_cont
      tot_fl_real_gen += fl_real
      tot_fl_cont_gen += fl_cont
      tot_fp_real_gen += fp_real
      tot_fp_cont_gen += fp_cont
      tot_general_real += total_recibo_real
      tot_general_cont += total_recibo_cont

      valores_fila = (
          item["codigo_ticket"],
          item.get("codigo_lote_origen", "-"),
          socio_txt,
          item.get("codigo_parcela", "-"),
          sacos_recibo,
          f"{m_real:.2f}",
          f"{round(m_cont)}",
          f"{fl_real:.2f}",
          f"{round(fl_cont)}",
          f"{fp_real:.2f}",
          f"{round(fp_cont)}",
          f"{total_recibo_real:.2f}",
          f"{round(total_recibo_cont)}",
          estado_txt,
      )
      filas_a_insertar.append((valores_fila, item))

    # 1. FILA DE TOTALES AL INICIO (JUSTO DEBAJO DE LOS ENCABEZADOS DE LA TABLA)
    if historial:
      valores_totales = (
          "--- TOTALES ---",
          "-",
          "-",
          "-",
          tot_sacos_gen,
          f"{tot_m_real_gen:.2f}",
          f"{round(tot_m_cont_gen):,}",
          f"{tot_fl_real_gen:.2f}",
          f"{round(tot_fl_cont_gen):,}",
          f"{tot_fp_real_gen:.2f}",
          f"{round(tot_fp_cont_gen):,}",
          f"{tot_general_real:.2f}",
          f"{round(tot_general_cont):,}",
          "-",
      )
      self.tree_master.insert(
          "", "end", values=valores_totales, tags=("total_row",)
      )

    # 2. INSERTAR RECIBOS INDIVIDUALES
    for vals, item_data in filas_a_insertar:
      item_id = self.tree_master.insert("", "end", values=vals)
      self.mapa_recibos[item_id] = item_data

    # Actualización de cinta KPI superior
    if tot_general_real > 0 or tot_general_cont > 0:
      texto_kpi = (
          f"TOTAL GENERAL -> REAL: {tot_general_real:.2f} kg | CONTABLE:"
          f" {round(tot_general_cont):,} kg  ||  MERCADO:"
          f" {tot_m_real_gen:.2f} kg  ||  FAB. LOCAL: {tot_fl_real_gen:.2f} kg"
          f"  ||  FAB. PLANTA: {tot_fp_real_gen:.2f} kg"
      )
    else:
      texto_kpi = (
          "TOTALES -> REAL: 0.00 kg | CONTABLE: 0 kg  ||  SIN REGISTROS"
      )

    self.lbl_totales.configure(text=texto_kpi)

  def _on_recibo_selected(self, event):
    selected_items = self.tree_master.selection()
    if not selected_items:
      return

    item_id = selected_items[0]

    # Ignorar clic en la fila de TOTALES del inicio
    recibo_data = self.mapa_recibos.get(item_id)
    if not recibo_data:
      self._limpiar_tabla_detalles()
      self.lbl_detail_title.configure(text="DESGLOSE DE BAJADAS DE BALANZA")
      return

    self.recibo_seleccionado_uuid = recibo_data["uuid"]
    self.lbl_detail_title.configure(
        text=(
            f"DESGLOSE - RECIBO: {recibo_data['codigo_ticket']} | SOCIO:"
            f" {recibo_data['codigo_padron']}"
        )
    )
    self._cargar_detalles_recibo(self.recibo_seleccionado_uuid)

  def _cargar_detalles_recibo(self, recepcion_uuid: str):
    self._limpiar_tabla_detalles()

    detalles = self.recepcion_dao.obtener_detalles_por_recepcion_uuid(
        recepcion_uuid
    )

    for d in detalles:
      self.tree_detail.insert(
          "",
          "end",
          values=(
              f"#{d['orden']}",
              d.get("codigo_trazabilidad", "-"),
              d.get("destino", "MERCADO"),
              d["numero_sacos"],
              f"{d['peso_bruto']:.2f} kg",
              f"{d['peso_contable']:.2f} kg",
          ),
      )

  def _limpiar_tabla_detalles(self):
    for item in self.tree_detail.get_children():
      self.tree_detail.delete(item)

  # ----------------------------------------------------------------------
  # REIMPRESIÓN DE RECIBO SELECCIONADO
  # ----------------------------------------------------------------------
  def _reimprimir_recibo_seleccionado(self):
        """Obtiene los datos del recibo seleccionado en la tabla y los envía a la impresora."""
        # 1. Obtener directamente la selección activa del Treeview
        seleccion = self.tree_master.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un recibo de la tabla para reimprimir.")
            return

        item_id = seleccion[0]
        recibo_data = self.mapa_recibos.get(item_id)

        # Si el usuario selecciona la fila de Totales o no hay datos
        if not recibo_data:
            messagebox.showwarning("Atención", "Selección inválida. Seleccione un recibo válido.")
            return

        if not hasattr(self, "print_service") or not self.print_service:
            messagebox.showerror("Error", "Servicio de impresión no disponible.")
            return

        # 2. Consultar detalles desde el DAO
        detalles = self.recepcion_dao.obtener_detalles_por_recepcion_uuid(recibo_data["uuid"])

        todas_bajadas = []
        for d in detalles:
            # Compatibilidad si el DAO devuelve dict o Row de SQLite
            peso_val = d["peso_bruto"] if isinstance(d, dict) else d[5]
            sacos_val = d["numero_sacos"] if isinstance(d, dict) else d[4]
            dest_val = d["destino"] if isinstance(d, dict) else d[3]

            todas_bajadas.append({
                "destino": dest_val,
                "sacos": sacos_val,
                "peso": float(peso_val),
            })

        recibo_payload = {
            "codigo_ticket": recibo_data.get("codigo_ticket", "S/N"),
            "codigo_padron": recibo_data.get("codigo_padron", "-"),
            "socio_nombre": recibo_data.get("socio_nombre", "-"),
            "documento": recibo_data.get("dni") or "-",  # <--- Lee el DNI traído por el LEFT JOIN
            "codigo_parcela": recibo_data.get("codigo_parcela", "-"),
            "sector": recibo_data.get("sector", "-"),
            "fecha_pesaje": (
                recibo_data.get("fecha_pesaje")
                or recibo_data.get("created_at", "-")
            ),
            "total_sacos": recibo_data.get("total_sacos", sum(b["sacos"] for b in todas_bajadas)),
            "peso_total": sum(b["peso"] for b in todas_bajadas),
            "bajadas": todas_bajadas,
        }
        print(recibo_payload)

        try:
            exito = self.print_service.imprimir_recibo_dec(recibo_payload)
            if exito:
                messagebox.showinfo("Éxito", f"Recibo {recibo_data.get('codigo_ticket')} re-impreso correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo enviar la orden a la impresora.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al reimprimir: {e}")
  
  # ----------------------------------------------------------------------
  # SINCRONIZACIÓN ASÍNCRONA
  # ----------------------------------------------------------------------
  def _sincronizar(self):
    self.btn_sync_now.configure(state="disabled", text="SINCRONIZANDO...")
    self.lbl_sync_status.configure(text="Conectando...", text_color="#1E3A8A")

    threading.Thread(target=self._hilo_sincronizacion, daemon=True).start()

  def _hilo_sincronizacion(self):
    subidos = self.sync_service.subir_pesajes_pendientes()
    maestros_ok = self.sync_service.descargar_maestros()

    self.after(0, lambda: self._finalizar_sincronizacion(subidos, maestros_ok))

  def _finalizar_sincronizacion(self, subidos: int, maestros_ok: bool):
    self.btn_sync_now.configure(state="normal", text="SINCRONIZAR")

    if subidos > 0 or maestros_ok:
      msg = f"OK: Sincronización exitosa ({subidos} enviados)."
      self.lbl_sync_status.configure(text=msg, text_color="#15803D")
    else:
      self.lbl_sync_status.configure(
          text="INFO: Sin datos pendientes o sin red.", text_color="#B45309"
      )

    self.cargar_datos_locales()

  # ----------------------------------------------------------------------
  # EXPORTACIÓN EXCEL CON DATOS DEL SOCIO SEPARADOS EN COLUMNAS
  # ----------------------------------------------------------------------
  def exportar_excel(self):
    """Exporta el reporte en Excel con Cod Padron, DNI y Nombres en columnas separadas e independientes."""
    filas = self.tree_master.get_children()
    if not filas:
      messagebox.showwarning(
          "Atención", "No hay datos en la tabla para exportar."
      )
      return

    fecha_str = self.txt_fecha_filtro.get().strip()
    ruta_archivo = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Archivos de Excel", "*.xlsx")],
        initialfile=f"Resumen_Agricultores_{fecha_str}.xlsx",
        title="Guardar Resumen por Agricultor",
    )

    if not ruta_archivo:
      return

    try:
      resumen_socios = {}
      destinos_encontrados = set()

      for item_id in filas:
        recibo_data = self.mapa_recibos.get(item_id)
        if not recibo_data:
          continue

        cod_padron = recibo_data.get("codigo_padron", "-")
        dni_ruc = (
            recibo_data.get("numero_documento")
            or recibo_data.get("documento")
            or "-"
        )
        socio_nombre = recibo_data.get("socio_nombre", "-")

        clave_socio = (cod_padron, dni_ruc, socio_nombre)

        if clave_socio not in resumen_socios:
          resumen_socios[clave_socio] = {}

        detalles = self.recepcion_dao.obtener_detalles_por_recepcion_uuid(
            recibo_data["uuid"]
        )

        for d in detalles:
          dest = str(d.get("destino", "MERCADO")).upper()
          destinos_encontrados.add(dest)

          p_real = float(d.get("peso_bruto", 0.0))
          p_contable = float(d.get("peso_contable", 0.0))

          k_real = f"{dest}_REAL"
          k_cont = f"{dest}_CONT"

          resumen_socios[clave_socio][k_real] = (
              resumen_socios[clave_socio].get(k_real, 0.0) + p_real
          )
          resumen_socios[clave_socio][k_cont] = (
              resumen_socios[clave_socio].get(k_cont, 0.0) + p_contable
          )

      destinos_ordenados = sorted(list(destinos_encontrados))
      datos_excel = []

      for (cod_padron, dni_ruc, socio_nombre), valores in resumen_socios.items():
        fila = {
            "Cod Padrón": cod_padron,
            "DNI / RUC": dni_ruc,
            "Nombres y Apellidos": socio_nombre,
        }

        total_real_socio = 0.0
        total_cont_socio = 0.0

        for dest in destinos_ordenados:
          real = valores.get(f"{dest}_REAL", 0.0)
          cont = valores.get(f"{dest}_CONT", 0.0)

          fila[f"{dest} Real (kg)"] = round(real, 2)
          fila[f"{dest} Cont. Redondeado (kg)"] = round(cont)

          total_real_socio += real
          total_cont_socio += cont

        fila["Total (kg)"] = round(total_real_socio, 2)
        fila["Total Cont. (kg)"] = round(total_cont_socio)

        datos_excel.append(fila)

      df = pd.DataFrame(datos_excel)
      df.to_excel(ruta_archivo, index=False)

      messagebox.showinfo(
          "Éxito", f"Reporte exportado correctamente:\n{ruta_archivo}"
      )
    except Exception as e:
      messagebox.showerror(
          "Error", f"No se pudo exportar el archivo Excel:\n{str(e)}"
      )