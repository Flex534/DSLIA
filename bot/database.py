import sqlite3
import os
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'archivos.db')
BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'archivos')

def inicializar_db():
    if not os.path.exists(DB_PATH):
        for carpeta in ["teoria", "tps", "bibliografia"]:
            os.makedirs(os.path.join(BASE_PATH, carpeta), exist_ok=True)
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
