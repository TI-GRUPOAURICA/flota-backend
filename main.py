import os
import requests
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, List

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

app = FastAPI(title="Grupo Aurica ERP - Flota Supabase Pro")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

# ==========================================
# TRADUCTORES DE CAPA (Mappers de Compatibilidad)
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
        "cr596_fechahoraretorno": v.get("fecha_retorno"),
        "conductor_id": str(v.get("conductor_id")) if v.get("conductor_id") else None
    }

# ==========================================
# MODELOS DE RECEPCIÓN (Pydantic)
# ==========================================
class RegistroSalida(BaseModel):
    vehiculo_id: str
    conductor_id: str  
    km_salida: int
    combustible_salida: int
    destino: str = "" # <-- NUEVO CAMPO OBLIGATORIO
    observaciones: str = "" # <-- AHORA ES OPCIONAL
    chk_brisas: bool = True
    chk_parachoques: bool = True
    chk_llantas: bool = True
    chk_puertas: bool = True
    chk_luces: bool = True
    chk_bocina: bool = True
    chk_maletero: bool = True
    chk_lunas: bool = True
    chk_limpieza: bool = True
    chk_guardafangos: bool = True
    chk_capo: bool = True
    chk_cinturon: bool = True

class RegistroRetorno(BaseModel):
    movimiento_id: str
    vehiculo_id: str  
    km_retorno: int
    combustible_retorno: int
    reporta_gastos: bool
    detalle_gastos: str = "" # <-- NUEVO CAMPO PARA GASTOS
    observaciones_retorno: str = "" # <-- AHORA ES SOLO PARA NOVEDADES DEL AUTO 
    estado_llegada: int = 144280000  
    detalle_taller: str = ""
    chk_brisas: bool = True
    chk_parachoques: bool = True
    chk_llantas: bool = True
    chk_puertas: bool = True
    chk_luces: bool = True
    chk_bocina: bool = True
    chk_maletero: bool = True
    chk_lunas: bool = True
    chk_limpieza: bool = True
    chk_guardafangos: bool = True
    chk_capo: bool = True
    chk_cinturon: bool = True

class CargaCombustible(BaseModel):
    vehiculo_id: str
    viaje_id: Optional[str] = None
    volumen_vol: float
    tipo_combustible: str
    costo_total: float
    estacion: str
    kilometraje_carga: int

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

class ActualizarVehiculo(BaseModel):
    vehiculo_id: str
    estado_operativo: Optional[int] = None
    ultimo_mantenimiento_km: Optional[int] = None
    frecuencia_mantenimiento: Optional[int] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
    tipo: Optional[str] = None
    tipo_propiedad: Optional[int] = None

# ==========================================
# ENDPOINTS: GESTIÓN DE CONDUCTORES
# ==========================================

@app.get("/conductores-autorizados")
def listar_conductores():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/conductores?select=*", headers=supabase_headers())
        if res.status_code == 200:
            return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS: OPERACIONES DE GARITA
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
        res_cond = requests.get(f"{SUPABASE_URL}/rest/v1/conductores?id=eq.{registro.conductor_id}&select=*", headers=supabase_headers())
        if res_cond.status_code != 200 or not res_cond.json():
            raise HTTPException(status_code=404, detail="Conductor no encontrado.")
            
        conductor = res_cond.json()[0]
        vencimiento = datetime.strptime(conductor["vencimiento_brevete"], "%Y-%m-%d").date()
        hoy = datetime.now(timezone.utc).date()
        
        if vencimiento < hoy:
            raise HTTPException(status_code=400, detail=f"❌ ALERTA CRÍTICA: El brevete de {conductor['nombre']} está VENCIDO desde el {conductor['vencimiento_brevete']}. Salida rechazada.")

        hora_actual = datetime.now(timezone.utc).isoformat()
        checklist_salida = {
            "brisas": registro.chk_brisas, "parachoques": registro.chk_parachoques, "llantas": registro.chk_llantas,
            "puertas": registro.chk_puertas, "luces": registro.chk_luces, "bocina": registro.chk_bocina,
            "maletero": registro.chk_maletero, "lunas": registro.chk_lunas, "limpieza": registro.chk_limpieza,
            "guardafangos": registro.chk_guardafangos, "capo": registro.chk_capo, "cinturon": registro.chk_cinturon
        }

        payload_viaje = {
            "vehiculo_id": registro.vehiculo_id,
            "conductor_id": registro.conductor_id,
            "nombre_viaje": f"Ruta-{hora_actual[:10]}",
            "km_salida": registro.km_salida,
            "combustible_salida": registro.combustible_salida,
            "fecha_salida": hora_actual,
            "destino": registro.destino, # <-- NUEVO CAMPO ENVIADO A SUPABASE
            "observaciones_salida": registro.observaciones,
            "checklist_salida": checklist_salida
        }
        
        res_viaje = requests.post(f"{SUPABASE_URL}/rest/v1/viajes", headers=supabase_headers(), json=payload_viaje)
        if res_viaje.status_code not in [200, 201, 204]: raise HTTPException(status_code=res_viaje.status_code, detail=res_viaje.text)
        
        for componente, estado in checklist_salida.items():
            if not estado:
                payload_incidente = {
                    "vehiculo_id": registro.vehiculo_id,
                    "descripcion": f"Falla detectada en salida: Componente [{componente.upper()}] con observaciones.",
                    "origen": "Checklist Salida"
                }
                requests.post(f"{SUPABASE_URL}/rest/v1/incidentes", headers=supabase_headers(), json=payload_incidente)

        requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{registro.vehiculo_id}", headers=supabase_headers(), json={"estado_operativo": 144280001})
        return {"status": "success", "message": "¡Salida autorizada y registrada con éxito!"}
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@app.patch("/registrar-retorno")
def registrar_retorno(registro: RegistroRetorno):
    try:
        hora_actual = datetime.now(timezone.utc).isoformat()
        checklist_retorno = {
            "brisas": registro.chk_brisas, "parachoques": registro.chk_parachoques, "llantas": registro.chk_llantas,
            "puertas": registro.chk_puertas, "luces": registro.chk_luces, "bocina": registro.chk_bocina,
            "maletero": registro.chk_maletero, "lunas": registro.chk_lunas, "limpieza": registro.chk_limpieza,
            "guardafangos": registro.chk_guardafangos, "capo": registro.chk_capo, "cinturon": registro.chk_cinturon
        }

        payload_viaje = {
            "km_retorno": registro.km_retorno,
            "combustible_retorno": registro.combustible_retorno,
            "fecha_retorno": hora_actual,
            "reporta_gastos": registro.reporta_gastos,
            "detalle_gastos": registro.detalle_gastos, # <-- NUEVO CAMPO ENVIADO A SUPABASE
            "observaciones_retorno": registro.observaciones_retorno,
            "detalle_taller": registro.detalle_taller,
            "checklist_salida": checklist_retorno 
        }
        
        res_viaje = requests.patch(f"{SUPABASE_URL}/rest/v1/viajes?id=eq.{registro.movimiento_id}", headers=supabase_headers(), json=payload_viaje)
        if res_viaje.status_code not in [200, 201, 204]: raise HTTPException(status_code=res_viaje.status_code, detail=res_viaje.text)
            
        for componente, estado in checklist_retorno.items():
            if not estado:
                payload_incidente = {
                    "vehiculo_id": registro.vehiculo_id,
                    "viaje_id": registro.movimiento_id,
                    "descripcion": f"Falla crítica reportada en retorno: Componente [{componente.upper()}] dañado o ausente.",
                    "origen": "Checklist Retorno"
                }
                requests.post(f"{SUPABASE_URL}/rest/v1/incidentes", headers=supabase_headers(), json=payload_incidente)

        payload_veh = {"estado_operativo": registro.estado_llegada, "kilometraje_actual": registro.km_retorno, "nivel_combustible": registro.combustible_retorno}
        requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{registro.vehiculo_id}", headers=supabase_headers(), json=payload_veh)
        return {"status": "success", "message": "Retorno e incidentes procesados correctamente."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# REQUERIMIENTO: CONTROL Y REGISTRO DE COMBUSTIBLE
# ==========================================

@app.post("/registrar-carga-combustible")
def registrar_carga_combustible(carga: CargaCombustible):
    try:
        endpoint_last = f"{SUPABASE_URL}/rest/v1/cargas_combustible?vehiculo_id=eq.{carga.vehiculo_id}&order=fecha_carga.desc&limit=1"
        res_last = requests.get(endpoint_last, headers=supabase_headers())
        
        rendimiento_calculado = 0.0
        if res_last.status_code == 200 and res_last.json():
            ultima_carga = res_last.json()[0]
            km_anterior = ultima_carga["kilometraje_carga"]
            km_recorridos = carga.kilometraje_carga - km_anterior
            
            if km_recorridos > 0 and carga.volumen_vol > 0:
                rendimiento_calculado = round(km_recorridos / float(carga.volumen_vol), 2)

        payload_carga = {
            "vehiculo_id": carga.vehiculo_id, "viaje_id": carga.viaje_id,
            "volumen_vol": carga.volumen_vol, "tipo_combustible": carga.tipo_combustible,
            "costo_total": carga.costo_total, "estacion": carga.estacion, "kilometraje_carga": carga.kilometraje_carga
        }
        res_insert = requests.post(f"{SUPABASE_URL}/rest/v1/cargas_combustible", headers=supabase_headers(), json=payload_carga)
        if res_insert.status_code not in [200, 201, 204]: raise HTTPException(status_code=res_insert.status_code, detail=res_insert.text)

        requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{carga.vehiculo_id}", headers=supabase_headers(), json={"kilometraje_actual": carga.kilometraje_carga})

        return {
            "status": "success", 
            "message": "Carga de combustible registrada.", 
            "rendimiento_periodo": f"{rendimiento_calculado} Km/Unidad Vol."
        }
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS RESTANTES (Mantenimiento e Historiales)
# ==========================================

@app.get("/vehiculo-incidentes/{vehiculo_id}")
def listar_incidentes_vehiculo(vehiculo_id: str):
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/incidentes?vehiculo_id=eq.{vehiculo_id}&order=fecha_incidente.desc", headers=supabase_headers())
        if res.status_code == 200: return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/viajes-con-gastos")
def listar_viajes_con_gastos():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/viajes?reporta_gastos=eq.true&select=*", headers=supabase_headers())
        if res.status_code == 200: return {"status": "success", "data": [mapear_viaje(v) for v in res.json()]}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/registrar-gasto")
def registrar_gasto(registro: RegistroGasto):
    try:
        payload_gasto = {
            "vehiculo_id": registro.vehiculo_id, "tipo_gasto": registro.tipo_gasto, "fecha_gasto": registro.fecha, 
            "empresa": registro.empresa, "proveedor": registro.proveedor, "comprobante": registro.comprobante, 
            "monto": registro.monto, "metodo_pago": registro.metodo_pago, "observacion": registro.observacion
        }
        if registro.movimiento_id: payload_gasto["viaje_id"] = registro.movimiento_id
        res_gasto = requests.post(f"{SUPABASE_URL}/rest/v1/gastos", headers=supabase_headers(), json=payload_gasto)
        if registro.movimiento_id: requests.patch(f"{SUPABASE_URL}/rest/v1/viajes?id=eq.{registro.movimiento_id}", headers=supabase_headers(), json={"reporta_gastos": False})
        return {"status": "success", "message": "Gasto registrado."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/estado-flota")
def estado_flota():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/vehiculos?select=*", headers=supabase_headers())
        if res.status_code == 200: return {"status": "success", "data": [mapear_vehiculo(v) for v in res.json()]}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.patch("/actualizar-vehiculo")
def actualizar_vehiculo(datos: ActualizarVehiculo):
    try:
        payload = {}
        if datos.estado_operativo is not None: payload["estado_operativo"] = datos.estado_operativo
        if datos.modelo is not None: payload["modelo"] = datos.modelo
        if datos.ano is not None: payload["ano"] = datos.ano
        if datos.tipo is not None: payload["tipo"] = datos.tipo
        if datos.tipo_propiedad is not None: payload["tipo_propiedad"] = datos.tipo_propiedad
        res = requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{datos.vehiculo_id}", headers=supabase_headers(), json=payload)
        return {"status": "success", "message": "Datos actualizados."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/historial-rutas")
def historial_rutas():
    try:
        # Usamos un JOIN nativo de Supabase para traer los nombres reales cruzando tablas
        query = "select=*,vehiculos(placa,nombre),conductores(nombre)&km_retorno=not.is.null&order=fecha_retorno.desc&limit=200"
        res = requests.get(f"{SUPABASE_URL}/rest/v1/viajes?{query}", headers=supabase_headers())
        
        if res.status_code == 200:
            return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))
# ==========================================
# ENDPOINTS: ADMINISTRACIÓN DE PERSONAL (FASE 3)
# ==========================================

class NuevoConductor(BaseModel):
    nombre: str
    brevete: str
    vencimiento_brevete: str

class ActualizarConductor(BaseModel):
    id: str
    nombre: Optional[str] = None
    brevete: Optional[str] = None
    vencimiento_brevete: Optional[str] = None

@app.post("/conductores")
def crear_conductor(conductor: NuevoConductor):
    try:
        payload = {
            "nombre": conductor.nombre,
            "brevete": conductor.brevete,
            "vencimiento_brevete": conductor.vencimiento_brevete
        }
        res = requests.post(f"{SUPABASE_URL}/rest/v1/conductores", headers=supabase_headers(), json=payload)
        if res.status_code not in [200, 201, 204]: 
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "success", "message": "Conductor registrado correctamente."}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/conductores")
def actualizar_conductor(conductor: ActualizarConductor):
    try:
        payload = {}
        if conductor.nombre: payload["nombre"] = conductor.nombre
        if conductor.brevete: payload["brevete"] = conductor.brevete
        if conductor.vencimiento_brevete: payload["vencimiento_brevete"] = conductor.vencimiento_brevete
        
        res = requests.patch(f"{SUPABASE_URL}/rest/v1/conductores?id=eq.{conductor.id}", headers=supabase_headers(), json=payload)
        if res.status_code not in [200, 201, 204]: 
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "success", "message": "Datos del conductor actualizados."}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conductores/{conductor_id}")
def eliminar_conductor(conductor_id: str):
    try:
        res = requests.delete(f"{SUPABASE_URL}/rest/v1/conductores?id=eq.{conductor_id}", headers=supabase_headers())
        if res.status_code not in [200, 201, 204]: 
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "success", "message": "Conductor eliminado del sistema."}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))
