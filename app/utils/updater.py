import urllib.request
import json
import ssl

# Configuración del Repositorio
GITHUB_REPO = "kaelhen/sosdigitalpyme"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def check_for_updates(current_version):
    """
    Consulta la API de GitHub para ver si hay una versión más nueva.
    Retorna: (has_update: bool, latest_version: str, download_url: str)
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
                
                # Limpieza simple de 'v'
                remote_ver = latest_tag.lstrip("v")
                local_ver = current_version.lstrip("v")
                
                # Comparación básica de strings (Ideal: usar packaging.version)
                # Si son distintos y el remoto no es vacío, asumimos update
                # (Para ser más robusto, comparamos tuplas de enteros)
                if remote_ver and remote_ver != local_ver:
                    # Intentar comparar numéricamente
                    try:
                        r_parts = [int(x) for x in remote_ver.split('.')]
                        l_parts = [int(x) for x in local_ver.split('.')]
                        
                        if r_parts > l_parts:
                            return True, latest_tag, html_url
                    except ValueError:
                        # Si falla el parseo, solo avisar si son distintos strings
                         if remote_ver != local_ver:
                             return True, latest_tag, html_url
                            
    except Exception as e:
        print(f"Update check failed: {e}")
        
    return False, None, None
