# app/data/ventas_repository.py
import sqlite3
import json
import requests
from datetime import datetime

class VentasRepository:
    def __init__(self, db_name="sos_pyme.db", api_url="http://localhost:8001/api/v1/pos/ventas"):
        self.db_name = db_name
        self.api_url = api_url

    def guardar_venta(self, venta_dict, token_jwt=None):
        """
        Intenta enviar la venta a la nube. Si falla, la guarda localmente.
        """
        headers = {}
        if token_jwt:
            headers["Authorization"] = f"Bearer {token_jwt}"
        
        try:
            # 1. Intentamos enviar a la nube con un timeout corto (3 segundos)
            # Nota: Ajusta la URL según tu entorno real
            print(f"📡 Intentando sincronizar venta con la nube... ({self.api_url})")
            respuesta = requests.post(self.api_url, json=venta_dict, headers=headers, timeout=3.0)
            respuesta.raise_for_status()
            return {"status": "online", "mensaje": "Venta guardada en la nube"}
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            # 2. 🚨 ¡FALLO DE RED O API! Activamos el escudo offline
            print(f"⚠️ Error de conexión ({type(e).__name__}): Guardando venta en bóveda local (SQLite3)...")
            self._guardar_venta_local(venta_dict)
            return {"status": "offline", "mensaje": "Venta guardada localmente. Se sincronizará luego."}

    def _guardar_venta_local(self, venta_dict):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ventas_offline (payload_json) VALUES (?)",
                (json.dumps(venta_dict),)
            )
            conn.commit()
            conn.close()
            print("✅ Venta asegurada en tabla ventas_offline.")
        except Exception as ex:
            print(f"❌ Error crítico guardando offline: {ex}")
