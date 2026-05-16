import os
import requests
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

load_dotenv()

# CONFIGURACIÓN DE SUPABASE
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

app = FastAPI(title="Gestión de Flotas API - Supabase Edition")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Helper para construir cabeceras de Supabase
def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

# ==========================================
# TRADUCTORES DE CAPA (Dataverse Mappings)
# ==========================================
def mapear_vehiculo(v):
    return {
        "cr596_flota_vehiculoid": str(v.get("id")),
        "cr596_nombre": v.get("nombre"),
        "cr596_placa": v.get("placa"),
        "cr596_modelo": v.get("modelo"),
        "cr596_ano": v.get("ano"),
        "cr596_tipo": v.get("tipo"),
        "cr596_tipopropiedad": v.get("tipo_propiedad"),
        "cr596_estadooperativo": v.get("estado_operativo"),
        "cr596_kilometrajeactual": v.get("kilometraje_actual"),
        "cr596_nivelcombustible": v.get("nivel_combustible"),
        "cr596_tipocombustible": v.get("tipo_combustible"),
        "cr596_ultimomantenimientokm": v.get("ultimo_mantenimiento_km"),
        "cr596_frecuenciamantenimiento": v.get("frecuencia_mantenimiento"),
        "cr596_proximomantenimientokm": v.get("proximo_mantenimiento_km"),
        "cr596_vencimientosoat": v.get("vencimiento_soat"),
        "cr596_vencimientorevisiontecnica": v.get("vencimiento_rt"),
        "cr596_vencimientoseguro": v.get("vencimiento_seguro"),
        "cr596_vencimientogps": v.get("vencimiento_gps"),
        "cr596_lunaspolarizadas": v.get("lunas_polarizadas")
    }

def mapear_viaje(v):
    return {
        "cr596_flota_movimientoid": str(v.get("id")),
        "cr596_nombre": v.get("nombre_viaje"),
        "cr596_kmsalida": v.get("km_salida"),
        "_cr596_vehiculo_value": str(v.get("vehiculo_id")),
        "cr596_observacionesretorno": v.get("observaciones_retorno"),
        "cr596_fechahoraretorno": v.get("fecha_retorno")
    }

def mapear_gasto(g):
    return {
        "cr596_flota_gastorutaid": str(g.get("id")),
        "cr596_tipogasto": g.get("tipo_gasto"),
        "cr596_monto": float(g.get("monto")) if g.get("monto") is not None else 0.0,
        "cr596_fecha": g.get("fecha_gasto"),
        "cr596_proveedor": g.get("proveedor"),
        "cr596_comprobante": g.get("comprobante"),
        "cr596_observacion": g.get("observacion")
    }

# ==========================================
# MODELOS DE RECEPCIÓN (Pydantic Validation)
# ==========================================
class RegistroSalida(BaseModel):
    vehiculo_id: str
    km_salida: int
    combustible_salida: int
    observaciones: str = ""
    chk_brisas: bool = False
    chk_parachoques: bool = False
    chk_llantas: bool = False
    chk_puertas: bool = False
    chk_luces: bool = False
    chk_bocina: bool = False
    chk_maletero: bool = False
    chk_lunas: bool = False
    chk_limpieza: bool = False
    chk_guardafangos: bool = False
    chk_capo: bool = False
    chk_cinturon: bool = False

class RegistroRetorno(BaseModel):
    movimiento_id: str
    vehiculo_id: str  
    km_retorno: int
    combustible_retorno: int
    reporta_gastos: bool
    observaciones_retorno: str = ""  
    estado_llegada: int = 144280000  
    detalle_taller: str = ""

class RegistroGasto(BaseModel):
    movimiento_id: Optional[str] = None
    vehiculo_id: str
    tipo_gasto: int
    fecha: str
    empresa: int
    proveedor: str
    comprobante: str
    monto: float
    metodo_pago: int
    observacion: str = ""

class RegistroContable(BaseModel):
    gasto_id: str
    estado_validacion: int
    numero_comprobante: str
    cantidad_galones: float = None

class ActualizarVehiculo(BaseModel):
    vehiculo_id: str
    estado_operativo: Optional[int] = None
    ultimo_mantenimiento_km: Optional[int] = None
    frecuencia_mantenimiento: Optional[int] = None
    vencimiento_soat: Optional[str] = None
    vencimiento_rt: Optional[str] = None
    vencimiento_gps: Optional[str] = None
    vencimiento_seguro: Optional[str] = None
    lunas_polarizadas: Optional[int] = None 
    modelo: Optional[str] = None
    ano: Optional[int] = None
    tipo: Optional[str] = None
    tipo_propiedad: Optional[int] = None

# ==========================================
# ENDPOINTS GESTIÓN DE CONTROL (GARITA)
# ==========================================

@app.get("/vehiculos-activos")
def listar_vehiculos_activos():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/vehiculos?select=*", headers=supabase_headers())
        if res.status_code == 200:
            return {"status": "success", "data": [mapear_vehiculo(v) for v in res.json()]}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/viajes-abiertos")
def listar_viajes_abiertos():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/viajes?km_retorno=is.null&select=*", headers=supabase_headers())
        if res.status_code == 200:
            return {"status": "success", "data": [mapear_viaje(v) for v in res.json()]}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/registrar-salida")
def registrar_salida(registro: RegistroSalida):
    try:
        hora_actual = datetime.now(timezone.utc).isoformat()
        checklist = {
            "chk_brisas": registro.chk_brisas, "chk_parachoques": registro.chk_parachoques,
            "chk_llantas": registro.chk_llantas, "chk_puertas": registro.chk_puertas,
            "chk_luces": registro.chk_luces, "chk_bocina": registro.chk_bocina,
            "chk_maletero": registro.chk_maletero, "chk_lunas": registro.chk_lunas,
            "chk_limpieza": registro.chk_limpieza, "chk_guardafangos": registro.chk_guardafangos,
            "chk_capo": registro.chk_capo, "chk_cinturon": registro.chk_cinturon
        }
        
        payload_viaje = {
            "vehiculo_id": registro.vehiculo_id,
            "nombre_viaje": f"Salida-{hora_actual[:10]}",
            "km_salida": registro.km_salida,
            "combustible_salida": registro.combustible_salida,
            "fecha_salida": hora_actual,
            "observaciones_salida": registro.observaciones,
            "checklist_salida": checklist
        }
        res_viaje = requests.post(f"{SUPABASE_URL}/rest/v1/viajes", headers=supabase_headers(), json=payload_viaje)
        if res_viaje.status_code not in [200, 201, 204]: raise HTTPException(status_code=res_viaje.status_code, detail=res_viaje.text)
            
        requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{registro.vehiculo_id}", headers=supabase_headers(), json={"estado_operativo": 144280001})
        return {"status": "success", "message": "¡Salida registrada exitosamente!"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.patch("/registrar-retorno")
def registrar_retorno(registro: RegistroRetorno):
    try:
        hora_actual = datetime.now(timezone.utc).isoformat()
        payload_viaje = {
            "km_retorno": registro.km_retorno, "combustible_retorno": registro.combustible_retorno,
            "fecha_retorno": hora_actual, "reporta_gastos": registro.reporta_gastos,
            "observaciones_retorno": registro.observaciones_retorno, "detalle_taller": registro.detalle_taller
        }
        res_viaje = requests.patch(f"{SUPABASE_URL}/rest/v1/viajes?id=eq.{registro.movimiento_id}", headers=supabase_headers(), json=payload_viaje)
        if res_viaje.status_code not in [200, 201, 204]: raise HTTPException(status_code=res_viaje.status_code, detail=res_viaje.text)
            
        payload_veh = {"estado_operativo": registro.estado_llegada, "kilometraje_actual": registro.km_retorno, "nivel_combustible": registro.combustible_retorno}
        requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{registro.vehiculo_id}", headers=supabase_headers(), json=payload_veh)
        return {"status": "success", "message": "Retorno registrado con éxito."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS DE CENTRO DE COSTOS (TESORERÍA)
# ==========================================

@app.get("/viajes-con-gastos")
def listar_viajes_con_gastos():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/viajes?reporta_gastos=eq.true&select=*", headers=supabase_headers())
        if res.status_code == 200:
            return {"status": "success", "data": [mapear_viaje(v) for v in res.json()]}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/registrar-gasto")
def registrar_gasto(registro: RegistroGasto):
    try:
        payload_gasto = {
            "vehiculo_id": registro.vehiculo_id, "tipo_gasto": registro.tipo_gasto,
            "fecha_gasto": registro.fecha, "empresa": registro.empresa, "proveedor": registro.proveedor,
            "comprobante": registro.comprobante, "monto": registro.monto, "metodo_pago": registro.metodo_pago, "observacion": registro.observacion
        }
        if registro.movimiento_id: payload_gasto["viaje_id"] = registro.movimiento_id
            
        res_gasto = requests.post(f"{SUPABASE_URL}/rest/v1/gastos", headers=supabase_headers(), json=payload_gasto)
        if res_gasto.status_code not in [200, 201, 204]: raise HTTPException(status_code=res_gasto.status_code, detail=res_gasto.text)
            
        if registro.movimiento_id:
            requests.patch(f"{SUPABASE_URL}/rest/v1/viajes?id=eq.{registro.movimiento_id}", headers=supabase_headers(), json={"reporta_gastos": False})
        return {"status": "success", "message": "Gasto registrado correctamente."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/reporte-gastos")
def reporte_gastos(inicio: str, fin: str):
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/gastos?fecha_gasto=gte.{inicio}&fecha_gasto=lte.{fin}&select=*,vehiculos(*)", headers=supabase_headers())
        if res.status_code == 200:
            lista = []
            for g in res.json():
                g_mapped = mapear_gasto(g)
                v_raw = g.get("vehiculos", {})
                g_mapped["cr596_Vehiculo"] = {"cr596_nombre": v_raw.get("nombre", "Desconocido"), "cr596_placa": v_raw.get("placa", "S/P")}
                lista.append(g_mapped)
            return {"status": "success", "data": lista}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS DE MANTENIMIENTO / FLOTA
# ==========================================

@app.get("/estado-flota")
def estado_flota():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/vehiculos?select=*", headers=supabase_headers())
        if res.status_code == 200:
            return {"status": "success", "data": [mapear_vehiculo(v) for v in res.json()]}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.patch("/actualizar-vehiculo")
def actualizar_vehiculo(datos: ActualizarVehiculo):
    try:
        payload = {}
        if datos.estado_operativo is not None: payload["estado_operativo"] = datos.estado_operativo
        if datos.vencimiento_soat: payload["vencimiento_soat"] = datos.vencimiento_soat
        if datos.vencimiento_rt: payload["vencimiento_rt"] = datos.vencimiento_rt
        if datos.vencimiento_gps: payload["vencimiento_gps"] = datos.vencimiento_gps
        if datos.vencimiento_seguro: payload["vencimiento_seguro"] = datos.vencimiento_seguro
        if datos.lunas_polarizadas is not None: payload["lunas_polarizadas"] = datos.lunas_polarizadas
        if datos.modelo is not None: payload["modelo"] = datos.modelo
        if datos.ano is not None: payload["ano"] = datos.ano
        if datos.tipo is not None: payload["tipo"] = datos.tipo
        if datos.tipo_propiedad is not None: payload["tipo_propiedad"] = datos.tipo_propiedad
        if datos.ultimo_mantenimiento_km is not None: payload["ultimo_mantenimiento_km"] = datos.ultimo_mantenimiento_km
        if datos.frecuencia_mantenimiento is not None: payload["frecuencia_mantenimiento"] = datos.frecuencia_mantenimiento
        
        if datos.ultimo_mantenimiento_km is not None and datos.frecuencia_mantenimiento is not None:
            payload["proximo_mantenimiento_km"] = datos.ultimo_mantenimiento_km + datos.frecuencia_mantenimiento

        res = requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{datos.vehiculo_id}", headers=supabase_headers(), json=payload)
        if res.status_code not in [200, 201, 204]: raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "success", "message": "Datos actualizados."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
