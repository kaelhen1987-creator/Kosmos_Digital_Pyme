import sys
sys.path.insert(0, '/Users/kaelhen/Desktop/SOSDIGITALPYME')

from app.utils.updater import check_for_updates

# Probar con versión anterior para forzar detección de actualización
print("Testing update check...")
print("Current version: 0.11.10")
print("Expected latest: 0.11.11")
print("-" * 50)

has_update, new_ver, update_url = check_for_updates("0.11.10", "android")

print("-" * 50)
print(f"Result:")
print(f"  Has Update: {has_update}")
print(f"  New Version: {new_ver}")
print(f"  Download URL: {update_url}")
