from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from database import obtener_conexion
from reportes import generar_excel_estilizado, generar_pdf_estilizado

app = FastAPI(title="Monitor de Calidad de Aire")

class MedicionEntrada(BaseModel):
    dispositivo_id: str
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    presion: Optional[float] = None
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    co2: Optional[float] = None

@app.get("/", response_class=HTMLResponse)
def dashboard():
    with open("index.html", "r", encoding="utf-8") as archivo:
        return archivo.read()

@app.post("/api/mediciones")
def guardar_medicion(datos: MedicionEntrada):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        consulta = """
        INSERT INTO mediciones (dispositivo_id, temperatura, humedad, presion, pm25, pm10)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        cursor.execute(consulta, (
            datos.dispositivo_id, datos.temperatura, datos.humedad,
            datos.presion, datos.pm25, datos.pm10
        ))
        conexion.commit()
        return {"estado": "exito", "id_medicion": cursor.lastrowid}
    except Exception as error:
        conexion.rollback()
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        conexion.close()

# Listado de dispositivos registrados
@app.get("/api/dispositivos")
def listar_dispositivos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, ubicacion FROM dispositivos ORDER BY id ASC;")
    filas = [dict(f) for f in cursor.fetchall()]
    conexion.close()
    return filas

# Consultar historial con filtro opcional por dispositivo
@app.get("/api/mediciones")
def obtener_mediciones(dispositivo_id: Optional[str] = None, limite: int = 50):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if dispositivo_id:
        cursor.execute("""
        SELECT id, dispositivo_id, datetime(fecha_hora, 'localtime') as fecha_hora, 
               temperatura, humedad, presion, pm25, pm10
        FROM mediciones 
        WHERE dispositivo_id = ?
        ORDER BY id DESC LIMIT ?;
        """, (dispositivo_id, limite))
    else:
        cursor.execute("""
        SELECT id, dispositivo_id, datetime(fecha_hora, 'localtime') as fecha_hora, 
               temperatura, humedad, presion, pm25, pm10
        FROM mediciones 
        ORDER BY id DESC LIMIT ?;
        """, (limite,))
    filas = [dict(f) for f in cursor.fetchall()]
    conexion.close()
    return filas

def agrupar_datos_ultimas_50():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT DISTINCT m.dispositivo_id, d.nombre, d.ubicacion 
    FROM mediciones m
    LEFT JOIN dispositivos d ON m.dispositivo_id = d.id;
    """)
    dispositivos = cursor.fetchall()

    datos_por_dev = {}
    for dev in dispositivos:
        dev_id = dev["dispositivo_id"]
        cursor.execute("""
        SELECT id, datetime(fecha_hora, 'localtime') as fecha_hora,
               temperatura, humedad, presion, pm25, pm10
        FROM mediciones
        WHERE dispositivo_id = ?
        ORDER BY id DESC LIMIT 50;
        """, (dev_id,))
        filas = [dict(f) for f in cursor.fetchall()]
        if filas:
            datos_por_dev[dev_id] = {
                "nombre": dev["nombre"] or "Prototipo",
                "ubicacion": dev["ubicacion"] or "General",
                "filas": list(reversed(filas)) # Orden cronológico para el reporte
            }
    conexion.close()
    return datos_por_dev

@app.get("/api/exportar-excel")
def exportar_excel():
    datos = agrupar_datos_ultimas_50()
    buffer = generar_excel_estilizado(datos)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reporte_ultimas_50_mediciones.xlsx"}
    )

@app.get("/api/exportar-pdf")
def exportar_pdf():
    datos = agrupar_datos_ultimas_50()
    buffer = generar_pdf_estilizado(datos)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_ultimas_50_mediciones.pdf"}
    )
