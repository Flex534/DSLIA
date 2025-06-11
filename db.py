import sqlite3
import os

DB_PATH = "archivos.db"
BASE_PATH = "archivos"

def inicializar_db():
    # Solo crear si no existe
    if not os.path.exists(DB_PATH):
        # Crear carpetas base si no existen
        for carpeta in ["teoria", "tps", "bibliografia"]:
            os.makedirs(os.path.join(BASE_PATH, carpeta), exist_ok=True)

        # Crear base de datos y tabla limpia
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE archivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_archivo TEXT NOT NULL,
                ruta_archivo TEXT NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('Teo', 'TP', 'BIB')),
                fecha_subida TEXT NOT NULL,
                autor_id INTEGER NOT NULL,
                autor_nombre TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()