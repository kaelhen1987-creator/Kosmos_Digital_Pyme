import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3

# =============================================================================
# MODELO (MODEL)
# Maneja la lógica de datos y la interacción con la base de datos SQLite.
# =============================================================================
class InventarioModel:
    def __init__(self, db_name='inventario.db'):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        """Inicializa la base de datos y crea la tabla si no existe."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL,
                stock_critico INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def get_all_products(self):
        """Obtiene todos los productos de la base de datos."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos")
        resultados = cursor.fetchall()
        conn.close()
        return resultados

    def add_product(self, nombre, precio, stock, stock_critico):
        """Agrega un producto o suma stock si ya existe (por nombre)."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Verificar si existe por nombre (case insensitive)
        cursor.execute("SELECT id, stock FROM productos WHERE lower(nombre) = ?", (nombre.lower(),))
        existing = cursor.fetchone()
        
        if existing:
            # Si existe, actualizamos stock y precio/critico (Upsert)
            product_id, current_stock = existing
            new_stock = current_stock + stock
            cursor.execute("""
                UPDATE productos 
                SET stock = ?, precio = ?, stock_critico = ? 
                WHERE id = ?
            """, (new_stock, precio, stock_critico, product_id))
        else:
            # Si no existe, insertamos
            cursor.execute("INSERT INTO productos (nombre, precio, stock, stock_critico) VALUES (?, ?, ?, ?)",
                           (nombre, precio, stock, stock_critico))
        
        conn.commit()
        conn.close()
        return existing is not None # Return True if updated, False if created

    def delete_product(self, product_id):
        """Elimina un producto por ID."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()

    def update_product(self, product_id, nombre, precio, stock, stock_critico):
        """Actualiza un producto existente."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET nombre = ?, precio = ?, stock = ?, stock_critico = ? WHERE id = ?",
                       (nombre, precio, stock, stock_critico, product_id))
        conn.commit()
        conn.close()

    def decrease_stock(self, product_id, quantity=1):
        """Disminuye el stock de un producto (Venta)."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (quantity, product_id))
        conn.commit()
        conn.close()


# =============================================================================
# VISTA (VIEW)
# Maneja la Interfaz Gráfica de Usuario (GUI) con Tkinter.
# No contiene lógica de negocio, solo muestra datos y captura eventos.
# =============================================================================
class POSView:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema POS y Gestión de Inventario MVP")
        self.root.geometry("800x600")

        # Configuración de estilos para el Treeview (Semáforo)
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)
        self.root.option_add('*TCombobox*Listbox.font', ("Arial", 12))

        # Crear Tabs (Pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Pestaña 1: Inventario
        self.tab_inventario = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_inventario, text='  Gestión de Inventario  ')
        self._setup_inventario_tab()

        # Pestaña 2: Venta Rápida (POS)
        self.tab_pos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_pos, text='  Venta Rápida (POS)  ')
        self._setup_pos_tab()

        # Callbacks (Serán asignados por el Controlador)
        self.on_add_product = None
        self.on_delete_product = None
        self.on_update_product = None
        # Callbacks Carrito
        self.on_add_to_cart = None
        self.on_remove_from_cart = None
        self.on_checkout = None
        self.on_clear_cart = None

    def _setup_inventario_tab(self):
        # Frame Formulario
        form_frame = ttk.LabelFrame(self.tab_inventario, text="Datos del Producto", padding=10)
        form_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_nombre = ttk.Entry(form_frame)
        self.entry_nombre.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Precio:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_precio = ttk.Entry(form_frame)
        self.entry_precio.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form_frame, text="Stock Inicial:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_stock = ttk.Entry(form_frame)
        self.entry_stock.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Stock Crítico:").grid(row=1, column=2, padx=5, pady=5)
        self.entry_stock_critico = ttk.Entry(form_frame)
        self.entry_stock_critico.grid(row=1, column=3, padx=5, pady=5)

        # Botones Acción
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        self.btn_agregar = ttk.Button(btn_frame, text="Agregar Producto", command=self._handle_add)
        self.btn_agregar.pack(side="left", padx=5)
        
        self.btn_editar = ttk.Button(btn_frame, text="Guardar Cambios", command=self._handle_update)
        self.btn_editar.pack(side="left", padx=5)

        self.btn_eliminar = ttk.Button(btn_frame, text="Eliminar Seleccionado", command=self._handle_delete)
        self.btn_eliminar.pack(side="left", padx=5)

        self.btn_limpiar = ttk.Button(btn_frame, text="Limpiar Formulario", command=self._clear_form)
        self.btn_limpiar.pack(side="left", padx=5)

        # Tabla de Inventario (Treeview)
        tree_frame = ttk.Frame(self.tab_inventario)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("ID", "Nombre", "Precio", "Stock", "Crítico")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col != "Nombre" else 300)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configurar tags para el Semáforo de Stock
        self.tree.tag_configure("critical", background="#ffcccc") # Rojo
        self.tree.tag_configure("warning", background="#ffffe0")  # Amarillo
        self.tree.tag_configure("normal", background="white")     # Blanco

        # Evento de selección
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _setup_pos_tab(self):
        # Frame Principal POS (Contenedor Horizontal)
        main_frame = ttk.Frame(self.tab_pos, padding=10)
        main_frame.pack(fill="both", expand=True)

        # === SECCIÓN IZQUIERDA: LISTA DE PRODUCTOS ===
        left_frame = ttk.LabelFrame(main_frame, text="1. Seleccionar Productos", padding=5)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Buscador (Opcional TODO) - Por ahora solo la lista
        columns_pos = ("ID", "Nombre", "Precio", "Stock")
        self.tree_pos = ttk.Treeview(left_frame, columns=columns_pos, show="headings")
        self.tree_pos.heading("ID", text="ID")
        self.tree_pos.heading("Nombre", text="Nombre")
        self.tree_pos.heading("Precio", text="Precio")
        self.tree_pos.heading("Stock", text="Stock")
        
        self.tree_pos.column("ID", width=40)
        self.tree_pos.column("Nombre", width=150)
        self.tree_pos.column("Precio", width=80)
        self.tree_pos.column("Stock", width=60)
        
        # Scrollbar Izquierda
        scroll_pos = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree_pos.yview)
        self.tree_pos.configure(yscroll=scroll_pos.set)
        
        self.tree_pos.pack(side="left", fill="both", expand=True)
        scroll_pos.pack(side="right", fill="y")
        
        # Botón Agregar al Carrito (Debajo de la lista izquierda)
        btn_add = ttk.Button(left_frame, text="Agregar al Carrito >>", command=self._handle_add_to_cart)
        btn_add.pack(side="bottom", fill="x", pady=5)
        self.tree_pos.bind("<Double-1>", lambda e: self._handle_add_to_cart()) # Doble click para agregar

        # === SECCIÓN DERECHA: CARRITO DE COMPRAS ===
        right_frame = ttk.LabelFrame(main_frame, text="2. Carrito de Compras", padding=5)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Lista del Carrito
        columns_cart = ("ID", "Producto", "Cant", "Total")
        self.tree_cart = ttk.Treeview(right_frame, columns=columns_cart, show="headings")
        self.tree_cart.heading("ID", text="ID")
        self.tree_cart.heading("Producto", text="Producto")
        self.tree_cart.heading("Cant", text="Cant")
        self.tree_cart.heading("Total", text="Total")
        
        self.tree_cart.column("ID", width=40)
        self.tree_cart.column("Producto", width=150)
        self.tree_cart.column("Cant", width=50)
        self.tree_cart.column("Total", width=80)

        # Scrollbar Derecha
        scroll_cart = ttk.Scrollbar(right_frame, orient="vertical", command=self.tree_cart.yview)
        self.tree_cart.configure(yscroll=scroll_cart.set)
        
        self.tree_cart.pack(side="top", fill="both", expand=True)
        scroll_cart.pack(side="right", fill="y")

        # Botón Quitar del Carrito
        btn_remove = ttk.Button(right_frame, text="Quitar Item Seleccionado", command=self._handle_remove_from_cart)
        btn_remove.pack(fill="x", pady=5)

        # TOTAL A PAGAR
        self.lbl_total = ttk.Label(right_frame, text="TOTAL: $0.0", font=("Arial", 20, "bold"), anchor="e")
        self.lbl_total.pack(fill="x", pady=10)

        # === BOTONES DE ACCIÓN (Confirmar / Cancelar) ===
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(side="bottom", fill="x", pady=10)

        self.btn_pagar = ttk.Button(action_frame, text="CONFIRMAR VENTA", command=self._handle_checkout)
        self.btn_pagar.pack(side="left", fill="x", expand=True, padx=2)
        
        self.btn_cancelar = ttk.Button(action_frame, text="CANCELAR", command=self._handle_clear_cart)
        self.btn_cancelar.pack(side="left", fill="x", expand=True, padx=2)


    # --- Métodos de Interfaz interna ---
    def _handle_add(self):
        try:
            nombre = self.entry_nombre.get()
            precio = float(self.entry_precio.get())
            stock = int(self.entry_stock.get())
            critico = int(self.entry_stock_critico.get())
            
            if not nombre:
                messagebox.showwarning("Faltan datos", "El nombre es obligatorio")
                return

            if self.on_add_product:
                self.on_add_product(nombre, precio, stock, critico)
            
            self._clear_form()
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos para Precio y Stock")

    def _handle_update(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un producto para editar")
            return
        
        item = self.tree.item(selected[0])
        product_id = item['values'][0]

        try:
            nombre = self.entry_nombre.get()
            precio = float(self.entry_precio.get())
            stock = int(self.entry_stock.get())
            critico = int(self.entry_stock_critico.get())
            
            if not nombre:
                messagebox.showwarning("Faltan datos", "El nombre es obligatorio")
                return

            if self.on_update_product:
                self.on_update_product(product_id, nombre, precio, stock, critico)
                messagebox.showinfo("Éxito", "Producto actualizado correctamente")
            
            self._clear_form()
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos")

    def _handle_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un producto para eliminar")
            return
        
        item = self.tree.item(selected[0])
        product_id = item['values'][0]
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este producto?"):
            if self.on_delete_product:
                self.on_delete_product(product_id)
            self._clear_form()

    # --- Métodos de Interfaz interna (POS Actualizado) ---
    def _handle_add_to_cart(self):
        selected = self.tree_pos.selection()
        if not selected:
            return # Nada seleccionado
        
        item = self.tree_pos.item(selected[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        
        # Pedir cantidad al usuario
        cantidad = simpledialog.askinteger("Cantidad", f"Ingrese cantidad para '{product_name}':", 
                                         parent=self.root, minvalue=1, initialvalue=1)
        
        if cantidad is not None and self.on_add_to_cart:
            self.on_add_to_cart(product_id, cantidad)

    def _handle_remove_from_cart(self):
        selected = self.tree_cart.selection()
        if not selected:
             messagebox.showwarning("Selección", "Seleccione un producto del carrito para quitar")
             return

        item = self.tree_cart.item(selected[0])
        product_id = item['values'][0]
        
        if self.on_remove_from_cart:
            self.on_remove_from_cart(product_id)

    def _handle_checkout(self):
        if self.on_checkout:
            self.on_checkout()

    def _handle_clear_cart(self):
        if self.on_clear_cart:
            self.on_clear_cart()

    def update_cart_view(self, cart_items, total):
        """Actualiza la tabla del carrito."""
        # Limpiar
        for i in self.tree_cart.get_children():
            self.tree_cart.delete(i)
        
        # Llenar
        for item in cart_items:
            # item = {id, nombre, precio, cantidad, subtotal}
            self.tree_cart.insert("", "end", values=(
                item['id'],
                item['nombre'],
                item['cantidad'],
                f"${item['subtotal']:.0f}"
            ))
        
        self.lbl_total.config(text=f"TOTAL: ${total:,.0f}")

    def _clear_form(self):
        self.entry_nombre.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.entry_stock.delete(0, tk.END)
        self.entry_stock_critico.delete(0, tk.END)
        # Deseleccionar árbol para evitar confusiones
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection()[0])

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        values = item['values']
        
        # values = [id, nombre, precio, stock, critico]
        # Llenar formulario
        self.entry_nombre.delete(0, tk.END)
        self.entry_nombre.insert(0, values[1])
        
        self.entry_precio.delete(0, tk.END)
        self.entry_precio.insert(0, values[2])
        
        self.entry_stock.delete(0, tk.END)
        self.entry_stock.insert(0, values[3])
        
        self.entry_stock_critico.delete(0, tk.END)
        self.entry_stock_critico.insert(0, values[4])

    def update_product_list(self, products):
        """Actualiza ambas tablas (Inventario y POS) con los datos y aplica colores."""
        # Limpiar tablas
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i in self.tree_pos.get_children():
            self.tree_pos.delete(i)

        for p in products:
            # p = (id, nombre, precio, stock, stock_critico)
            p_id, nombre, precio, stock, critico = p
            
            # Lógica del Semáforo
            tag = "normal"
            if stock <= critico:
                tag = "critical"
            elif stock <= (critico + 5):
                tag = "warning"

            # Insertar en Inventario con color
            self.tree.insert("", "end", values=p, tags=(tag,))
            
            # Insertar en POS (sin colores o con colores si se prefiere, aquí simple)
            self.tree_pos.insert("", "end", values=(p_id, nombre, precio, stock))


# =============================================================================
# CONTROLADOR (CONTROLLER)
# Une el Modelo y la Vista. Escucha eventos de la Vista y actualiza el Modelo.
# =============================================================================
class POSController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.cart = {} # {product_id: {'info': tuple_prod, 'qty': int}}

        # Asignar callbacks de la vista
        self.view.on_add_product = self.add_product
        self.view.on_delete_product = self.delete_product
        self.view.on_update_product = self.update_product
        
        # Callbacks del Carrito
        self.view.on_add_to_cart = self.add_to_cart
        self.view.on_remove_from_cart = self.remove_from_cart
        self.view.on_checkout = self.checkout
        self.view.on_clear_cart = self.clear_cart

        # Cargar datos iniciales
        self.refresh_list()

    def add_product(self, nombre, precio, stock, stock_critico):
        updated = self.model.add_product(nombre, precio, stock, stock_critico)
        if updated:
            messagebox.showinfo("Stock Actualizado", f"El producto '{nombre}' ya existía. Se sumó el stock.")
        else:
            # messagebox.showinfo("Agregado", "Producto nuevo agregado.") # Opcional, para no ser invasivo
            pass
        self.refresh_list()

    def update_product(self, product_id, nombre, precio, stock, stock_critico):
        self.model.update_product(product_id, nombre, precio, stock, stock_critico)
        self.refresh_list()

    def delete_product(self, product_id):
        self.model.delete_product(product_id)
        self.refresh_list()

    # --- Lógica del Carrito ---
    
    def add_to_cart(self, product_id, quantity=1):
        # Obtener info actual del producto de la BD (para chequear stock real)
        products = self.model.get_all_products()
        product = next((p for p in products if p[0] == product_id), None)
        
        if not product:
            return

        # product = (id, nombre, precio, stock, critico)
        stock_real = product[3]
        
        # Calcular stock disponible considerando lo que ya está en el carrito
        qty_in_cart = 0
        if product_id in self.cart:
            qty_in_cart = self.cart[product_id]['qty']
        
        if qty_in_cart + quantity > stock_real:
            messagebox.showwarning("Stock Insuficiente", f"No hay suficiente stock de '{product[1]}'.\nStock Real: {stock_real}\nEn canasta: {qty_in_cart}\nSolicitado: {quantity}")
            return

        # Agregar al carrito
        if product_id not in self.cart:
            self.cart[product_id] = {'info': product, 'qty': 0}
        
        self.cart[product_id]['qty'] += quantity
        self._refresh_cart_view()

    def remove_from_cart(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]
            self._refresh_cart_view()

    def clear_cart(self):
        self.cart = {}
        self._refresh_cart_view()

    def checkout(self):
        if not self.cart:
            return

        if not messagebox.askyesno("Confirmar Venta", "¿Procesar la venta actual?"):
            return

        # Procesar venta
        try:
            for pid, data in self.cart.items():
                qty = data['qty']
                self.model.decrease_stock(pid, qty)
            
            self.cart = {} # Limpiar carrito
            self.refresh_list() # Actualizar inventario
            self._refresh_cart_view() # Limpiar vista carrito
            messagebox.showinfo("Venta Exitosa", "Venta registrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al procesar la venta: {e}")

    def _refresh_cart_view(self):
        cart_items_display = []
        total = 0.0
        
        for pid, data in self.cart.items():
            prod = data['info']
            qty = data['qty']
            price = prod[2]
            subtotal = price * qty
            total += subtotal
            
            cart_items_display.append({
                'id': pid,
                'nombre': prod[1],
                'cantidad': qty,
                'subtotal': subtotal
            })
            
        self.view.update_cart_view(cart_items_display, total)

    def refresh_list(self):
        products = self.model.get_all_products()
        self.view.update_product_list(products)


# =============================================================================
# MAIN (PUNTO DE ENTRADA)
# =============================================================================
if __name__ == "__main__":
    # Inicializar Base de Datos (Modelo)
    model = InventarioModel()

    # Inicializar GUI (Vista)
    root = tk.Tk()
    view = POSView(root)

    # Inicializar Lógica (Controlador)
    controller = POSController(model, view)

    # Iniciar Loop de la Aplicación
    root.mainloop()
