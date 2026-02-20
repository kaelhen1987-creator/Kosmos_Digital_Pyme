# 🏪 Digital PyME — Sistema POS & Gestión Financiera

Sistema de Punto de Venta (POS) multiplataforma desarrollado en **Python** y **Flet**, diseñado para empoderar a pequeñas y medianas empresas. Más que un registrador de ventas: es una herramienta de **Inteligencia de Negocios** que revela "La Verdad Financiera" de tu operación en tiempo real.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flet](https://img.shields.io/badge/Flet-0.80.4-green)
![SQLite](https://img.shields.io/badge/SQLite-Integrado-orange)
![Version](https://img.shields.io/badge/Versión-0.11.22-purple)
![Platforms](https://img.shields.io/badge/Plataformas-Windows%20%7C%20macOS%20%7C%20Android-informational)
![License](https://img.shields.io/badge/Licencia-Propietaria-red)

---

## 📋 Descripción

**Digital PyME** transforma la complejidad financiera en simplicidad operativa. Elimina las "cuentas de servilleta" y ofrece un control estricto sobre el dinero, el inventario y los créditos.

El sistema se centra en la **transparencia del flujo de caja**, diferenciando claramente entre lo que vendiste (Venta Bruta) y el dinero que realmente entró a tu cajón, descontando fiados y sumando abonos de deudas pasadas.

---

## ✨ Características Principales

### 🖥️ Panel Financiero (Dashboard)
El corazón de tu negocio en tiempo real.
- **Métricas en Vivo**: Ventas Brutas, Gastos Operativos y Ganancia Estimada del turno actual al instante.
- **Gestión de Gastos**: Registra salidas de dinero (proveedores, servicios, retiros) y se descuentan automáticamente del cierre.
- **Alertas de Vencimiento**: Semáforo de caducidad — notificaciones automáticas para productos próximos a vencer.

### 🛒 Punto de Venta (POS)
Rápido, intuitivo y a prueba de errores.
- **Carrito Inteligente**: Validación de stock en tiempo real (impide vender lo que no tienes).
- **Múltiples Medios de Pago**: Efectivo, Transferencia, Débito, Crédito y **Fiado (Cuenta Corriente)**.
- **Descuentos por Venta**: Aplica porcentaje de descuento directamente al total.
- **Búsqueda Flexible**: Escanea códigos de barras o busca por nombre al vuelo.
- **Promociones / Combos**: Crea productos compuestos que descuentan automáticamente los componentes del inventario.

### 👥 Cuaderno Digital (Gestión de Créditos)
Olvídate del cuaderno de papel. Profesionaliza los fiados.
- **Perfiles de Clientes**: Historial completo de compras a crédito y pagos recibidos.
- **Límites de Crédito**: Define cupos máximos por cliente. El sistema bloquea nuevas ventas fiadas si superan su límite.
- **Semáforo de Deudas**: Visualización rápida del estado de cuenta (Al Día / Deudor).
- **Abonos Parciales**: Registra pagos a cuenta de la deuda total con cualquier medio de pago.

### 📦 Inventario
- **Gestión Completa**: Alta, baja y modificación de productos con categorías.
- **Stock Crítico**: Alertas automáticas de productos con bajo inventario.
- **Control de Vencimientos**: Fecha de expiración por producto.
- **Código de Barras**: Asignación y búsqueda por código de barras.

### 🔐 Control de Caja (Turnos)
Seguridad para el dueño y el cajero.
- **Apertura de Turno**: Obligatoria, registrando usuario y monto inicial en caja.
- **Cierre Blindado**: Al cerrar, el sistema calcula el "Dinero Esperado" (Monto Inicial + Ventas Efectivo + Abonos − Gastos). Toda diferencia queda registrada.
- **Desglose por Método de Pago**: Visualiza ventas y pagos de deuda organizados por Efectivo, Débito, Crédito, Transferencia y Fiado.

### 📊 Reportes Avanzados ("La Verdad Financiera")
Analiza el pasado para mejorar el futuro.
- **Filtros por Fecha**: Rangos personalizados.
- **Top Productos**: Descubre tus "Best Sellers" (Top 7, 15 y 30 días).
- **Desglose de Flujo**:
    - **Ventas Brutas**: Todo lo facturado.
    - **Dinero REAL**: Lo que efectivamente entró al bolsillo.
    - **Crédito Otorgado**: Dinero que está en la calle.
    - **Recuperación**: Deudas cobradas en el periodo.
- **Historial Unificado de Ingresos**: Lista combinada de ventas y abonos ordenada cronológicamente.

### 🛡️ Seguridad & Activación
- **Hardware Lock**: Licenciamiento atado al hardware del equipo (evita piratería).
- **Suscripciones**: Soporte para planes de 1, 3, 6 y 12 meses con fecha de caducidad encriptada.
- **Generador de Licencias**: Herramientas CLI (`key_generator.py`) y GUI (`key_generator_gui.py`) para emitir llaves desde el panel del administrador.

### 🔄 Sistema de Actualizaciones (OTA)
- **Verificación Automática**: Al iniciar, la app consulta la API de GitHub Releases para detectar nuevas versiones.
- **Descarga por Plataforma**: Detecta automáticamente si es Android (.apk), Windows (.exe) o macOS (.dmg) y ofrece el archivo correcto.
- **Repositorio de Descargas**: Las releases se publican en [`kaelhen/SoS-Descargas`](https://github.com/kaelhen/SoS-Descargas) (público) para mantener el código fuente privado.

### 💾 Copia de Seguridad (Backup)
- **Un clic**: Genera una copia de la base de datos con fecha y nombre del negocio.
- **Destino Automático**: Se guarda en `~/Desktop/Digital_PyME_Backups/` (desktop).

### 📐 Diseño Responsivo
- **Desktop**: Barra de navegación con botones superiores y acceso rápido a Backup / Cerrar Caja.
- **Móvil (< 600px)**: AppBar con menú hamburguesa lateral (drawer) y navegación touch-friendly.
- **Transición automática**: La UI se adapta dinámicamente al redimensionar la ventana o según el dispositivo.

### 🏪 Configuración Inicial (Setup Wizard)
- Al primer uso, una pantalla guiada solicita nombre del negocio, dirección, dueño, teléfono y email.
- Los datos se almacenan en la configuración interna de la DB.

---

## 🚀 Instalación y Ejecución

### Requisitos
- Python 3.10 o superior (se desarrolló con 3.12)
- Flet ≥ 0.25.2 (probado con 0.80.4)
- Pillow

### Ejecución en Desarrollo
```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd SOSDIGITALPYME

# 2. Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
python3 main.py
```

### Builds de Producción (CI/CD)
Los builds se generan automáticamente vía **GitHub Actions** (`workflow_dispatch`):

| Plataforma | Workflow | Artefacto |
|-----------|----------|-----------|
| 🤖 Android | `build-android.yml` | `.apk` |
| 🍎 macOS | `build-macos.yml` | `.dmg` |
| 🪟 Windows | `build-windows.yml` | `.exe` (Installer vía Inno Setup) |

Los instaladores se publican como **GitHub Releases** en el repo de descargas público.

---

## 📂 Estructura del Proyecto

```
SOSDIGITALPYME/
├── main.py                     # 🚀 Punto de entrada. Orquestador de navegación y flujo.
├── requirements.txt            # Dependencias Python (flet, Pillow).
├── pyproject.toml              # Permisos Android (storage, internet).
├── installer.iss               # Script Inno Setup para generar instalador Windows.
│
├── app/
│   ├── data/
│   │   └── database.py         # 🧠 Modelo de datos: ~40 métodos SQL (CRUD, reportes, turnos).
│   ├── ui/
│   │   ├── activation_view.py  # 🔑 Pantalla de activación / ingreso de licencia.
│   │   ├── setup_view.py       # 🏪 Wizard de configuración inicial del negocio.
│   │   ├── shift_view.py       # 🕒 Apertura de turno (login de cajero).
│   │   ├── dashboard_view.py   # 📉 Panel principal: métricas, gastos, alertas.
│   │   ├── pos_view.py         # 🛒 Caja registradora / carrito / medios de pago.
│   │   ├── inventory_view.py   # 📦 Gestión de productos y stock.
│   │   ├── clients_view.py     # 👥 Cuaderno digital de fiados.
│   │   └── reports_view.py     # 📊 Reportes financieros e históricos.
│   └── utils/
│       ├── activation.py       # 🔐 Hardware lock, generación/verificación de licencias.
│       ├── updater.py          # 🔄 Verificación de actualizaciones (GitHub API).
│       ├── helpers.py          # 🛠️ Utilidades: detección móvil, mensajes snackbar.
│       └── formatting.py       # 💲 Formato de moneda.
│
├── assets/
│   ├── icon.png                # Ícono de la aplicación.
│   ├── manifest.json           # Manifiesto web (PWA).
│   ├── html5-qrcode.min.js     # Librería scanner de códigos de barras.
│   └── scanner_logic.js        # Lógica de integración del escáner.
│
├── key_generator.py            # 🔑 Generador de licencias (CLI).
├── key_generator_gui.py        # 🖥️ Generador de licencias (GUI con Flet).
│
├── .github/workflows/
│   ├── build-android.yml       # CI: Build APK Android.
│   ├── build-macos.yml         # CI: Build DMG macOS.
│   └── build-windows.yml       # CI: Build EXE Windows + Inno Setup Installer.
│
└── sos_pyme.db                 # Base de datos local (SQLite) — solo en dev.
```

---

## 🛠️ Tecnologías

| Capa | Tecnología |
|------|-----------|
| **Frontend** | [Flet](https://flet.dev) — UI multiplataforma basada en Flutter para Python |
| **Backend** | Python puro |
| **Base de Datos** | SQLite3 (integrada, sin servidor, con migración automática) |
| **Empaquetado** | `flet build` (para .apk, .app, .exe) + Inno Setup (para instalador Windows) |
| **CI/CD** | GitHub Actions (builds automáticos por plataforma) |
| **Actualizaciones** | GitHub Releases API (verificación OTA al iniciar) |

---

## 📝 Notas Técnicas

- **Persistencia de Datos**: La DB se almacena en `~/Documents/Digital_PyME/sos_pyme.db` para sobrevivir reinstalaciones. Incluye migración automática desde la carpeta de instalación y desde el nombre antiguo (`SOS_Digital_PyME`).
- **Migración de DB**: El modelo ejecuta migraciones incrementales automáticas al detectar versiones anteriores del esquema.
- **Modo Web**: La app soporta ejecución en modo `WEB_BROWSER` (desactivado por defecto), útil para debug en dispositivos iOS vía WiFi.

---

Desarrollado con ❤️ para impulsar el comercio local.
