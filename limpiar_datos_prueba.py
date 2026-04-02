import sqlite3
import os

DB_PATH = "/Users/kaelhen/Documents/Digital_PyME/sos_pyme.db"

def reset_transactions():
    if not os.path.exists(DB_PATH):
        print("La base de datos no existe.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("Borrando ventas y detalles...")
    c.execute("DELETE FROM detalle_ventas")
    c.execute("DELETE FROM ventas")
    
    print("Borrando turnos de caja...")
    c.execute("DELETE FROM turnos")
    
    print("Borrando gastos de caja...")
    c.execute("DELETE FROM gastos")
    
    print("Borrando movimientos de fiados...")
    c.execute("DELETE FROM movimientos_cuenta")
    
    print("Reiniciando límites de crédito a 0...")
    c.execute("UPDATE clientes SET limite_credito = 0")
    
    print("Limpiando clientes (opcional, comentado)...")
    # c.execute("DELETE FROM clientes")
    
    conn.commit()
    conn.close()
    print("\n✅ Todas las ventas, turnos, movimientos y gastos de prueba han sido eliminados.")
    print("➡️ Tu catálogo de productos, categorías y configuraciones siguen intactos.")

if __name__ == "__main__":
    print("========================================")
    print(" LIMPIEZA DE DATOS DE PRUEBA (SOS PYME)")
    print("========================================")
    reset_transactions()

