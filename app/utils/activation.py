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
    Obtiene el ID de hardware único y ESTABLE del dispositivo.
    Intenta usar comandos del sistema (macOS/Windows) para obtener el UUID de la placa/sistema.
    Si falla, hace fallback a uuid.getnode() (MAC Address).
    """
    import platform
    import subprocess
    
    system = platform.system()
    
    try:
        if system == 'Darwin': # macOS
            # Comando: ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID"
            output = subprocess.check_output(cmd, shell=True).decode()
            # Formato esperado: "  "IOPlatformUUID" = "00000000-0000-0000-0000-000000000000"\n"
            if "IOPlatformUUID" in output:
                return output.split('"')[-2]
                
        elif system == 'Windows': # Windows
            # Método 1: WMIC (BIOS UUID) - Preferido
            try:
                # flags=0x08000000 (CREATE_NO_WINDOW) para evitar parpadeo
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                cmd = "wmic csproduct get uuid"
                # Usamos startupinfo si estamos en python con permisos, si falla probamos normal
                try:
                    output = subprocess.check_output(cmd, startupinfo=startupinfo).decode()
                except:
                    output = subprocess.check_output(cmd, shell=True).decode()
                    
                lines = [line.strip() for line in output.split('\n') if line.strip()]
                if len(lines) > 1 and "UUID" not in lines[1]: # Validar que no sea header repetido
                    return lines[1]
            except Exception as e:
                print(f"Windows wmic failed: {e}")

            # Método 2: Registry (MachineGuid) - Muy estable
            try:
                cmd = "reg query HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography /v MachineGuid"
                output = subprocess.check_output(cmd, shell=True).decode()
                # Output: ... MachineGuid    REG_SZ    UUID ...
                if "MachineGuid" in output:
                    return output.strip().split()[-1]
            except Exception as e:
                print(f"Windows Registry failed: {e}")
                
            # Método 3: PowerShell (Fallback final antes de MAC)
            try:
                cmd = "powershell -Command \"Get-WmiObject Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID\""
                output = subprocess.check_output(cmd, shell=True).decode().strip()
                if len(output) > 10:
                    return output
            except Exception as e:
                print(f"Windows PowerShell failed: {e}")

    except Exception as e:
        print(f"Warning: Error obteniendo Stable ID ({e}), usando fallback.")
    
    # Fallback: uuid.getnode() (MAC Address, puede cambiar con red)
    # Solo llegamos aqui si fallaron TODOS los metodos de SO
    print("Warning: Usando MAC Address como fallback.")
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
    
    Retorna: XXXX-XXXX-XXXX-XXXX (16 chars, 4 grupos de 4)
    Contiene: YYYYMMDD (8 chars) + SIGNATURE (8 chars) intercalados o concatenados?
    Para simplificar: YYYYMMDD + SIGNATURE, luego agrupar.
    """
    # Payload incluye la fecha para que la firma sea única para ESE vencimiento
    payload = f"{request_code.upper()}{expiration_date_str}{SECRET_SALT}"
    hashed = hashlib.sha256(payload.encode()).hexdigest().upper()
    
    # Usamos los primeros 8 chars del hash como firma
    signature = hashed[:8]
    
    # Combinar fecha y firma: 20260217 + A1B2C3D4 = 20260217A1B2C3D4 (16 chars)
    raw_key = f"{expiration_date_str}{signature}"
    
    # Formatear en grupos de 4: 2026-0217-A1B2-C3D4
    groups = [raw_key[i:i+4] for i in range(0, len(raw_key), 4)]
    return "-".join(groups)

def verify_key_and_get_expiry(input_key, _current_date=None):
    """
    Verifica si la llave es válida Y si no ha expirado.
    Retorna: (is_valid, message_or_date)
    """
    # Limpieza básica: Quitamos guiones y espacios
    clean_key = input_key.strip().upper().replace("-", "")
    
    # Formato esperado: 16 caracteres (8 Fecha + 8 Firma)
    if len(clean_key) != 16:
        return False, "Longitud de clave inválida."
        
    date_part = clean_key[:8] # Primeros 8: Fecha YYYYMMDD
    signature_part = clean_key[8:] # Últimos 8: Firma
    
    # 1. Verificar Firma (Integridad y Hardware)
    req_code = get_request_code()
    
    # Regenerar firma esperada
    payload = f"{req_code.upper()}{date_part}{SECRET_SALT}"
    hashed = hashlib.sha256(payload.encode()).hexdigest().upper()
    expected_signature = hashed[:8]
    
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
