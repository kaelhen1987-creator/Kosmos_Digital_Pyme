import uuid
import hashlib
import os
from datetime import datetime

# --- CONFIGURATION (HARDCODED SECRET) ---
# En un sistema real, esto debería estar ofuscado o compilado.
SECRET_SALT = "SOS_DIGITAL_PYME_2026_SECURE_SALT_!@#"

import sys
if getattr(sys, 'frozen', False):
    # Si está empaquetado (.app/.exe), usar carpeta Documentos
    home_dir = os.path.expanduser("~")
    data_dir = os.path.join(home_dir, "Documents", "SOS_Digital_PyME")
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
        except OSError:
            pass
    ACTIVATION_FILE = os.path.join(data_dir, "activation.lic")
else:
    # Modo Dev
    ACTIVATION_FILE = "activation.lic"

def get_hardware_id():
    """
    Obtiene el ID de hardware único del dispositivo.
    Usa uuid.getnode() que devuelve la dirección MAC.
    """
    node = uuid.getnode()
    return f"{node:X}"

def get_request_code():
    """
    Genera el código de solicitud para que el usuario envíe.
    Formato: XXXX-XXXX
    """
    hw_id = get_hardware_id()
    raw_hash = hashlib.sha256(hw_id.encode()).hexdigest().upper()
    code_part = raw_hash[:8]
    return f"{code_part[:4]}-{code_part[4:]}"

def generate_subscription_key(request_code, expiration_date_str):
    """
    Genera una llave de suscripción válida hasta una fecha.
    request_code: XXXX-XXXX
    expiration_date_str: YYYYMMDD (Ej: 20260217)
    
    Retorna: YYYYMMDD-SIGNATURE (Ej: 20260217-A1B2C3D4)
    """
    # Payload incluye la fecha para que la firma sea única para ESE vencimiento
    payload = f"{request_code.upper()}{expiration_date_str}{SECRET_SALT}"
    hashed = hashlib.sha256(payload.encode()).hexdigest().upper()
    
    # Usamos los primeros 8 chars del hash como firma
    signature = hashed[:8]
    
    return f"{expiration_date_str}-{signature}"

def verify_key_and_get_expiry(input_key, _current_date=None):
    """
    Verifica si la llave es válida Y si no ha expirado.
    Retorna: (is_valid, message_or_date)
    """
    # Limpieza básica
    clean_key = input_key.strip().upper()
    
    # Formato esperado: YYYYMMDD-SIGNATURE (17 chars aprox)
    parts = clean_key.split('-')
    if len(parts) != 2:
        # Fallback para soporte legacy (llaves perpetuas antiguas) si quisieras mantenerlo,
        # pero por ahora asumiremos solo el nuevo formato para suscripciones.
        return False, "Formato de clave inválido."
        
    date_part = parts[0] # YYYYMMDD
    signature_part = parts[1]
    
    if len(date_part) != 8:
        return False, "Formato de fecha inválido."
        
    # 1. Verificar Firma (Integridad y Hardware)
    req_code = get_request_code()
    # Reconstruimos la llave esperada para esa fecha
    expected_key = generate_subscription_key(req_code, date_part)
    expected_signature = expected_key.split('-')[1]
    
    if signature_part != expected_signature:
        return False, "La clave no corresponde a este dispositivo."
        
    # 2. Verificar Fecha (Vencimiento)
    try:
        expiry_date = datetime.strptime(date_part, "%Y%m%d")
        today = _current_date if _current_date else datetime.now()
        
        # Comparamos solo partes de fecha (ignorando hora)
        if today.date() > expiry_date.date():
            return False, f"La suscripción venció el {expiry_date.strftime('%d/%m/%Y')}"
            
        return True, expiry_date
        
    except ValueError:
        return False, "Fecha interna corrupta."

def save_activation(key):
    """
    Guarda la llave de activación en disco si es válida.
    """
    is_valid, msg = verify_key_and_get_expiry(key)
    if is_valid:
        with open(ACTIVATION_FILE, "w") as f:
            f.write(key)
        return True, msg
    return False, msg

def get_activation_status():
    """
    Retorna el estado de la activación.
    Returns: (is_active, message)
    """
    if not os.path.exists(ACTIVATION_FILE):
        return False, "No activado"
        
    try:
        with open(ACTIVATION_FILE, "r") as f:
            stored_key = f.read().strip()
            
        return verify_key_and_get_expiry(stored_key)
    except Exception as e:
        return False, f"Error: {str(e)}"

def is_activated():
    """
    Helper simple para usar en condicionales booleanos.
    """
    active, _ = get_activation_status()
    return active
