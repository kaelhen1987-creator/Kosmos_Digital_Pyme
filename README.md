# 🏪 SOS Digital PyME - Sistema POS

Sistema de Punto de Venta (POS) completo desarrollado con **Flet**, diseñado específicamente para pequeñas y medianas empresas (PyMEs). Optimizado para funcionar en modo web con interfaz responsive y una arquitectura robusta de control financiero.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flet](https://img.shields.io/badge/Flet-0.80.1-green)
![SQLite](https://img.shields.io/badge/SQLite-3-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Descripción

SOS Digital PyME es una solución integral que profesionaliza la gestión de tu negocio. No solo registra ventas, sino que te ofrece "La Verdad Financiera" de tu operación.

El sistema permite:
- **Gestionar Ventas e Inventario** con código de barras y alertas de stock.
- **Controlar Turnos y Caja** (Apertura y Cierre con rendición de dinero).
- **Manejar "Fiados" (Créditos)** mediante un Cuaderno Digital.
- **Visualizar Reportes Reales** calculando utilidad, flujo de caja y deudas.

## ✨ Características Principales

### 🛒 Punto de Venta (POS)
- **Carrito dinámico**: Validación de stock en tiempo real (impide vender más de lo que tienes).
- **Integridad de Datos**: Prevención de stock negativo a nivel de base de datos.
- **Búsqueda e Identificación**: Por nombre o código de barras.

### 🔐 Control de Turnos (Caja)
- **Apertura de Caja**: Obligatoria al iniciar. Registra usuario y monto inicial.
- **Cierre de Caja**: Rendición de monto final y desconexión segura.
- **Cálculo de Efectivo**: El sistema sabe exactamente cuánto dinero debería haber en el cajón (Monto Inicial + Ventas Efectivo + Abonos - Gastos).

### 👥 Cuaderno Digital (Gestión de Clientes)
- **Registro de Clientes**: Nombre, teléfono y alias.
- **Cuenta Corriente**:
  - Dar Fiado (Venta a crédito).
  - Registrar Abonos/Pagos.
  - Historial detallado de movimientos.
- **Semáforo de Deudas**: Visualización rápida de clientes con deuda (Rojo) o al día (Verde).

### 📊 La Verdad Financiera (Reportes)
- **Reporte por Fechas**: Filtra por día, mes o rango personalizado.
- **Métricas Clave**:
  - **Ventas Brutas**: Todo lo vendido (Efectivo + Crédito).
  - **Dinero REAL en Caja**: Flujo de caja neto (descuenta lo fiado, suma los abonos).
  - **Utilidad Operativa**: Ventas - Gastos.
- **Trazabilidad**: Diferenciación clara entre dinero físico y cuentas por cobrar.

### 📦 Gestión de Inventario
- CRUD completo de productos.
- Cálculo automático de Stock Crítico.
- Soporte para Códigos de Barras.

## 🚀 Instalación

### Requisitos Previos
- Python 3.10 o superior
- pip

### Pasos
1. **Clonar el repositorio**
```bash
git clone https://github.com/kaelhen/sosdigitalpyme.git
cd sosdigitalpyme
```

2. **Instalar dependencias**
```bash
pip install flet
```

3. **Ejecutar la aplicación**
```bash
# Modo web (recomendado)
python3 main.py
```
Acceder en navegador: `http://localhost:8080` (o el puerto indicado).

## 📁 Estructura del Proyecto

```
SOSDIGITALPYME/
├── main.py                 # Punto de entrada y navegación
├── sos_pyme.db            # Base de datos Principal
├── app/
│   ├── data/
│   │   └── database.py    # Modelo de datos y Lógica Financiera
│   ├── ui/
│   │   ├── shift_view.py      # Apertura/Cierre de Turnos
│   │   ├── pos_view.py        # Ventas
│   │   ├── inventory_view.py  # Inventario
│   │   ├── dashboard_view.py  # Finanzas Rápidas y Gastos
│   │   ├── clients_view.py    # Cuaderno Digital (Fiados)
│   │   └── reports_view.py    # Reportes Financieros Detallados
│   └── utils/
└── README.md
```

## 🗄️ Base de Datos

El sistema utiliza **SQLite** (`sos_pyme.db`) con un esquema relacional optimizado:
- `productos`: Inventario y códigos.
- `ventas` y `detalle_ventas`: Registro transaccional.
- `turnos`: Sesiones de caja (inicio/fin/montos).
- `clientes`: Información de contacto.
- `movimientos_cuenta`: Registro de deudas y pagos linkeados a ventas o abonos.
- `gastos`: Egresos operativos.

## 🎨 Diseño y UX

- **Enfoque Móvil**: Botones grandes, navegación simple.
- **Feedback Visual**:
  - Alertas de stock en rojo.
  - Indicadores de ganancia/pérdida.
  - Mensajes "Toast" para confirmaciones.

## 🔧 Soluciones Técnicas Destacadas

1. **Anti-Race Condition**: Verificación atómica de stock en `register_sale` antes de confirmar la venta.
2. **Shift Logic persistence**: El sistema recuerda si hay un turno abierto aunque se cierre la pestańa del navegador.
3. **Responsive Navigation**: Adaptación dinámica del menú según el dispositivo.

## 👤 Autor

**Kael Hen**
- GitHub: [@kaelhen](https://github.com/kaelhen)
- Proyecto: [sosdigitalpyme](https://github.com/kaelhen/sosdigitalpyme)

---
⭐ **SOS Digital PyME**: Profesionalizando el comercio de barrio.
