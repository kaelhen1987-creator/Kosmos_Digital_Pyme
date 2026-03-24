import os
import platform
from datetime import datetime


def generar_ticket_texto(venta_id, carrito, total, medio_pago, descuento=0, 
                         nombre_local="S.O.S DIGITAL PYME", 
                         rut_local="", 
                         direccion_local="",
                         telefono_local="",
                         tipo_impresora="58mm",
                         mensaje_pie="¡Gracias por su preferencia!"):

    """
    Genera el texto formateado adaptándose a ticketeras de 58mm o 80mm.
    """
    # Configuramos el ancho y los espacios según la impresora
    if tipo_impresora == "80mm":
        ancho = 48
        largo_nombre = 26
        formato_encabezado = "CANT   DESCRIPCION                      TOTAL"
    else: # Por defecto 58mm
        ancho = 32
        largo_nombre = 14
        formato_encabezado = "CANT  DESCRIPCION       TOTAL"

    ticket = []
    
    # --- 1. ENCABEZADO ---
    ticket.append("=" * ancho)
    ticket.append(nombre_local.upper().center(ancho))
    
    if rut_local: ticket.append(rut_local.center(ancho))
    if direccion_local: ticket.append(direccion_local.center(ancho))
    if telefono_local: ticket.append(f"Tel: {telefono_local}".center(ancho))
        
    ticket.append("=" * ancho)
    ticket.append("Comprobante Interno de Venta".center(ancho))
    ticket.append(f"Ticket Nro: {venta_id}")
    ticket.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    ticket.append("-" * ancho)
    
    # --- 2. DETALLE DE PRODUCTOS ---
    ticket.append(formato_encabezado)
    for pid, item in carrito.items():
        nombre = item['info'][1][:largo_nombre] # Cortamos el nombre según el ancho disponible
        qty = item['qty']
        precio = item['info'][2]
        subtotal = qty * precio
        
        # Ajustamos los espacios dinámicamente
        if tipo_impresora == "80mm":
            linea = f"{qty:<5g} {nombre:<27} ${subtotal:>10,.0f}"
        else:
            linea = f"{qty:<3g} {nombre:<15} ${subtotal:>8,.0f}"
            
        ticket.append(linea)
        
    ticket.append("-" * ancho)
    
    # --- 3. TOTALES ---
    if descuento > 0:
        ticket.append(f"Descuento:".ljust(ancho - 10) + f"{descuento:>8}%")
        
    ticket.append(f"TOTAL A PAGAR:".ljust(ancho - 12) + f"${total:>10,.0f}")
    ticket.append(f"Medio de Pago:".ljust(ancho - 12) + f"{medio_pago:>12}")
    ticket.append("=" * ancho)
    
    # --- 4. PIE DE PÁGINA ---
    ticket.append(mensaje_pie.center(ancho))
    ticket.append("Vuelva pronto".center(ancho))
    ticket.append("\n\n\n\n\n") # Saltos de línea para la guillotina
    
    return "\n".join(ticket)


def imprimir_ticket(texto_ticket):
    """
    Envía el texto del ticket a la impresora predeterminada del sistema.
    Funciona en Windows, macOS y Linux sin librerías adicionales.

    Returns:
        True si el envío fue exitoso, False en caso de error.
    """
    ruta_archivo = "ticket_temporal.txt"
    try:
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            f.write(texto_ticket)

        sistema = platform.system()
        if sistema == "Windows":
            # Usa la impresora predeterminada de Windows directamente
            os.startfile(ruta_archivo, "print")
        elif sistema == "Darwin":   # macOS
            # En desarrollo: abre el ticket en TextEdit para verificar el formato.
            # Cuando tengas una impresora real configurada como predeterminada,
            # reemplazá esta línea por:  os.system(f'lpr "{ruta_archivo}"')
            os.system(f'open -a TextEdit "{ruta_archivo}"')
        else:                       # Linux
            os.system(f'lp "{ruta_archivo}"')

        return True

    except Exception as e:
        print(f"[PrinterHelper] Error al imprimir: {e}")
        return False
