import flet as ft

class ThemeManager:
    _instance = None

    # Tema Claro (Paleta Principal Solicitada por el Usuario)
    LIGHT = {
        "nav_bg": "#1e3a5f",
        "bg_color": "#ffffff",
        "surface": "#f8fafc",
        "border": "#e2e8f0",
        "revenue": "#2a7d4f", # Ingreso
        "expense": "#c0392b", # Gasto / Alertas
        "primary": "#f97316", # Cobrar / Acción principal
        "text_primary": "#1a1a1a",
        "text_secondary": "#555555",
        "field_bg": "#ffffff",
    }

    # Tema Oscuro (A implementar en el futuro, placeholders por ahora)
    DARK = {
        "nav_bg": "#2d2d2a",
        "bg_color": "#fafaf8",
        "surface": "#f2f2ee",
        "border": "#d8d8d0",
        "revenue": "#1a8a4a",
        "expense": "#b83232",
        "primary": "#5a8a00",
        "text_primary": "#1a1a1a",
        "text_secondary": "#555555",
        "field_bg": "#ffffff",
    }

    # Tema Intermedio (Grisáceo, a confirmar colores exactos)
    INTERMEDIATE = {
        "nav_bg": "#7b1d2a",
        "bg_color": "#ffffff",
        "surface": "#f9f4f5",
        "border": "#e8d8da",
        "revenue": "#166534",
        "expense": "#7b1d2a",
        "primary": "#b45309",
        "text_primary": "#1a1a1a",
        "text_secondary": "#555555",
        "field_bg": "#ffffff",
    }

    def __init__(self):
        if ThemeManager._instance is not None:
            raise Exception("Esta clase es un Singleton. Usa get_instance().")
        else:
            self.current_theme_name = "LIGHT"
            self.current_theme = getattr(self, self.current_theme_name)
            ThemeManager._instance = self

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls()
        return cls._instance

    def set_theme(self, theme_name: str):
        theme_name = theme_name.upper()
        if hasattr(self, theme_name):
            self.current_theme_name = theme_name
            self.current_theme = getattr(self, theme_name)
        else:
            print(f"Advertencia: Tema '{theme_name}' no existe. Cayendo a LIGHT.")
            self.current_theme_name = "LIGHT"
            self.current_theme = getattr(self, "LIGHT")

    def get_color(self, color_key: str) -> str:
        return self.current_theme.get(color_key, "#ff00ff") # Magenta brillante si no se encuentra (para debug fácil)

# Instancia global para fácil acceso
theme_manager = ThemeManager.get_instance()
