import tkinter as tk
from tkinter import ttk, messagebox
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
        """Agrega un nuevo producto."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO productos (nombre, precio, stock, stock_critico) VALUES (?, ?, ?, ?)",
                       (nombre, precio, stock, stock_critico))
        conn.commit()
        conn.close()

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
        self.on_sell_product = None

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
        # Frame Principal POS
        main_frame = ttk.Frame(self.tab_pos, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Seleccione Producto a Vender:", font=("Arial", 14)).pack(pady=10)

        # Lista de productos para venta rápida (Treeview simplificado)
        columns_pos = ("ID", "Nombre", "Precio", "Stock")
        self.tree_pos = ttk.Treeview(main_frame, columns=columns_pos, show="headings", height=15)
        
        for col in columns_pos:
            self.tree_pos.heading(col, text=col)
            self.tree_pos.column(col, width=100 if col != "Nombre" else 400)
        
        self.tree_pos.pack(fill="both", expand=True, pady=10)

        # Botón VENDER GIGANTE
        self.btn_vender = tk.Button(main_frame, text="VENDER ( -1 UNIDAD )", bg="#4CAF50", fg="white", 
                                    font=("Arial", 16, "bold"), height=3, command=self._handle_sell)
        self.btn_vender.pack(fill="x", pady=20)

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

    def _handle_sell(self):
        selected = self.tree_pos.selection()
        if not selected:
            messagebox.showwarning("Selección", "Seleccione un producto de la lista para vender")
            return

        item = self.tree_pos.item(selected[0])
        product_id = item['values'][0]
        stock_actual = item['values'][3]

        if stock_actual <= 0:
            messagebox.showerror("Error", "No hay stock suficiente para realizar la venta")
            return

        if self.on_sell_product:
            self.on_sell_product(product_id)
            messagebox.showinfo("Venta Exitosa", "Se descontó 1 unidad del inventario")

    def _clear_form(self):
        self.entry_nombre.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.entry_stock.delete(0, tk.END)
        self.entry_stock_critico.delete(0, tk.END)

    def _on_tree_select(self, event):
        # Opcional: Cargar datos en el formulario al seleccionar para editar (no requerido estrictamente en MVP)
        pass

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

        # Asignar callbacks de la vista a métodos del controlador
        self.view.on_add_product = self.add_product
        self.view.on_delete_product = self.delete_product
        self.view.on_sell_product = self.sell_product

        # Cargar datos iniciales
        self.refresh_list()

    def add_product(self, nombre, precio, stock, stock_critico):
        self.model.add_product(nombre, precio, stock, stock_critico)
        self.refresh_list()

    def delete_product(self, product_id):
        self.model.delete_product(product_id)
        self.refresh_list()

    def sell_product(self, product_id):
        self.model.decrease_stock(product_id)
        self.refresh_list()

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
