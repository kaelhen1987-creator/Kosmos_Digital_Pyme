import sqlite3

class InventarioModel:
    def __init__(self, db_name='sos_pyme.db'):
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
            pass # Ya existe
            
        # Migración: Agregar columna categoria si no existe (Modo Café)
        try:
            cursor.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'General'")
            conn.commit()
        except sqlite3.OperationalError:
            pass # Ya existe
        
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
        
        # Migración: Agregar columna medio_pago a ventas si no existe
        try:
            cursor.execute("ALTER TABLE ventas ADD COLUMN medio_pago TEXT DEFAULT 'EFECTIVO'")
            conn.commit()
        except sqlite3.OperationalError:
            pass # Ya existe
        
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

        # 7. Tabla Turnos (Control de Caja)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT,
                monto_inicial REAL NOT NULL,
                monto_final REAL,
                usuario TEXT
            )
        ''')

        # 8. Tabla Items de Promocion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promocion_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                promocion_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                FOREIGN KEY (promocion_id) REFERENCES productos (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')

        # 9. Tabla Configuración (Key-Value)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    # ==========================================
    # METODOS CONFIGURACION
    # ==========================================
    def get_config(self, key, default=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else default

    def set_config(self, key, value):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()

    # ==========================================
    # METODOS CRUD PRODUCTOS
    # ==========================================
    
    # --- MIGRACION VENCIMIENTO ---
    def _ensure_expiration_column(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE productos ADD COLUMN fecha_vencimiento TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass # Ya existe
        conn.close()
    
    def get_all_products(self):
        self._ensure_expiration_column()
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos")
        res = cursor.fetchall()
        
        # Procesar para calcular stock dinámico de Promociones
        final_res = []
        for p in res:
            # Schema: id, nombre, precio, stock, critico, barcode, categoria
            # Check length just in case
            p_cat = "General"
            if len(p) >= 7: p_cat = p[6]
            
            if p_cat == "Promociones":
                # Calcular stock máximo disponible basado en componentes
                cursor.execute("SELECT producto_id, cantidad FROM promocion_items WHERE promocion_id = ?", (p[0],))
                comps = cursor.fetchall()
                if not comps:
                    real_stock = 0
                else:
                    possible_stocks = []
                    for c_pid, c_qty in comps:
                        cursor.execute("SELECT stock FROM productos WHERE id = ?", (c_pid,))
                        c_res = cursor.fetchone()
                        c_stock = c_res[0] if c_res else 0
                        # Cuantos paquetes puedo armar con este item?
                        possible_stocks.append(c_stock // c_qty)
                    real_stock = min(possible_stocks) if possible_stocks else 0
                
                # Reconstruir tupla con nuevo stock
                # Tuplas son inmutables
                p_list = list(p)
                p_list[3] = real_stock # Index 3 is stock
                final_res.append(tuple(p_list))
            else:
                final_res.append(p)

        conn.close()
        return final_res

    def add_product(self, nombre, precio, stock, stock_critico, codigo_barras=None, categoria="General", fecha_vencimiento=None):
        self._ensure_expiration_column()
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO productos (nombre, precio, stock, stock_critico, codigo_barras, categoria, fecha_vencimiento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, precio, stock, stock_critico, codigo_barras, categoria, fecha_vencimiento))
            conn.commit()
        except sqlite3.IntegrityError:
            raise Exception(f"El producto '{nombre}' ya existe.")
        finally:
            conn.close()

    def update_product(self, product_id, nombre, precio, stock, stock_critico, codigo_barras=None, categoria="General", fecha_vencimiento=None):
        self._ensure_expiration_column()
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE productos 
            SET nombre = ?, precio = ?, stock = ?, stock_critico = ?, codigo_barras = ?, categoria = ?, fecha_vencimiento = ?
            WHERE id = ?
        ''', (nombre, precio, stock, stock_critico, codigo_barras, categoria, fecha_vencimiento, product_id))
        conn.commit()
        conn.close()

    def get_expiring_products(self, days_threshold=7):
        self._ensure_expiration_column()
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        today = datetime.date.today().isoformat()
        future_limit = (datetime.date.today() + datetime.timedelta(days=days_threshold)).isoformat()
        
        # Buscar productos vencidos y por vencer (<= today + 7)
        cursor.execute('''
            SELECT * FROM productos 
            WHERE fecha_vencimiento IS NOT NULL 
            AND fecha_vencimiento != ''
            AND fecha_vencimiento <= ?
        ''', (future_limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_product(self, product_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (product_id,))
        conn.commit()
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

    def update_stock(self, product_id, quantity):
        """Metodo alias para actualizar stock desde UI"""
        self.increase_stock_by_id(product_id, quantity)

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
        
        # Si es promo, calcular stock
        if res:
            p_cat = "General"
            if len(res) >= 7: p_cat = res[6]
            
            if p_cat == "Promociones":
                cursor.execute("SELECT producto_id, cantidad FROM promocion_items WHERE promocion_id = ?", (res[0],))
                comps = cursor.fetchall()
                real_stock = 0
                if comps:
                    possible_stocks = []
                    for c_pid, c_qty in comps:
                        cursor.execute("SELECT stock FROM productos WHERE id = ?", (c_pid,))
                        c_res = cursor.fetchone()
                        c_stock = c_res[0] if c_res else 0
                        possible_stocks.append(c_stock // c_qty)
                    real_stock = min(possible_stocks) if possible_stocks else 0
                
                p_list = list(res)
                p_list[3] = real_stock
                res = tuple(p_list)

        conn.close()
        return res

    # ==========================================
    # LOGICA DE PROMOCIONES
    # ==========================================

    def add_promotion(self, nombre, precio, componentes):
        """
        Crea una promoción (Producto ficticio) y sus items.
        componentes: lista de tuplas (producto_id, cantidad)
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            # 1. Crear producto tipo "Promoción"
            # Stock ficticio 0, pero no importa porque no se descuenta.
            # Se puede usar stock para limitar la promo, pero por ahora ilimitado (controlado por componentes)
            cursor.execute('''
                INSERT INTO productos (nombre, precio, stock, stock_critico, codigo_barras, categoria)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nombre, precio, 0, 0, None, "Promociones"))
            promo_id = cursor.lastrowid
            
            # 2. Insertar componentes
            for pid, qty in componentes:
                cursor.execute('''
                    INSERT INTO promocion_items (promocion_id, producto_id, cantidad)
                    VALUES (?, ?, ?)
                ''', (promo_id, pid, qty))
            
            conn.commit()
            return promo_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_promotion_items(self, promo_id):
        """Retorna componentes de una promo: [(prod_id, cant_requerida)]"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT producto_id, cantidad FROM promocion_items WHERE promocion_id = ?", (promo_id,))
        res = cursor.fetchall()
        conn.close()
        return res

    # ==========================================
    # NUEVOS METODOS (VENTAS Y GASTOS)
    # ==========================================
    
    def register_sale(self, items, medio_pago='EFECTIVO', discount_percent=0):
        """
        Registra una venta completa con sus detalles.
        items: lista de tuplas/objetos (producto_id, cantidad, precio_unitario)
        medio_pago: EFECTIVO, TRANSFERENCIA, DEBITO, CREDITO, DEUDA
        discount_percent: Porcentaje de descuento (0-100)
        """
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Calcular total bruto
            subtotal_venta = sum(item['qty'] * item['info'][2] for item in items.values())
            
            # Aplicar Descuento
            descuento_monto = subtotal_venta * (discount_percent / 100.0)
            total_venta = subtotal_venta - descuento_monto
            
            fecha_actual = datetime.datetime.now().isoformat()
            
            # 1. Crear cabecera de venta
            cursor.execute("INSERT INTO ventas (fecha, total, medio_pago) VALUES (?, ?, ?)", (fecha_actual, total_venta, medio_pago))
            venta_id = cursor.lastrowid
            
            # 2. Insertar detalles y descontar stock
            for pid, item in items.items():
                cantidad_venta = item['qty']
                precio_unit = item['info'][2]
                subtotal = cantidad_venta * precio_unit
                
                # Insertar detalle de venta (lo que el cliente ve)
                cursor.execute('''
                    INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (venta_id, pid, cantidad_venta, precio_unit, subtotal))

                # --- LOGICA DE STOCK (Normal vs Promoción) ---
                
                # Chequear si es promo
                cursor.execute("SELECT producto_id, cantidad FROM promocion_items WHERE promocion_id = ?", (pid,))
                promo_components = cursor.fetchall()
                
                if promo_components:
                    # ES UNA PROMO: Descontar stock de sus componentes
                    for comp_pid, comp_qty in promo_components:
                        total_deduct = comp_qty * cantidad_venta
                        
                        # Verificar Stock Componente
                        cursor.execute("SELECT stock, nombre FROM productos WHERE id = ?", (comp_pid,))
                        curr = cursor.fetchone()
                        if not curr:
                            raise Exception(f"Componente ID {comp_pid} no existe")
                        
                        c_stock, c_name = curr
                        if c_stock < total_deduct:
                             raise Exception(f"Stock insuficiente de componente '{c_name}' para la promoción.")
                             
                        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (total_deduct, comp_pid))
                
                else:
                    # PRODUCTO NORMAL
                    cursor.execute("SELECT stock, nombre FROM productos WHERE id = ?", (pid,))
                    curr = cursor.fetchone()
                    if not curr:
                        raise Exception(f"Producto ID {pid} no existe")
                    
                    current_stock, prod_name = curr
                    
                    # Ignoramos stock check si es solo 'Promociones' category sin components? 
                    # No, debería tener componentes si es promo. Si no tiene, se comporta como normal.
                    
                    if current_stock < cantidad_venta:
                        raise Exception(f"Stock insuficiente para {prod_name}. Stock actual: {current_stock}")
                    
                    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cantidad_venta, pid))
            
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

    def get_payments_report(self):
        """Retorna todos los movimientos de tipo PAGO (Abonos) con nombre de cliente"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Incluir c.nombre al final
        cursor.execute('''
            SELECT m.*, c.nombre 
            FROM movimientos_cuenta m
            JOIN clientes c ON m.cliente_id = c.id
            WHERE m.tipo='PAGO' 
            ORDER BY m.fecha DESC
        ''')
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

    def update_client(self, client_id, nombre, telefono, alias, limite_credito):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE clientes 
                SET nombre = ?, telefono = ?, alias = ?, limite_credito = ?
                WHERE id = ?
            ''', (nombre, telefono, alias, limite_credito, client_id))
            conn.commit()
        finally:
            conn.close()

    def delete_client(self, client_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            # Eliminar movimientos asociados primero (si no hay CASCADE)
            cursor.execute("DELETE FROM movimientos_cuenta WHERE cliente_id = ?", (client_id,))
            cursor.execute("DELETE FROM clientes WHERE id = ?", (client_id,))
            conn.commit()
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

    # ==========================================
    # METODOS CONTROL DE TURNOS
    # ==========================================
    
    def get_active_turno(self):
        """Devuelve el turno activo (fecha_fin IS NULL) o None"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM turnos WHERE fecha_fin IS NULL ORDER BY id DESC LIMIT 1")
        res = cursor.fetchone()
        conn.close()
        return res

    def iniciar_turno(self, monto_inicial, usuario="Admin"):
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            fecha_inicio = datetime.datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO turnos (fecha_inicio, monto_inicial, usuario)
                VALUES (?, ?, ?)
            ''', (fecha_inicio, monto_inicial, usuario))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def cerrar_turno(self, monto_final):
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            fecha_fin = datetime.datetime.now().isoformat()
            # Cerrar el último turno abierto
            cursor.execute('''
                UPDATE turnos 
                SET fecha_fin = ?, monto_final = ? 
                WHERE fecha_fin IS NULL
            ''', (fecha_fin, monto_final))
            conn.commit()
        finally:
            conn.close()

    def get_current_shift_stats(self):
        """Calcula el estado actual de la caja según el turno activo"""
        turno = self.get_active_turno()
        if not turno:
            return None
            
        # turno: (id, fecha_inicio, fecha_fin, monto_inicial, monto_final, usuario)
        t_id, t_inicio, _, t_inicial, _, t_usuario = turno
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # 1. Sumar ventas DESDE el inicio del turno
        cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha >= ?", (t_inicio,))
        res = cursor.fetchone()
        ventas_total = res[0] if res[0] else 0
        
        # 2. Sumar ABONOS (Pagos) DESDE el inicio del turno
        # Estos son dinero real que entra a la caja
        cursor.execute("SELECT SUM(monto) FROM movimientos_cuenta WHERE tipo='PAGO' AND fecha >= ?", (t_inicio,))
        res = cursor.fetchone()
        abonos_total = res[0] if res[0] else 0
        
        # 3. Sumar GASTOS (Salidas) DESDE el inicio del turno
        # Para que el teorico en caja sea REAL (Entradas - Salidas)
        cursor.execute("SELECT SUM(monto) FROM gastos WHERE fecha >= ?", (t_inicio,))
        res = cursor.fetchone()
        gastos_total = res[0] if res[0] else 0
        
        conn.close()
        
        # Teorico = Inicial + Ventas + Abonos - Gastos
        teorico = t_inicial + ventas_total + abonos_total - gastos_total
        
        return {
            "turno_id": t_id,
            "usuario": t_usuario,
            "inicio": t_inicio,
            "monto_inicial": t_inicial,
            "ventas_turno": ventas_total,
            "abonos_turno": abonos_total,
            "gastos_turno": gastos_total,
            "teorico_en_caja": teorico
        }

    def get_financial_report(self, start_date=None, end_date=None):
        """
        Genera un reporte financiero detallado entre fechas.
        Retorna diccionario con métricas clave.
        """
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Filtros de fecha (ISO strings YYYY-MM-DD...)
        if not start_date:
            start_date = "1900-01-01"
        if not end_date:
            # Fin del día de hoy
            end_date = datetime.datetime.now().isoformat()
            
        # Asegurar que cubra todo el día final si solo se pasa fecha
        if len(end_date) == 10: 
            end_date += "T23:59:59"
            
        try:
            # 1. Ventas Totales (Bruto)
            cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha BETWEEN ? AND ?", (start_date, end_date))
            res = cursor.fetchone()
            total_ventas = res[0] or 0
            
            # 2. Gastos Totales
            cursor.execute("SELECT SUM(monto) FROM gastos WHERE fecha BETWEEN ? AND ?", (start_date, end_date))
            res = cursor.fetchone()
            total_gastos = res[0] or 0
            
            # 3. Fiados Generados (Movimientos tipo DEUDA en el rango)
            # Nota: Esto nos dice cuánto de la venta NO entró en caja.
            cursor.execute("SELECT SUM(monto) FROM movimientos_cuenta WHERE tipo='DEUDA' AND fecha BETWEEN ? AND ?", (start_date, end_date))
            res = cursor.fetchone()
            total_fiado_generado = res[0] or 0
            
            # 4. Pagos Recibidos (Movimientos tipo PAGO en el rango)
            # Dinero que entró por deudas pasadas o abonos
            cursor.execute("SELECT SUM(monto) FROM movimientos_cuenta WHERE tipo='PAGO' AND fecha BETWEEN ? AND ?", (start_date, end_date))
            res = cursor.fetchone()
            total_pagos_recibidos = res[0] or 0
            
            # --- CALCULOS ---
            
            # Dinero Real Entrado por Ventas = Ventas Totales - Fiado Generado
            efectivo_ventas = total_ventas - total_fiado_generado
            
            # Flujo de Caja TOTAL (Entradas Reales) = Efectivo Ventas + Pagos Recibidos
            flujo_caja_entradas = efectivo_ventas + total_pagos_recibidos
            
            # Flujo Neto (Caja Final Teorica generada en periodo) = Entradas - Gastos
            flujo_neto = flujo_caja_entradas - total_gastos
            
            # Utilidad Operativa (Estado de Resultados simplificado) = Ventas - Gastos
            # (Ignorando si cobramos o no, contabilidad de devengo simplificada)
            utilidad_operativa = total_ventas - total_gastos
            
            return {
                "total_ventas": total_ventas,
                "total_gastos": total_gastos,
                "total_fiado": total_fiado_generado,
                "total_abonos": total_pagos_recibidos,
                
                # Derivados
                "efectivo_ventas": efectivo_ventas,
                "flujo_entradas": flujo_caja_entradas,
                "flujo_neto": flujo_neto,
                "utilidad": utilidad_operativa
            }
            
        finally:
            conn.close()



    def get_top_selling_products(self, days=30, limit=5):
        """
        Obtiene los productos más vendidos en los últimos N días.
        Retorna lista de tuplas: (nombre_producto, cantidad_total_vendida)
        """
        import datetime
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # Calcular fecha de inicio (hace N días)
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            query = '''
                SELECT 
                    p.nombre,
                    SUM(d.cantidad) as total_vendido
                FROM detalle_ventas d
                JOIN ventas v ON d.venta_id = v.id
                JOIN productos p ON d.producto_id = p.id
                WHERE v.fecha >= ?
                GROUP BY p.id, p.nombre
                ORDER BY total_vendido DESC
                LIMIT ?
            '''
            
            cursor.execute(query, (start_date, limit))
            return cursor.fetchall()
            
        finally:
            conn.close()

    def get_sales_in_range(self, start_date, end_date):
        """
        Retorna lista de ventas en un rango de fechas.
        Retorna: [(id, fecha, total), ...] ordenado por fecha DESC
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Asegurar formato completo para end_date
        if len(end_date) == 10: 
            end_date += "T23:59:59"
            
        try:
            cursor.execute("SELECT id, fecha, total, medio_pago FROM ventas WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC", 
                           (start_date, end_date))
            return cursor.fetchall()
        finally:
            conn.close()

    # ==========================================
    # NUEVOS METODOS (HISTORIAL UNIFICADO)
    # ==========================================

    def get_sale_details(self, sale_id):
        """
        Retorna detalles de los productos vendidos en una venta especifica.
        Lista de tuplas: (nombre_producto, cantidad, precio_unit, subtotal)
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        query = '''
            SELECT p.nombre, d.cantidad, d.precio_unitario, d.subtotal
            FROM detalle_ventas d
            JOIN productos p ON d.producto_id = p.id
            WHERE d.venta_id = ?
            ORDER BY p.nombre ASC
        '''
        cursor.execute(query, (sale_id,))
        res = cursor.fetchall()
        conn.close()
        return res

    def get_all_income_events(self):
        """
        Retorna lista unificada de Ventas y Abonos (Pagos) ordenados por fecha DESC.
        Formato de items en la lista:
        {
            'type': 'VENTA' o 'PAGO',
            'id': int (id de la venta o movimiento),
            'date': str (ISO date),
            'amount': float,
            'description': str,
            'details_id': int (id para buscar detalle, venta_id o movimiento_id)
        }
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        events = []
        
        try:
            # 1. Obtener Ventas
            cursor.execute("SELECT id, fecha, total FROM ventas")
            sales = cursor.fetchall()
            for s in sales:
                events.append({
                    'type': 'VENTA',
                    'id': s[0],
                    'date': s[1],
                    'amount': s[2],
                    'description': f"Venta #{s[0]}",
                    'details_id': s[0]
                })
                
            # 2. Obtener Abonos (Pagos) con nombre de cliente
            query_pagos = '''
                SELECT m.id, m.fecha, m.monto, m.descripcion, c.nombre
                FROM movimientos_cuenta m
                JOIN clientes c ON m.cliente_id = c.id
                WHERE m.tipo = 'PAGO'
            '''
            cursor.execute(query_pagos)
            pagos = cursor.fetchall()
            for p in pagos:
                desc_extra = p[3] if p[3] else ""
                events.append({
                    'type': 'PAGO',
                    'id': p[0],
                    'date': p[1],
                    'amount': p[2],
                    'description': f"Abono - {p[4]} ({desc_extra})",
                    'details_id': p[0] # Para abonos, usaremos el mismo ID para mostrar info
                })
                
            # 3. Ordenar por fecha descendente (lo mas reciente primero)
            events.sort(key=lambda x: x['date'], reverse=True)
            
            return events
            
        finally:
            conn.close()

