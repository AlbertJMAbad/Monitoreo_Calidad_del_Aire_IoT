import sqlite3

NOMBRE_BD = "calidad_aire.db"

def obtener_conexion():
    conexion = sqlite3.connect(NOMBRE_BD)
    conexion.execute("PRAGMA foreign_keys = ON;")
    conexion.row_factory = sqlite3.Row
    return conexion

def inicializar_bd():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dispositivos (
        id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        ubicacion TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mediciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dispositivo_id TEXT NOT NULL,
        fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        temperatura REAL,
        humedad REAL,
        presion REAL,
        pm25 REAL,
        pm10 REAL,
        FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id) ON DELETE CASCADE
    );
    """)

    # Migración automática si la tabla existía sin la columna presion
    cursor.execute("PRAGMA table_info(mediciones);")
    columnas = [col[1] for col in cursor.fetchall()]
    if "presion" not in columnas:
        cursor.execute("ALTER TABLE mediciones ADD COLUMN presion REAL;")
        print("Columna 'presion' agregada exitosamente a la base de datos.")

    cursor.execute("""
    INSERT OR IGNORE INTO dispositivos (id, nombre, ubicacion)
    VALUES ('esp32_01', 'ESP32 Prototipo', 'Laboratorio Interior');
    """)

    conexion.commit()
    conexion.close()
    print("Base de datos y tablas inicializadas correctamente.")

if __name__ == "__main__":
    inicializar_bd()
