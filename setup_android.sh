#!/bin/bash

# 🚀 SOS Digital PyME - Script de Configuración Pro para Android
# Autor: Gemini Pro Assistant

echo "---------------------------------------------------"
echo "🛠️  Iniciando configuración del entorno Android..."
echo "---------------------------------------------------"

# 1. Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual (venv)..."
    python3 -m venv venv
else
    echo "✅ El entorno virtual ya existe."
fi

# 2. Activar el entorno virtual
echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# 3. Actualizar pip e instalar dependencias
echo "📥 Instalando dependencias necesarias..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# 4. Asegurar soporte para Flet Android
echo "📱 Instalando soporte nativo para Flet Android..."
pip install "flet[all]"

echo "---------------------------------------------------"
echo "✅ Entorno listo."
echo "---------------------------------------------------"
echo "⚠️  RECUERDA: Debes tener el emulador de Android Studio encendido"
echo "    o tu teléfono conectado por USB con Depuración activada."
echo "---------------------------------------------------"

read -p "¿Deseas lanzar la aplicación en Android ahora? (s/n): " confirm
if [[ $confirm == [sS] ]]; then
    echo "🚀 Lanzando flet run --android..."
    flet run --android
else
    echo "👋 Configuración finalizada. Para correr la app luego usa: flet run --android"
fi
