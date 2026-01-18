#!/usr/bin/env python3
import sys
import os
import calendar
from datetime import datetime, timedelta

# Agregamos el directorio actual al path
sys.path.append(os.getcwd())

try:
    from app.utils.activation import generate_subscription_key
except ImportError:
    print("Error: No se pudo importar app.utils.activation")
    sys.exit(1)

def add_months(source_date, months):
    """
    Función auxiliar para sumar meses sin usar librerías externas.
    Maneja el desbordamiento de años y días (ej: 31 Ene + 1 mes -> 28/29 Feb).
    """
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return source_date.replace(year=year, month=month, day=day)

def main():
    print("=========================================")
    print("   GENERADOR DE LICENCIAS - SOS DIGITAL")
    print("=========================================")
    
    # 1. Obtener Código de Solicitud
    if len(sys.argv) > 1:
        req_code = sys.argv[1]
    else:
        req_code = input("\nIngrese el Código de Solicitud (XXXX-XXXX): ").strip()
    
    if not req_code:
        print("Error: Código vacío.")
        return

    # 2. Seleccionar Duración
    print("\nSeleccione la duración de la suscripción:")
    print("1. 1 Mes")
    print("2. 3 Meses")
    print("3. 6 Meses")
    print("4. 1 Año")
    print("5. Personalizado (Días)")
    
    option = input("\nOpción (1-5): ").strip()
    
    today = datetime.now()
    expiry_date = today
    
    if option == "1":
        expiry_date = add_months(today, 1)
    elif option == "2":
        expiry_date = add_months(today, 3)
    elif option == "3":
        expiry_date = add_months(today, 6)
    elif option == "4":
        expiry_date = add_months(today, 12)
    elif option == "5":
        days = input("Ingrese número de días: ")
        try:
            expiry_date = today + timedelta(days=int(days))
        except ValueError:
            print("Número de días inválido.")
            return
    else:
        print("Opción inválida.")
        return
        
    # Formatear fecha para la llave (YYYYMMDD)
    date_str = expiry_date.strftime("%Y%m%d")
    
    # 3. Generar Llave
    key = generate_subscription_key(req_code, date_str)
    
    print("\n-----------------------------------------")
    print(f" LLAVE GENERADA: {key}")
    print(f" VENCE EL:       {expiry_date.strftime('%d/%m/%Y')}")
    print("-----------------------------------------")
    print("\nCopie y entregue esta llave al cliente.\n")

if __name__ == "__main__":
    main()
