import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.utils.activation import get_hardware_id, get_request_code, verify_key_and_get_expiry, ACTIVATION_FILE

print(f"--- Activation Debug Info ---")
print(f"Activation File Path: {ACTIVATION_FILE}")

if os.path.exists(ACTIVATION_FILE):
    with open(ACTIVATION_FILE, 'r') as f:
        content = f.read().strip()
    print(f"File Content: {content}")
    
    is_valid, msg = verify_key_and_get_expiry(content)
    print(f"Validation Result: {is_valid}")
    print(f"Message: {msg}")
else:
    print("Activation file not found.")

print(f"Current Hardware ID: {get_hardware_id()}")
print(f"Current Request Code: {get_request_code()}")
