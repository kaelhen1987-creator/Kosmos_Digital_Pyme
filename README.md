# 🏪 SOS Digital PyME - Sistema POS

Sistema de Punto de Venta (POS) completo desarrollado con **Flet**, diseñado específicamente para pequeñas y medianas empresas (PyMEs). Optimizado para funcionar en modo web con interfaz responsive.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Flet](https://img.shields.io/badge/Flet-0.80.1-green)
![SQLite](https://img.shields.io/badge/SQLite-3-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Descripción

SOS Digital PyME es una solución integral para la gestión de ventas, inventario y finanzas de pequeños negocios. El sistema permite:

- **Gestionar ventas** de forma rápida e intuitiva
- **Controlar inventario** con alertas de stock bajo
- **Registrar gastos** y visualizar estadísticas financieras
- **Acceder desde cualquier dispositivo** con navegador web

## ✨ Características Principales

### 🛒 Punto de Venta (POS)
- **Carrito de compras dinámico** con validación de stock en tiempo real
- **Búsqueda rápida** de productos
- **Checkout atómico** que actualiza ventas y stock simultáneamente
- **Interfaz responsive** adaptable a móvil y desktop
- **Visualización clara** de precios y disponibilidad

### 📦 Gestión de Inventario
- **CRUD completo** de productos (Crear, Leer, Actualizar, Eliminar)
- **Alertas visuales de stock**:
  - 🔴 Rojo: Stock crítico
  - 🟡 Amarillo: Stock bajo
  - ⚪ Blanco: Stock normal
- **Cálculo automático de IVA** (19%)
- **Búsqueda en tiempo real**
- **Edición y suma de stock** sin reemplazar valores

### 💰 Panel Financiero
- **Tarjetas de estadísticas** con diseño moderno:
  - Ventas totales (Azul)
  - Gastos totales (Naranja)
  - Ganancia neta (Verde/Rojo dinámico)
- **Registro de gastos** con formulario centrado
- **Historial** de últimas 10 ventas y gastos
- **Actualización automática** de totales

## 🚀 Instalación

### Requisitos Previos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

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
python3 main.py --web --port 8000

# Modo desktop (ventana nativa)
python3 main.py
```

4. **Acceder a la aplicación**
- **Computadora local**: http://127.0.0.1:8000
- **Red local**: http://[TU_IP]:8000 (limitaciones de seguridad en móvil)

## 📁 Estructura del Proyecto

```
SOSDIGITALPYME/
├── main.py                 # Punto de entrada y navegación
├── inventario.db          # Base de datos SQLite
├── app/
│   ├── data/
│   │   └── database.py    # Modelo de datos (SQLite)
│   ├── ui/
│   │   ├── pos_view.py    # Interfaz de Punto de Venta
│   │   ├── inventory_view.py  # Interfaz de Inventario
│   │   └── dashboard_view.py  # Interfaz de Finanzas
│   └── utils/
│       └── helpers.py     # Funciones compartidas
└── README.md
```

## 🗄️ Base de Datos

El sistema utiliza **SQLite** con las siguientes tablas:

### Productos
```sql
CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    stock INTEGER NOT NULL,
    stock_critico INTEGER DEFAULT 5
)
```

### Ventas
```sql
CREATE TABLE ventas (
    id INTEGER PRIMARY KEY,
    fecha TEXT NOT NULL,
    total REAL NOT NULL
)

CREATE TABLE ventas_detalle (
    id INTEGER PRIMARY KEY,
    venta_id INTEGER,
    producto_id INTEGER,
    cantidad INTEGER,
    precio_unitario REAL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
)
```

### Gastos
```sql
CREATE TABLE gastos (
    id INTEGER PRIMARY KEY,
    fecha TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    monto REAL NOT NULL
)
```

## 🎨 Diseño y UX

### Paleta de Colores
- **Azul** (#2196F3): Acciones principales, ventas
- **Verde** (#4CAF50): Éxito, ganancias
- **Naranja** (#FF9800): Advertencias, gastos
- **Rojo** (#F44336): Alertas críticas, pérdidas

### Características de Diseño
- ✅ **Sombras suaves** para profundidad visual
- ✅ **Bordes redondeados** (10-12px) para look moderno
- ✅ **Responsive** adaptable a móvil, tablet y desktop
- ✅ **Sin emojis** para máxima compatibilidad
- ✅ **Tipografía clara** con jerarquía visual

## 🔧 Soluciones Técnicas

### Compatibilidad con Flet 0.80.1

Durante el desarrollo se resolvieron varios problemas de compatibilidad:

1. **Navegación**: Uso de botones simples en lugar de `NavigationBar`/`NavigationRail` para evitar crashes
2. **Iconos**: Sintaxis correcta `ft.Icon(icon_name, ...)` en lugar de `ft.Icon(name=...)`
3. **Colores**: Uso de `ft.Colors.with_opacity()` (C mayúscula)
4. **Service Workers**: Acceso vía localhost para evitar bloqueos de seguridad

## 📱 Uso del Sistema

### 1. Configurar Inventario
1. Ir a la sección **Inventario**
2. Completar el formulario con:
   - Nombre del producto
   - Precio (sin IVA, se calcula automáticamente)
   - Stock inicial
   - Stock crítico (alerta)
3. Hacer clic en **Agregar Producto**

### 2. Realizar Ventas
1. Ir a **Ventas**
2. Buscar productos (opcional)
3. Hacer clic en las tarjetas de productos para agregarlos al carrito
4. Revisar el carrito (eliminar productos si es necesario)
5. Hacer clic en **COBRAR** para finalizar la venta

### 3. Registrar Gastos
1. Ir a **Finanzas**
2. Completar el formulario de gastos:
   - Descripción (ej: "Luz", "Internet")
   - Monto
3. Hacer clic en **Registrar Gasto**

### 4. Visualizar Estadísticas
- Las tarjetas superiores muestran totales en tiempo real
- El historial muestra las últimas 10 transacciones
- La ganancia se calcula automáticamente (Ventas - Gastos)

## ⚠️ Limitaciones Conocidas

- **Acceso móvil desde red local**: Los navegadores bloquean Service Workers en conexiones HTTP no-localhost. Para acceso desde dispositivos móviles en la red local, se requiere configurar HTTPS.
- **Modo web recomendado**: El sistema está optimizado para modo web. El modo desktop funciona pero puede tener diferencias visuales.

## 🛠️ Tecnologías Utilizadas

- **[Flet](https://flet.dev/)** 0.80.1 - Framework de UI basado en Flutter
- **Python** 3.14 - Lenguaje de programación
- **SQLite** 3 - Base de datos embebida
- **Material Design** - Sistema de diseño de Google

## 📝 Próximas Mejoras

- [ ] Soporte HTTPS para acceso móvil en red local
- [ ] Exportación de reportes a PDF/Excel
- [ ] Gráficos de ventas por período
- [ ] Sistema de usuarios y permisos
- [ ] Backup automático de base de datos
- [ ] Integración con impresoras térmicas

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👤 Autor

**Kael Hen**
- GitHub: [@kaelhen](https://github.com/kaelhen)
- Proyecto: [sosdigitalpyme](https://github.com/kaelhen/sosdigitalpyme)

## 🙏 Agradecimientos

- Equipo de [Flet](https://flet.dev/) por el excelente framework
- Comunidad de Python por las herramientas y soporte

---

⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub!
