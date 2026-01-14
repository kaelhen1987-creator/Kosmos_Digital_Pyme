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
                stock_critico INTEGER NOT NULL,
                codigo_barras TEXT
            )
        ''')
        
        # Migración: Agregar columna codigo_barras si no existe
        try:
            cursor.execute("ALTER TABLE productos ADD COLUMN codigo_barras TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # La columna ya existe
            pass
        
        # Crear índice para búsqueda rápida por código de barras
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_codigo_barras 
            ON productos(codigo_barras)
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

        # 5. Tabla Clientes (Cuaderno Digital)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                telefono TEXT,
                alias TEXT,
                limite_credito REAL DEFAULT 0
            )
        ''')

        # 6. Tabla Movimientos Cuenta (Deudas/Pagos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimientos_cuenta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                tipo TEXT NOT NULL, -- 'DEUDA' o 'PAGO'
                monto REAL NOT NULL,
                descripcion TEXT,
                venta_id INTEGER,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id),
                FOREIGN KEY (venta_id) REFERENCES ventas (id)
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

    def add_product(self, nombre, precio, stock, stock_critico, codigo_barras=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO productos (nombre, precio, stock, stock_critico, codigo_barras) VALUES (?, ?, ?, ?, ?)",
                           (nombre, precio, stock, stock_critico, codigo_barras))
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

    def update_product(self, product_id, nombre, precio, stock, stock_critico, codigo_barras=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET nombre = ?, precio = ?, stock = ?, stock_critico = ?, codigo_barras = ? WHERE id = ?",
                       (nombre, precio, stock, stock_critico, codigo_barras, product_id))
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
    
    def get_product_by_barcode(self, codigo_barras):
        """Buscar producto por código de barras (búsqueda exacta, case-insensitive)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE LOWER(codigo_barras) = LOWER(?) AND codigo_barras IS NOT NULL", 
                       (codigo_barras,))
        res = cursor.fetchone()
        conn.close()
        return res

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

    # ==========================================
    # METODOS CUADERNO DIGITAL (CLIENTES/DEUDAS)
    # ==========================================

    def add_client(self, nombre, telefono="", alias="", limite_credito=0):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO clientes (nombre, telefono, alias, limite_credito) VALUES (?, ?, ?, ?)",
                           (nombre, telefono, alias, limite_credito))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_clients_with_balance(self):
        """Retorna lista de clientes con su saldo calculado (Deuda - Pagos)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Consulta optimizada: Clientes con saldo
        query = '''
            SELECT 
                c.id, c.nombre, c.telefono, c.alias, c.limite_credito,
                COALESCE(SUM(CASE WHEN m.tipo = 'DEUDA' THEN m.monto ELSE 0 END), 0) as total_deuda,
                COALESCE(SUM(CASE WHEN m.tipo = 'PAGO' THEN m.monto ELSE 0 END), 0) as total_pagado
            FROM clientes c
            LEFT JOIN movimientos_cuenta m ON c.id = m.cliente_id
            GROUP BY c.id
            ORDER BY c.nombre
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        
        clients = []
        for r in rows:
            balance = r[5] - r[6] # Deuda - Pagado
            clients.append({
                "id": r[0],
                "nombre": r[1],
                "telefono": r[2],
                "alias": r[3],
                "limite": r[4],
                "deuda_total": r[5],
                "pagado_total": r[6],
                "saldo_actual": balance
            })
            
        conn.close()
        return clients

    def get_client_movements(self, cliente_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movimientos_cuenta WHERE cliente_id = ? ORDER BY fecha DESC", (cliente_id,))
        res = cursor.fetchall()
        conn.close()
        return res

    def add_movement(self, cliente_id, tipo, monto, descripcion, venta_id=None):
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            fecha_actual = datetime.datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO movimientos_cuenta (cliente_id, fecha, tipo, monto, descripcion, venta_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (cliente_id, fecha_actual, tipo, monto, descripcion, venta_id))
            conn.commit()
            return True
        finally:
            conn.close()

