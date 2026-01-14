import sqlite3

class InventarioModel:
    def __init__(self, db_name='inventario.db'):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # 1. Tabla Productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL,
                stock_critico INTEGER NOT NULL
            )
        ''')
        
        # 2. Tabla Ventas (Cabecera)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                total REAL NOT NULL
            )
        ''')
        
        # 3. Tabla Detalle Ventas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detalle_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')
        
        # 4. Tabla Gastos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL,
                categoria TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_all_products(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos")
        res = cursor.fetchall()
        conn.close()
        return res

    def add_product(self, nombre, precio, stock, stock_critico):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO productos (nombre, precio, stock, stock_critico) VALUES (?, ?, ?, ?)",
                           (nombre, precio, stock, stock_critico))
            conn.commit()
            return True
        finally:
            conn.close()

    def increase_stock_by_name(self, nombre, cantidad):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE nombre = ?", (cantidad, nombre))
        conn.commit()
        conn.close()

    def increase_stock_by_id(self, product_id, cantidad):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad, product_id))
        conn.commit()
        conn.close()

    def update_product(self, product_id, nombre, precio, stock, stock_critico):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET nombre = ?, precio = ?, stock = ?, stock_critico = ? WHERE id = ?",
                       (nombre, precio, stock, stock_critico, product_id))
        conn.commit()
        conn.close()

    def delete_product(self, product_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()

    def decrease_stock(self, product_id, quantity=1):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (quantity, product_id))
        conn.commit()
        conn.close()

    # ==========================================
    # NUEVOS METODOS (VENTAS Y GASTOS)
    # ==========================================
    
    def register_sale(self, items):
        """
        Registra una venta completa con sus detalles.
        items: lista de tuplas/objetos (producto_id, cantidad, precio_unitario)
        """
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Calcular total
            total_venta = sum(item['qty'] * item['info'][2] for item in items.values())
            fecha_actual = datetime.datetime.now().isoformat()
            
            # 1. Crear cabecera de venta
            cursor.execute("INSERT INTO ventas (fecha, total) VALUES (?, ?)", (fecha_actual, total_venta))
            venta_id = cursor.lastrowid
            
            # 2. Insertar detalles y descontar stock
            for pid, item in items.items():
                cantidad = item['qty']
                precio_unit = item['info'][2]
                subtotal = cantidad * precio_unit
                
                # Insertar detalle
                cursor.execute('''
                    INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (venta_id, pid, cantidad, precio_unit, subtotal))
                
                # Descontar stock
                cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cantidad, pid))
            
            conn.commit()
            return venta_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def add_expense(self, descripcion, monto, categoria="General"):
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            fecha_actual = datetime.datetime.now().isoformat()
            cursor.execute("INSERT INTO gastos (descripcion, monto, fecha, categoria) VALUES (?, ?, ?, ?)",
                           (descripcion, monto, fecha_actual, categoria))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_sales_report(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC")
        res = cursor.fetchall()
        conn.close()
        return res

    def get_expenses_report(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gastos ORDER BY fecha DESC")
        res = cursor.fetchall()
        conn.close()
        return res

