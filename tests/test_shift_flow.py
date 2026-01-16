
import os
import sqlite3
import unittest
from app.data.database import InventarioModel

class TestShiftControl(unittest.TestCase):
    def setUp(self):
        # Usar una DB de prueba
        self.db_name = "test_sos_pyme.db"
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
        self.model = InventarioModel(self.db_name)

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_database_creation(self):
        """Verifica que la DB y las tablas se creen correctamente."""
        self.assertTrue(os.path.exists(self.db_name))
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Verificar tabla turnos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='turnos'")
        self.assertIsNotNone(cursor.fetchone(), "La tabla 'turnos' no existe")
        
        conn.close()

    def test_shift_flow(self):
        """Verifica el flujo de inicio y cierre de turnos."""
        
        # 1. Al principio no debe haber turno activo
        self.assertIsNone(self.model.get_active_turno(), "No debería haber turno activo al inicio")
        
        # 2. Iniciar turno
        monto_inicial = 5000
        self.model.iniciar_turno(monto_inicial)
        
        # 3. Verificar turno activo
        active = self.model.get_active_turno()
        self.assertIsNotNone(active, "Debería haber un turno activo")
        self.assertEqual(active[3], monto_inicial, "El monto inicial no coincide")
        self.assertIsNone(active[2], "La fecha fin debería ser NULL")
        
        # 4. Cerrar turno (simulado)
        self.model.cerrar_turno(monto_final=10000)
        
        # 5. Verificar que ya no hay turno activo
        self.assertIsNone(self.model.get_active_turno(), "El turno debería estar cerrado")

if __name__ == '__main__':
    unittest.main()
