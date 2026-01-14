from app.data.database import InventarioModel
import os

# Usar una BD de prueba para no ensuciar la real
TEST_DB = "test_inventario.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

print("🚀 Iniciando Tests de Base de Datos...")
model = InventarioModel(TEST_DB)

# 1. Crear Producto
print("\n[1] Creando producto 'Test Item'...")
model.add_product("Test Item", 1000, 10, 2)
products = model.get_all_products()
assert len(products) == 1
pid, p_name, p_price, p_stock, p_crit = products[0]
print(f"✅ Producto creado: ID={pid}, Stock={p_stock}")

# 2. Registrar Venta
print("\n[2] Registrando venta de 2 unidades...")
cart_items = {
    pid: {
        'info': (pid, p_name, p_price, p_stock, p_crit),
        'qty': 2
    }
}
venta_id = model.register_sale(cart_items)
print(f"✅ Venta registrada con ID: {venta_id}")

# 3. Verificar Stock Descontado
print("\n[3] Verificando descuento de stock...")
updated_products = model.get_all_products()
new_stock = updated_products[0][3]
print(f"📉 Stock anterior: 10 -> Nuevo Stock: {new_stock}")
assert new_stock == 8
print("✅ Stock actualizado correctamente")

# 4. Verificar Registro de Venta
print("\n[4] Verificando tabla reportes...")
sales = model.get_sales_report()
print(f"📊 Total ventas registradas: {len(sales)}")
assert len(sales) == 1
assert sales[0][2] == 2000.0 # Total = 2 * 1000
print("✅ Reporte de ventas correcto")

# 5. Registrar Gasto
print("\n[5] Registrando gasto de prueba...")
model.add_expense("Compra insumos", 5000)
print("✅ Gasto registrado")

# Limpiar
os.remove(TEST_DB)
print("\n✨ TODOS LOS TESTS PASARON EXITOSAMENTE ✨")
