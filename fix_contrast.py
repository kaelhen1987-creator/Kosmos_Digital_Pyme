"""
Script de corrección: Fix contraste de colores.
El problema: color=TEXT se aplicó incorrectamente en textos/iconos dentro de 
botones de color (EXPENSE, PRIMARY, REVENUE, ACCENT, GREEN), donde debería 
seguir siendo "white".

Estrategia:
1. Reemplazar patrones donde bgcolor=COLOR, color=TEXT por bgcolor=COLOR, color="white"
2. Corregir SnackBar (bgcolor=RED, color=TEXT -> color="white")
3. En campos de texto (TextField), color=TEXT es CORRECTO (texto oscuro sobre fondo claro)
"""
import re
import os
import glob

FILES = glob.glob('/Users/kaelhen/Desktop/SOSDIGITALPYME/app/ui/*.py')
FILES.append('/Users/kaelhen/Desktop/SOSDIGITALPYME/main.py')

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    
    # Patrón 1: ButtonStyle con bgcolor=COLOR, color=TEXT -> color="white"
    # Esto cubre ft.ButtonStyle(bgcolor=X, color=TEXT, ...) y
    # ft.ButtonStyle(color=TEXT, bgcolor=X, ...)
    
    # Los patrones más comunes que generaron el bug:
    fixes = [
        # FilledButton / ButtonStyle con bgcolor coloreado y color=TEXT
        ('style=ft.ButtonStyle(bgcolor=ACCENT, color=TEXT', 'style=ft.ButtonStyle(bgcolor=ACCENT, color="white"'),
        ('style=ft.ButtonStyle(bgcolor=PRIMARY, color=TEXT', 'style=ft.ButtonStyle(bgcolor=PRIMARY, color="white"'),
        ('style=ft.ButtonStyle(bgcolor=REVENUE, color=TEXT', 'style=ft.ButtonStyle(bgcolor=REVENUE, color="white"'),
        ('style=ft.ButtonStyle(bgcolor=EXPENSE, color=TEXT', 'style=ft.ButtonStyle(bgcolor=EXPENSE, color="white"'),
        ('style=ft.ButtonStyle(bgcolor=GREEN, color=TEXT', 'style=ft.ButtonStyle(bgcolor=GREEN, color="white"'),
        ('style=ft.ButtonStyle(bgcolor=RED, color=TEXT', 'style=ft.ButtonStyle(bgcolor=RED, color="white"'),

        # FilledButton con bgcolor inline
        ('bgcolor=ACCENT, color=TEXT', 'bgcolor=ACCENT, color="white"'),
        ('bgcolor=PRIMARY, color=TEXT', 'bgcolor=PRIMARY, color="white"'),
        ('bgcolor=REVENUE, color=TEXT', 'bgcolor=REVENUE, color="white"'),
        ('bgcolor=EXPENSE, color=TEXT', 'bgcolor=EXPENSE, color="white"'),
        ('bgcolor=GREEN, color=TEXT', 'bgcolor=GREEN, color="white"'),
        ('bgcolor=RED, color=TEXT', 'bgcolor=RED, color="white"'),
        ('bgcolor=CART_BG, color=TEXT', 'bgcolor=CART_BG, color=TEXT'),  # CART_BG es claro -> TEXT está bien
        
        # color=TEXT, bgcolor (inverso)
        ('color=TEXT, bgcolor=ACCENT', 'color="white", bgcolor=ACCENT'),
        ('color=TEXT, bgcolor=PRIMARY', 'color="white", bgcolor=PRIMARY'),
        ('color=TEXT, bgcolor=REVENUE', 'color="white", bgcolor=REVENUE'),
        ('color=TEXT, bgcolor=EXPENSE', 'color="white", bgcolor=EXPENSE'),
        ('color=TEXT, bgcolor=GREEN', 'color="white", bgcolor=GREEN'),
        ('color=TEXT, bgcolor=RED', 'color="white", bgcolor=RED'),
        
        # SnackBar: icono con color=TEXT sobre fondo EXPENSE/RED coloreado
        ('ft.Icon(ft.Icons.WARNING_ROUNDED, color=TEXT)', 'ft.Icon(ft.Icons.WARNING_ROUNDED, color="white")'),
        
        # Texto en SnackBar sobre fondo coloreado (se detecta por el bgcolor=RED luego)
        # Se maneja en la revisión contextual abajo
        
        # nav_bg -> texto debe ser blanco
        ('bgcolor=theme_manager.get_color("nav_bg"), color=TEXT', 'bgcolor=theme_manager.get_color("nav_bg"), color="white"'),
        
        # FilledButton con color inline después de bgcolor de nav_bg
        ('bgcolor=ACCENT, color=TEXT,', 'bgcolor=ACCENT, color="white",'),
        
        # En delete confirm dialog, texto de botón
        ('bgcolor=EXPENSE, color=TEXT,', 'bgcolor=EXPENSE, color="white",'),
        ('bgcolor=EXPENSE, color="white",', 'bgcolor=EXPENSE, color="white",'), # idempotente
        
        # Para botones de Cobrar, Efectivo etc
        ('bgcolor=PRIMARY, color=TEXT,', 'bgcolor=PRIMARY, color="white",'),
        ('bgcolor=REVENUE, color=TEXT,', 'bgcolor=REVENUE, color="white",'),
    ]
    
    # Aplicar fixes simples
    for old, new in fixes:
        content = content.replace(old, new)
    
    # Fix contextual: ft.Text con color=TEXT dentro de SnackBar con bgcolor rojo/coloreado
    # Patrón: dentro de SnackBar con bgcolor=RED en la misma llamada:
    # ft.Text("...texto...", color=TEXT, weight="bold") -> weight debería seguir siendo bold
    content = re.sub(
        r'(ft\.SnackBar\s*\()([^)]*bgcolor=(?:RED|EXPENSE))(.+?)(ft\.Text\([^)]+color=)TEXT',
        lambda m: m.group(1) + m.group(2) + m.group(3) + m.group(4) + '"white"',
        content, flags=re.DOTALL
    )
    
    # Fix del label_style en Dropdown (label_style=ft.TextStyle(color=TEXT) está BIEN sobre fondo claro)
    # NO cambiar este
    
    # Fix para PopupMenuItem texto con color=EXPENSE (está bien - es el ícono de eliminar)
    # Ya está correcto
    
    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Corregido: {os.path.basename(path)}")
    else:
        print(f"Sin cambios: {os.path.basename(path)}")

for f in FILES:
    fix_file(f)

print("\nDone.")
