import customtkinter as ctk

class AperturaSesionView(ctk.CTkFrame):
    def __init__(self, parent, sesion_dao, on_sesion_abierta):
        super().__init__(parent, fg_color="#CBD5E1", corner_radius=0)
        self.sesion_dao = sesion_dao
        self.on_sesion_abierta = on_sesion_abierta

        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(
            self, 
            fg_color="#FFFFFF", 
            border_width=2, 
            border_color="#000000", 
            corner_radius=0, 
            width=520, 
            height=260
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        ctk.CTkLabel(
            card, 
            text="JORNADA DE ACOPIO", 
            font=("Arial", 20, "bold"), 
            text_color="#000000"
        ).pack(pady=(30, 8))

        ctk.CTkLabel(
            card, 
            text="No hay una sesion de pesaje activa en la balanza.\nAperture una nueva jornada para iniciar la recepcion de fruta.", 
            font=("Arial", 13), 
            text_color="#334155",
            justify="center"
        ).pack(pady=(0, 25), padx=20)

        self.btn_abrir = ctk.CTkButton(
            card,
            text="ABRIR NUEVA SESION DE ACOPIO",
            font=("Arial", 14, "bold"),
            fg_color="#16A34A",
            hover_color="#15803D",
            text_color="#FFFFFF",
            corner_radius=0,
            height=48,
            command=self._iniciar_jornada
        )
        self.btn_abrir.pack(padx=30, fill="x")

    def _iniciar_jornada(self):
        nueva_sesion = self.sesion_dao.abrir_nueva_sesion()
        if nueva_sesion and self.on_sesion_abierta:
            self.on_sesion_abierta(nueva_sesion)