# 🏪 SOS Digital PyME - Sistema POS & Gestión Financiera

Sistema de Punto de Venta (POS) profesional desarrollado en **Python** y **Flet**, diseñado específicamente para empoderar a pequeñas y medianas empresas. Más que un simple registrador de ventas, es una herramienta de **Inteligencia de Negocios** que te revela "La Verdad Financiera" de tu operación en tiempo real.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flet](https://img.shields.io/badge/Flet-0.80.4-green)
![SQLite](https://img.shields.io/badge/SQLite-Integrated-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)

## 📋 Descripción

**SOS Digital PyME** transforma la complejidad financiera en simplicidad operativa. Elimina las "cuentas de servilleta" y ofrece un control estricto sobre el dinero, el inventario y los créditos.

El sistema se centra en la **transparencia del flujo de caja**, diferenciando claramente entre lo que vendiste (Venta Bruta) y el dinero que realmente entró a tu cajón, descontando fiados y sumando abonos de deudas pasadas.

## ✨ Características Principales

### 🖥️ Panel Financiero (Dashboard)
El corazón de tu negocio en tiempo real.
- **Métricas en Vivo**: Visualiza Ventas Brutas, Gastos Operativos y Ganancia Estimada del turno actual al instante.
- **Gestión de Gastos**: Registra salidas de dinero (proveedores, servicios, retiros) directamente en la caja para descontarlos automáticamente del cierre.
- **Alertas de Vencimiento**: Notificaciones visuales automáticas cuando tus productos están próximos a vencer (Semáforo de caducidad).

### 🛒 Punto de Venta (POS)
Rápido, intuitivo y a prueba de errores.
- **Carrito Inteligente**: Validación de stock en tiempo real (impide vender lo que no tienes).
- **Múltiples Medios de Pago**: Efectivo, Transferencia, Débito, Crédito y **Fiado (Cuenta Corriente)**.
- **Búsqueda Flexible**: Escanea códigos de barras o busca por nombre al vuelo.

### 👥 Cuaderno Digital (Gestión de Créditos)
Olvídate del cuaderno de papel. Profesionaliza los fiados.
- **Perfiles de Clientes**: Historial completo de compras y pagos.
- **Límites de Crédito**: Define cupos máximos por cliente. El sistema bloquea nuevas ventas fiadas si superan su límite.
- **Semáforo de Deudas**: Visualización rápida del estado de cuenta (Al Día / Deudor).
- **Abonos Parciales**: Registra pagos a cuenta de la deuda total.

### 📦 Inventario & Promociones
- **Gestión Completa**: Alta, baja y modificación de productos.
- **Stock Crítico**: Reportes de productos con bajo inventario.
- **Control de Vencimientos**: Fecha de expiración por lote/producto.

### 🔐 Control de Caja (Turnos)
Seguridad para el dueño y el cajero.
- **Apertura de Turno**: Obligatoria, registrando quién abre y con cuánto dinero (sencillo).
- **Cierre Blindado**: Al cerrar, el sistema calcula el "Dinero Esperado" (Monto Inicial + Ventas Efectivo + Abonos - Gastos). Cualquier diferencia queda registrada.

### 📊 Reportes Avanzados ("La Verdad Financiera")
Analiza el pasado para mejorar el futuro.
- **Filtros por Fecha**: Rangos personalizados.
- **Top Productos**: Descubre tus "Best Sellers" (Top 7, 15 y 30 días).
- **Desglose de Flujo**:
    - **Ventas Brutas**: Todo lo facturado.
    - **Dinero REAL**: Lo que efectivamente entró al bolsillo.
    - **Crédito Otorgado**: Dinero que está en la calle.
    - **Recuperación**: Deudas cobradas en el periodo.

### 🛡️ Seguridad & Activación
- **Hardware Lock**: Licenciamiento atado al hardware del equipo (evita piratería).
- **Sistema de Licencias**: Soporte para planes mensuales, trimestrales o anuales con fecha de caducidad encriptada.

## 🚀 Instalación y Ejecución

### Requisitos
- Python 3.10 o superior
- Flet 0.80.4

### Pasos
1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repo>
   cd SOSDIGITALPYME
   ```

2. **Crear entorno virtual (Opcional pero recomendado)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Mac/Linux
   # venv\Scripts\activate   # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   python3 main.py
   ```

## 📂 Estructura del Proyecto

```
SOSDIGITALPYME/
├── main.py                 # 🚀 Punto de entrada. Orquestador de navegación.
├── app/
│   ├── data/
│   │   └── database.py     # 🧠 Cerebro: Lógica de negocio y SQL.
│   ├── ui/
│   │   ├── dashboard_view.py # 📉 Panel principal y gastos.
│   │   ├── pos_view.py       # 🛒 Caja registradora.
│   │   ├── inventory_view.py # 📦 Gestión de productos.
│   │   ├── clients_view.py   # 👥 Cuaderno de fiados.
│   │   ├── reports_view.py   # 📊 Analíticas históricas.
│   │   └── shift_view.py     # 🕒 Apertura de turnos.
│   └── utils/
├── assets/                 # Recursos estáticos.
├── sos_pyme.db             # Base de datos local (SQLite).
└── requirements.txt        # Dependencias.
```

## 🛠️ Tecnologías

- **Frontend**: [Flet](https://flet.dev) (Framework de UI basado en Flutter para Python).
- **Backend**: Python puro.
- **Base de Datos**: SQLite3 (Integrada, sin configuración de servidor).
- **Empaquetado**: PyInstaller (para generar .exe y .app).

---
Desarrollado con ❤️ para impulsar el comercio local.
