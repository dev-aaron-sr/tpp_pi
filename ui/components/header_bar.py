import customtkinter as ctk

class HeaderBar(ctk.CTkFrame):
    def __init__(self, parent, on_tab_change):
        super().__init__(parent, fg_color="#003B73", height=50, corner_radius=0)
        self.on_tab_change = on_tab_change
        self.pack_propagate(False)

        self._build_ui()

    def _build_ui(self):
        # Logo / Marca Industrial (Izquierda)
        self.lbl_logo = ctk.CTkLabel(
            self, 
            text="intelisoft INDUSTRIAL", 
            font=("Segoe UI", 18, "bold"), 
            text_color="#FFFFFF"
        )
        self.lbl_logo.pack(side="left", padx=15)

        # Indicador de Balanza Único (Centro/Izquierda)
        self.frame_status = ctk.CTkFrame(self, fg_color="#002855", corner_radius=15, height=28)
        self.frame_status.pack(side="left", padx=20)

        self.lbl_balanza_status = ctk.CTkLabel(
            self.frame_status, 
            text="● BALANZA EN LÍNEA", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#22C55E"
        )
        self.lbl_balanza_status.pack(padx=12, pady=3)

        # Botones de Pestañas Principales (Derecha)
        self.btn_padron = ctk.CTkButton(
            self, 
            text="libro padron", 
            font=("Segoe UI", 13, "bold"),
            fg_color="#FFFFFF", 
            text_color="#000000",
            hover_color="#E2E8F0",
            corner_radius=10,
            width=130,
            height=32,
            command=lambda: self._select_tab("PADRON")
        )
        self.btn_padron.pack(side="right", padx=(5, 15), pady=8)

        self.btn_admin = ctk.CTkButton(
            self, 
            text="administracion", 
            font=("Segoe UI", 13, "bold"),
            fg_color="#FFFFFF", 
            text_color="#000000",
            hover_color="#E2E8F0",
            corner_radius=10,
            width=130,
            height=32,
            command=lambda: self._select_tab("ADMIN")
        )
        self.btn_admin.pack(side="right", padx=(5, 15), pady=8)

        self.btn_pesaje = ctk.CTkButton(
            self, 
            text="pesaje", 
            font=("Segoe UI", 13, "bold"),
            fg_color="#FFFFFF", 
            text_color="#000000",
            hover_color="#E2E8F0",
            corner_radius=10,
            width=100,
            height=32,
            command=lambda: self._select_tab("PESAJE")
        )
        self.btn_pesaje.pack(side="right", padx=5, pady=8)

        self.btn_pesaje = ctk.CTkButton(
            self, 
            text="Configuracion", 
            font=("Segoe UI", 13, "bold"),
            fg_color="#FFFFFF", 
            text_color="#000000",
            hover_color="#E2E8F0",
            corner_radius=10,
            width=100,
            height=32,
            command=lambda: self._select_tab("CONFIG")
        )
        self.btn_pesaje.pack(side="right", padx=5, pady=8)

    def set_balanza_status(self, online: bool):
        """Actualiza el indicador visual de la balanza dinámicamente."""
        if online:
            self.lbl_balanza_status.configure(text="● BALANZA EN LÍNEA", text_color="#22C55E")
        else:
            self.lbl_balanza_status.configure(text="● BALANZA DESCONECTADA", text_color="#EF4444")

    def _select_tab(self, tab_name: str):
        self.on_tab_change(tab_name)