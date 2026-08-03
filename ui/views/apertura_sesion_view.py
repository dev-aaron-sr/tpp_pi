import customtkinter as ctk

class AperturaSesionView(ctk.CTkFrame):
    def __init__(self, parent, sesion_dao, on_sesion_abierta):
        super().__init__(parent, fg_color="#CBD5E1", corner_radius=0)
        self.sesion_dao = sesion_dao
        self.on_sesion_abierta = on_sesion_abierta

        self._build_ui()

    def _build_ui(self):
        # Card Central
        card = ctk.CTkFrame(
            self, 
            fg_color="#FFFFFF", 
            border_width=2, 
            border_color="#1E3A8A", 
            corner_radius=8, 
            width=500, 
            height=280
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # Ícono / Título
        ctk.CTkLabel(
            card, 
            text="🚜 JORNADA DE ACOPIO", 
            font=("Segoe UI", 22, "bold"), 
            text_color="#1E3A8A"
        ).pack(pady=(30, 8))

        ctk.CTkLabel(
            card, 
            text="No hay una sesión de pesaje activa en la balanza.\nAperture una nueva jornada para iniciar la recepción de fruta.", 
            font=("Segoe UI", 12), 
            text_color="#475569",
            justify="center"
        ).pack(pady=(0, 25), padx=20)

        # Botón Verde de Apertura
        self.btn_abrir = ctk.CTkButton(
            card,
            text="🚀 ABRIR NUEVA SESIÓN DE ACOPIO",
            font=("Segoe UI", 14, "bold"),
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="#FFFFFF",
            corner_radius=4,
            height=50,
            command=self._iniciar_jornada
        )
        self.btn_abrir.pack(padx=30, fill="x")

    def _iniciar_jornada(self):
        """Crea la sesión en SQLite y notifica al contenedor principal."""
        nueva_sesion = self.sesion_dao.abrir_nueva_sesion()
        if nueva_sesion and self.on_sesion_abierta:
            self.on_sesion_abierta(nueva_sesion)