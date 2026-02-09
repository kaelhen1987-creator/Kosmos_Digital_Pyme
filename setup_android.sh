#!/bin/bash

# 🚀 Digital PyME - Script de Configuración Pro para Android
# Autor: Gemini Pro Assistant

echo "---------------------------------------------------"
echo "🛠️  MODO DETALLADO: Iniciando configuración..."
echo "---------------------------------------------------"

# 1. Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual (venv)..."
    python3 -m venv venv
fi

# 2. Activar
echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# 3. Instalación con progreso visible
echo "📥 Instalando requerimientos (por favor espera)..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

echo "📱 Instalando soporte completo de Flet Android..."
pip install "flet[all]"

echo "---------------------------------------------------"
echo "✅ CONFIGURACIÓN COMPLETADA"
echo "---------------------------------------------------"

# Pregunta final corregida (compatibilidad universal)
echo -n "¿Deseas lanzar la aplicación en Android ahora? (s/n): "
read confirm

if [[ "$confirm" == "s" || "$confirm" == "S" ]]; then
    echo "🚀 Iniciando Flet en modo Android..."
    flet run --android
else
    echo "👋 Listo. Usa 'source venv/bin/activate' para trabajar en este entorno."
fi
