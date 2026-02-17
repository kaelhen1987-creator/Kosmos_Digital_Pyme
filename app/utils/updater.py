import urllib.request
import json
import ssl

# Configuración del Repositorio (Público de Descargas)
GITHUB_REPO = "kaelhen/SoS-Descargas"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def check_for_updates(current_version, platform=None):
    """
    Consulta la API de GitHub para ver si hay una versión más nueva.
    Retorna: (has_update: bool, latest_version: str, download_url: str)
    
    Args:
        current_version: Versión actual de la app (ej: "0.11.3")
        platform: Plataforma del sistema (ej: "android", "windows", "macos")
    """
    try:
        # Contexto SSL seguro (o no verificado si da problemas de certificados locales)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(API_URL)
        req.add_header('User-Agent', 'SOSDigitalPyME-App')
        
        with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read())
                
                # La API devuelve "tag_name", ej: "v1.0.1" o "1.0.1"
                latest_tag = data.get("tag_name", "").strip()
                html_url = data.get("html_url", "") # URL de la release en web
                assets = data.get("assets", []) # Lista de archivos adjuntos
                
                print(f"GitHub Latest Tag: {latest_tag}")
                print(f"Local Version: {current_version}")
                print(f"Platform: {platform}")

                # Limpieza simple de 'v'
                remote_ver = latest_tag.lstrip("v")
                local_ver = current_version.lstrip("v")
                
                # DEV MODE CHECK
                if "dev" in current_version.lower():
                    print("Dev version detected. Skipping update check.")
                    return False, None, None

                # Comparación básica de strings (Ideal: usar packaging.version)
                # Si son distintos y el remoto no es vacío, asumimos update
                # (Para ser más robusto, comparamos tuplas de enteros)
                if remote_ver and remote_ver != local_ver:
                    # Intentar comparar numéricamente
                    try:
                        # Limpiar sufijos (ej: 0.10.0-beta -> 0.10.0) para comparar numeros
                        r_clean = remote_ver.split('-')[0]
                        l_clean = local_ver.split('-')[0]
                        
                        r_parts = [int(x) for x in r_clean.split('.')]
                        l_parts = [int(x) for x in l_clean.split('.')]
                        
                        if r_parts > l_parts:
                            print("Update found (Numeric comparison)")
                            
                            # Buscar el asset correcto según la plataforma
                            download_url = html_url # Fallback a la página HTML
                            
                            # Fix: platform puede ser Enum (PagePlatform.MACOS),
                            # convertir a string lowercase para comparar
                            plat_str = str(platform).lower() if platform else ""
                            print(f"Platform string for matching: '{plat_str}'")
                            
                            if plat_str and assets:
                                # Buscar el archivo correcto según la plataforma
                                if "android" in plat_str:
                                    # Buscar .apk
                                    for asset in assets:
                                        if asset.get("name", "").lower().endswith(".apk"):
                                            download_url = asset.get("browser_download_url", html_url)
                                            print(f"Found Android APK: {download_url}")
                                            break
                                            
                                elif "windows" in plat_str:
                                    # Buscar .exe o Setup.exe
                                    for asset in assets:
                                        name = asset.get("name", "").lower()
                                        if name.endswith(".exe") or "setup" in name:
                                            download_url = asset.get("browser_download_url", html_url)
                                            print(f"Found Windows installer: {download_url}")
                                            break
                                            
                                elif "macos" in plat_str:
                                    # Buscar .dmg o .app.zip
                                    for asset in assets:
                                        name = asset.get("name", "").lower()
                                        if name.endswith(".dmg") or name.endswith(".app.zip"):
                                            download_url = asset.get("browser_download_url", html_url)
                                            print(f"Found macOS installer: {download_url}")
                                            break
                            
                            return True, latest_tag, download_url
                            
                    except ValueError:
                        # Si falla el parseo, solo avisar si son distintos strings
                        pass # No forzamos la actualización si no es numérica clara
                        
                    # Fallback String Comparison (Solo si queremos ser agresivos, pero mejor evitar falsos positivos)
                    # if remote_ver != local_ver:
                    #     print("Update found (String comparison)")
                    #     return True, latest_tag, html_url
                            
    except Exception as e:
        print(f"Update check failed: {e}")
        
    return False, None, None
