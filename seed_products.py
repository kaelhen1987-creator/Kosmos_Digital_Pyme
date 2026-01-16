
from app.data.database import InventarioModel

def seed_products():
    print("🌱 Iniciando carga de productos de prueba...")
    model = InventarioModel("sos_pyme.db")
    
    products = [
        ("Bebida Cola 3L", 3500, 50, 10, "78010001"),
        ("Arroz Grado 1 1kg", 1200, 100, 20, "78010002"),
        ("Aceite Maravilla 1L", 2500, 60, 10, "78010003"),
        ("Fideos Espirales 400g", 800, 80, 15, "78010004"),
        ("Salsa de Tomate 200g", 600, 100, 20, "78010005"),
        ("Pan Molde Blanco", 2200, 30, 5, "78010006"),
        ("Leche Entera 1L", 1100, 70, 10, "78010007"),
        ("Yogurt Frutilla", 450, 100, 20, "78010008"),
        ("Mantequilla 250g", 1800, 40, 5, "78010009"),
        ("Queso Gouda 1/4", 2800, 30, 5, "78010010"),
        ("Jamon Pierna 1/4", 3000, 30, 5, "78010011"),
        ("Papas Fritas Lays", 1500, 50, 10, "78010012"),
        ("Galletas Mora", 900, 60, 10, "78010013"),
        ("Chocolate Barra", 1200, 80, 15, "78010014"),
        ("Jabon Liquido", 1800, 40, 5, "78010015"),
        ("Detergente 1kg", 2500, 30, 5, "78010016"),
        ("Papel Higienico 4u", 3000, 20, 5, "78010017"),
        ("Toalla Nova 2u", 2800, 20, 5, "78010018"),
        ("Cloro Gel 1L", 1000, 50, 10, "78010019"),
        ("Fosforos Caja", 200, 200, 50, "78010020")
    ]
    
    count = 0
    for prod in products:
        try:
            model.add_product(*prod)
            print(f"✅ Agregado: {prod[0]}")
            count += 1
        except Exception as e:
            print(f"⚠️ Error agregando {prod[0]}: {e}")
            
    print(f"\n✨ Proceso finalizado. {count} productos agregados.")

if __name__ == "__main__":
    seed_products()
