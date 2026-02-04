#!/usr/bin/env python3
"""
Script de prueba para simular comportamiento de Android
"""
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flet as ft
from main import main as main_app

# Wrapper para forzar plataforma Android
async def android_test_wrapper(page: ft.Page):
    # Forzar plataforma a Android
    original_platform = page.platform
    # Simulamos que page.platform devuelve el Enum, pero para efectos de este script
    # que corre en desktop, inyectamos el string "android" o un objeto compatible si fuera necesario.
    # Como main.py ahora hace str(page.platform).lower(), asignar "android" basta.
    page.platform = "android"
    print(f"🤖 MODO PRUEBA ANDROID ACTIVADO")
    print(f"Platform original: {original_platform}")
    print(f"Platform simulada: {page.platform}")
    print("-" * 50)
    
    # Ejecutar la app principal
    print("⚠️ NOTA: Si ejecutas esto en Mac/Windows, la parte de 'jnius' fallará")
    print("   o mostrará el error controlado en los logs.")
    await main_app(page)

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 MODO PRUEBA - SIMULANDO ANDROID")
    print("=" * 50)
    ft.app(target=android_test_wrapper)
