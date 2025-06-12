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
        # Crear tabla de entregas
        cursor.execute('''
            CREATE TABLE entregas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                canal_id INTEGER NOT NULL,
                recordado_24h INTEGER DEFAULT 0,
                recordado_1h INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()