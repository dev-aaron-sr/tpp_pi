import customtkinter as ctk
from ui.components.header_bar import HeaderBar
from ui.views.pesaje_view import PesajeView
from ui.views.apertura_sesion_view import AperturaSesionView
from ui.views.admin_view import AdminView
from ui.views.padron_view import PadronView
from ui.views.config_view import ConfiguracionView  # <--- 1. NUEVO IMPORT

class AppWindow(ctk.CTk):
    def __init__(self, agricultor_dao, recepcion_dao, sesion_dao, scale_service, print_service, sync_service):
        super().__init__()

        self.agricultor_dao = agricultor_dao
        self.recepcion_dao = recepcion_dao
        self.sesion_dao = sesion_dao
        self.scale_service = scale_service
        self.print_service = print_service
        self.sync_service = sync_service

        self.title("Intelisoft Industrial - Sistema de Pesaje")
        self.geometry("1024x600")
        self.minsize(1024, 600)
        self.configure(fg_color="#DCE0E5")

        self._build_ui()

    def _build_ui(self):
        self.header = HeaderBar(self, on_tab_change=self.cambiar_vista)
        self.header.pack(fill="x", side="top")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.pesaje_container = ctk.CTkFrame(self.container, fg_color="transparent")

        # 2. Registrar la vista de Configuración
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
            ),
            "CONFIG": ConfiguracionView(
                self.container,
                on_guardar_cb=self._al_guardar_configuracion  # Callback para reconectar balanza
            )
        }

        self.cambiar_vista("PESAJE")

    def _al_guardar_configuracion(self, nueva_config: dict):
        """Reconecta la balanza en vivo con el nuevo puerto COM sin reiniciar la App."""
        if hasattr(self.scale_service, 'reconnect'):
            self.scale_service.reconnect(
                port=nueva_config["balanza_port"], 
                baudrate=nueva_config["balanza_baudrate"]
            )

    def _cargar_modulo_pesaje(self):
        for widget in self.pesaje_container.winfo_children():
            widget.destroy()

        sesion_activa = self.sesion_dao.obtener_sesion_activa()

        if not sesion_activa:
            vista_apertura = AperturaSesionView(
                parent=self.pesaje_container,
                sesion_dao=self.sesion_dao,
                on_sesion_abierta=lambda ses: self._cargar_modulo_pesaje()
            )
            vista_apertura.pack(fill="both", expand=True)
        else:
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
        for view in self.views.values():
            view.pack_forget()

        if tab_name in self.views:
            if tab_name == "PESAJE":
                self._cargar_modulo_pesaje()

            self.views[tab_name].pack(fill="both", expand=True)

            if tab_name == "ADMIN":
                self.views["ADMIN"].cargar_datos_locales()