from app.data.database import InventarioModel

m = InventarioModel()
events = m.get_all_income_events()
print(f"Events found: {len(events)}")

if events:
    first_sale = next((e for e in events if e['type'] == 'VENTA'), None)
    if first_sale:
        print(f"Testing details for sale {first_sale['id']}")
        details = m.get_sale_details(first_sale['id'])
        print(f"Details: {details}")
    else:
        print("No sales found to test details")
else:
    print("No events found")
