"""
Script final: Eliminar paletas estáticas del tema oscuro en archivos que quedaron sin refactorizar.
Reemplaza las variables globales BG, CARD_BG, ACCENT, DIM, etc. hardcodeadas a negro
por referencias a theme_manager.
"""
import re, os

def migrate_file(path: str, func_pattern: str):
    """Reemplaza definición de paleta global por inyección en función."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    
    # ---- 1. Eliminar bloque de paleta global al tope del archivo ----
    # Patrón: líneas seguidas que definen variables de color al inicio del módulo (antes de la función)
    content = re.sub(
        r'# ─+ Paleta [^\n]*\n(?:[A-Z_]+\s*=\s*"#[0-9a-fA-F]+"\s*\n)+',
        '',
        content
    )
    # También eliminar bloques sin encabezado
    content = re.sub(
        r'(?:^(?:[A-Z_]+\s*=\s*"#[0-9a-fA-F]+"\s*\n))+',
        '',
        content,
        flags=re.MULTILINE
    )

    # ---- 2. Si ya tiene theme_manager, no inyectar de nuevo ----
    if 'theme_manager' not in content:
        theme_inject = """    from app.utils.theme import theme_manager
    BG = theme_manager.get_color("bg_color")
    SURFACE = theme_manager.get_color("surface")
    BORDER = theme_manager.get_color("border")
    PRIMARY = theme_manager.get_color("primary")
    REVENUE = theme_manager.get_color("revenue")
    EXPENSE = theme_manager.get_color("expense")
    TEXT = theme_manager.get_color("text_primary")
    DIM = theme_manager.get_color("text_secondary")
    FIELD_BG = theme_manager.get_color("field_bg")
    ACCENT = theme_manager.get_color("nav_bg")
    CARD_BG = theme_manager.get_color("surface")
    PANEL_BG = theme_manager.get_color("surface")
"""
        # Encontrar primera función global y añadir justo después de los primeros ':' + newline
        m = re.search(func_pattern, content)
        if m:
            insert_pos = m.end()
            content = content[:insert_pos] + "\n" + theme_inject + content[insert_pos:]
        else:
            print(f"  ⚠ No se encontró función en {path}")
    
    # ---- 3. Reemplazar usos de variables viejas que no existen ya en el scope ----
    replacements = {
        # Variables viejas -> variables nuevas
        'TEXT_DIM': 'DIM',
        'PANEL_BG': 'SURFACE',
        'CARD_BG': 'SURFACE',
        'CART_BG': 'SURFACE',
        # Colores hardcodeados restantes que aún aparezcan
        'color="#2196F3"': 'color=PRIMARY',
        'color="#4CAF50"': 'color=REVENUE',
        'color="#F44336"': 'color=EXPENSE',
        'color="#aaaaaa"': 'color=DIM',
        'bgcolor="#FFF5F5"': 'bgcolor=SURFACE',
        'side=ft.BorderSide(2, "#2196F3")': 'side=ft.BorderSide(2, PRIMARY)',
        'side=ft.BorderSide(1, "#2196F3"), color="#2196F3"': 'side=ft.BorderSide(1, PRIMARY), color=PRIMARY',
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # ---- 4. Botones con bgcolor coloreado y color=TEXT -> color="white" ----
    for bg_var in ['ACCENT', 'PRIMARY', 'REVENUE', 'EXPENSE']:
        content = content.replace(f'bgcolor={bg_var}, color=TEXT', f'bgcolor={bg_var}, color="white"')
        content = content.replace(f'bgcolor={bg_var}, color=TEXT,', f'bgcolor={bg_var}, color="white",')
    
    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Migrado: {os.path.basename(path)}")
    else:
        print(f"⏭ Sin cambios: {os.path.basename(path)}")

# Archivos con paletas estáticas del tema oscuro que no se migraron bien
files_to_fix = [
    # (path, regex para la definición de la primera función)
    ('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/setup_view.py',
     r'def build_setup_view\([^)]*\):'),
    ('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/shift_view.py',
     r'def build_shift_view\([^)]*\):'),
    ('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/settings_view.py',
     r'def build_settings_view\([^)]*\):'),
    ('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/reports_view.py',
     r'def build_reports_view\([^)]*\):'),
    ('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/activation_view.py',
     r'def build_activation_view\([^)]*\):'),
]

# También limpiar los restantes en clients_view e inventory_view
files_to_fix += [
    ('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/clients_view.py', r'def build_clients_view\([^)]*\):'),
    ('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/inventory_view.py', r'def build_inventory_view\([^)]*\):'),
    ('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/dashboard_view.py', r'def build_dashboard_view\([^)]*\):'),
]

for path, pattern in files_to_fix:
    migrate_file(path, pattern)

print("\nListo!")
