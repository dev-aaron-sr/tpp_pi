import customtkinter as ctk
from ui.components.header_bar import HeaderBar
from ui.views.pesaje_view import PesajeView
from ui.views.apertura_sesion_view import AperturaSesionView  # <--- NUEVO IMPORT
from ui.views.admin_view import AdminView
from ui.views.padron_view import PadronView


class AppWindow(ctk.CTk):
    def __init__(self, agricultor_dao, recepcion_dao, sesion_dao, scale_service, print_service, sync_service):
        super().__init__()

        self.agricultor_dao = agricultor_dao
        self.recepcion_dao = recepcion_dao
        self.sesion_dao = sesion_dao  # <--- RECIBE EL DAO
        self.scale_service = scale_service
        self.print_service = print_service
        self.sync_service = sync_service

        # Ventana Base
        self.title("Intelisoft Industrial - Sistema de Pesaje")
        self.geometry("1024x600")
        self.minsize(1024, 600)
        self.configure(fg_color="#DCE0E5")

        self._build_ui()

    def _build_ui(self):
        # 1. Header Bar Único
        self.header = HeaderBar(self, on_tab_change=self.cambiar_vista)
        self.header.pack(fill="x", side="top")

        # 2. Contenedor Dinámico para Vistas
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # 3. Contenedor wrapper para el área de Pesaje (Apertura o Balanza)
        self.pesaje_container = ctk.CTkFrame(self.container, fg_color="transparent")

        # Diccionario de Vistas Principal
        self.views = {
            "PESAJE": self.pesaje_container,
            "ADMIN": AdminView(
                self.container, 
                self.recepcion_dao, 
                self.sync_service
            ),
            "PADRON": PadronView(
                self.container, 
                self.agricultor_dao, 
                self.sync_service
            )
        }

        # Vista por defecto: Pesaje
        self.cambiar_vista("PESAJE")

    def _cargar_modulo_pesaje(self):
        """Alterna limpiamente entre la vista de Apertura y la de Pesaje según la BD."""
        # Limpiar cualquier widget previo en el contenedor de pesaje
        for widget in self.pesaje_container.winfo_children():
            widget.destroy()

        sesion_activa = self.sesion_dao.obtener_sesion_activa()

        if not sesion_activa:
            # Opción A: No hay sesión -> Mostrar pantalla limpia de bienvenida/apertura
            vista_apertura = AperturaSesionView(
                parent=self.pesaje_container,
                sesion_dao=self.sesion_dao,
                on_sesion_abierta=lambda ses: self._cargar_modulo_pesaje()
            )
            vista_apertura.pack(fill="both", expand=True)
        else:
            # Opción B: Sesión activa -> Cargar vista completa de pesaje
            vista_pesaje = PesajeView(
                parent=self.pesaje_container,
                agricultor_dao=self.agricultor_dao,
                recepcion_dao=self.recepcion_dao,
                sesion_dao=self.sesion_dao,
                scale_service=self.scale_service,
                print_service=self.print_service,
                sesion_activa=sesion_activa,
                on_cerrar_sesion_cb=lambda: self._cargar_modulo_pesaje()
            )
            vista_pesaje.pack(fill="both", expand=True)

    def cambiar_vista(self, tab_name: str):
        """Oculta la vista activa y muestra la seleccionada."""
        for view in self.views.values():
            view.pack_forget()

        if tab_name in self.views:
            # Si se selecciona PESAJE, recargamos el estado de sesión dinámicamente
            if tab_name == "PESAJE":
                self._cargar_modulo_pesaje()

            self.views[tab_name].pack(fill="both", expand=True)

            if tab_name == "ADMIN":
                self.views["ADMIN"].cargar_datos_locales()