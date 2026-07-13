import os
import requests
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, List


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "").strip()
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "").strip()
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "").strip()
MAIL_SENDER = os.getenv("MAIL_SENDER", "").strip()

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
        "cr596_capacidadtanquelitros": v.get("capacidad_tanque"),
        "cr596_rendimientoesperado": v.get("rendimiento_esperado"),
        "cr596_tipocombustible": v.get("tipo_combustible"),
        "cr596_ultimomantenimientokm": v.get("ultimo_mantenimiento_km"),
        "cr596_frecuenciamantenimiento": v.get("frecuencia_mantenimiento"),
        "cr596_proximomantenimientokm": v.get("proximo_mantenimiento_km"),
        "cr596_vencimientosoat": v.get("vencimiento_soat"),
        "cr596_vencimientorevisiontecnica": v.get("vencimiento_rt"),
        "cr596_vencimientoseguro": v.get("vencimiento_seguro"),
        "cr596_vencimientogps": v.get("vencimiento_gps"),
        "cr596_lunaspolarizadas": v.get("lunas_polarizadas"),
        "notas_mantenimiento": v.get("notas_mantenimiento"),
        "cr596_sistemacombustible": v.get("sistemacombustible", "Simple"),
        "cr596_capacidadtanquegas": v.get("capacidadtanquegas"),
        "cr596_rendimientoesperadogas": v.get("rendimientoesperadogas")
    }

def mapear_viaje(v):
    return {
        "cr596_flota_movimientoid": str(v.get("id")),
        "cr596_nombre": v.get("nombre_viaje"),
        "cr596_kmsalida": v.get("km_salida"),
        "combustible_salida": v.get("combustible_salida"),
        "combustible_salida_gas": v.get("combustible_salida_gas"),
        "combustible_retorno_gas": v.get("combustible_retorno_gas"),
        "_cr596_vehiculo_value": str(v.get("vehiculo_id")),
        "cr596_observacionesretorno": v.get("observaciones_retorno"),
        "cr596_fechahoraretorno": v.get("fecha_retorno"),
        "conductor_id": str(v.get("conductor_id")) if v.get("conductor_id") else None,
        "origen": v.get("origen"),
        "origen_detalle": v.get("origen_detalle"),
        "destino": v.get("destino"),
        "fecha_salida": v.get("fecha_salida"),
        "observaciones_salida": v.get("observaciones_salida"),
        "conductores": v.get("conductores"),
        "checklist_salida": v.get("checklist_salida")
    }

# ==========================================
# MODELOS DE RECEPCIÓN (Pydantic)
# ==========================================
class RegistroSalida(BaseModel):
    vehiculo_id: str
    conductor_id: str  
    km_salida: int
    combustible_salida: int
    combustible_salida_gas: Optional[int] = None
    destino: str = ""
    observaciones: str = ""
    origen: str = ""
    origen_detalle: str = ""
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
    chk_otros: bool = True
    detalles_checklist: dict = {}
    docs_validados: Optional[bool] = None

class RegistroRetorno(BaseModel):
    movimiento_id: str
    vehiculo_id: str  
    km_retorno: int
    combustible_retorno: int
    combustible_retorno_gas: Optional[int] = None
    reporta_gastos: bool
    detalle_gastos: str = ""
    observaciones_retorno: str = ""
    estado_llegada: str = "Disponible"  
    reporta_siniestro: bool = False
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
    chk_otros: bool = True
    motivo_taller: str = ""
    detalles_checklist: dict = {}

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
    estado_operativo: Optional[str] = None
    modelo: Optional[str] = None
    ano: Optional[int] = None
    tipo: Optional[str] = None
    sistema_combustible: Optional[str] = None
    capacidad_tanque_gas: Optional[float] = None
    rendimiento_esperado_gas: Optional[float] = None
    tipo_propiedad: Optional[int] = None
    frecuencia_mantenimiento: Optional[int] = None
    ultimo_mantenimiento_km: Optional[int] = None
    capacidad_tanque: Optional[int] = None
    rendimiento_esperado: Optional[float] = None
    notas_mantenimiento: Optional[str] = None
    detalle_reparacion: Optional[str] = None
    vencimiento_soat: Optional[str] = None
    vencimiento_rt: Optional[str] = None
    vencimiento_seguro: Optional[str] = None
    vencimiento_gps: Optional[str] = None
    lunas_polarizadas: Optional[int] = None
    motivo_cambio_estado: Optional[str] = None
    kilometraje_actual_test: Optional[int] = None
    nivel_combustible_test: Optional[int] = None

class NuevoSiniestro(BaseModel):
    vehiculo_id: str
    fecha_ocurrencia: str
    responsable: str
    descripcion: str
    estado: str = "Reportado"
    url_documentos: str = ""

class ActualizarSiniestro(BaseModel):
    id: str
    estado: Optional[str] = None
    fecha_cierre: Optional[str] = None
    url_documentos: Optional[str] = None
    observacion: Optional[str] = None
    nombre_taller: Optional[str] = None
    sobrescribir_descripcion: bool = False

class NuevoPermiso(BaseModel):
    email: str
    mod_dashboard: bool = False
    mod_mantenimiento: bool = False
    mod_garita: bool = False
    mod_tesoreria: bool = False
    mod_admin: bool = False
    mod_siniestros: bool = False
    mod_conta: bool = False
    recibe_alertas: bool = False

class ActualizarPermiso(BaseModel):
    id: str
    mod_dashboard: Optional[bool] = None
    mod_mantenimiento: Optional[bool] = None
    mod_garita: Optional[bool] = None
    mod_tesoreria: Optional[bool] = None
    mod_admin: Optional[bool] = None
    mod_siniestros: Optional[bool] = None
    mod_conta: Optional[bool] = None
    recibe_alertas: Optional[bool] = None

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
        res = requests.get(f"{SUPABASE_URL}/rest/v1/viajes?km_retorno=is.null&select=*,conductores(nombre)", headers=supabase_headers())
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

        # ==========================================
        # VALIDACIÓN DEL VEHÍCULO Y DOCUMENTOS
        # ==========================================
        res_veh = requests.get(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{registro.vehiculo_id}&select=*", headers=supabase_headers())
        if res_veh.status_code != 200 or not res_veh.json():
            raise HTTPException(status_code=404, detail="Vehículo no encontrado.")
        vehiculo = res_veh.json()[0]

        if vehiculo.get("estado_operativo") in ["Siniestro", "Mantenimiento Correctivo", "Mantenimiento Preventivo"]:
            raise HTTPException(status_code=400, detail="❌ ALERTA CRÍTICA: El vehículo se encuentra en estado de TALLER/CRÍTICO o SINIESTRO. Salida rechazada.")

        doc_vencidos = []
        hoy_str = hoy.isoformat()
        
        if vehiculo.get("vencimiento_soat") and vehiculo.get("vencimiento_soat") < hoy_str: doc_vencidos.append("SOAT")
        if vehiculo.get("vencimiento_rt") and vehiculo.get("vencimiento_rt") < hoy_str: doc_vencidos.append("Revisión Técnica")
        if vehiculo.get("vencimiento_seguro") and vehiculo.get("vencimiento_seguro") < hoy_str: doc_vencidos.append("Seguro Vehicular")
        if vehiculo.get("vencimiento_gps") and vehiculo.get("vencimiento_gps") < hoy_str: doc_vencidos.append("Servicio GPS")
        
        km_actual = vehiculo.get("kilometraje_actual") or 0
        if registro.km_salida < km_actual:
            raise HTTPException(status_code=400, detail=f"❌ El kilometraje de salida ({registro.km_salida}) no puede ser menor al actual ({km_actual}).")

        prox_mante = vehiculo.get("proximo_mantenimiento_km") or 0
        if prox_mante > 0 and km_actual >= prox_mante:
            doc_vencidos.append("Mantenimiento por Km")

        if doc_vencidos:
            raise HTTPException(status_code=400, detail=f"❌ ALERTA CRÍTICA: Vehículo con documentos/mantenimiento vencido ({', '.join(doc_vencidos)}). Salida rechazada.")

        hora_actual = datetime.now(timezone.utc).isoformat()
        checklist_salida = {
            "brisas": registro.chk_brisas, "parachoques": registro.chk_parachoques, "llantas": registro.chk_llantas,
            "puertas": registro.chk_puertas, "luces": registro.chk_luces, "bocina": registro.chk_bocina,
            "maletero": registro.chk_maletero, "lunas": registro.chk_lunas, "limpieza": registro.chk_limpieza,
            "guardafangos": registro.chk_guardafangos, "capo": registro.chk_capo, "cinturon": registro.chk_cinturon,
            "otros": registro.chk_otros,
            "detalles": registro.detalles_checklist
        }

        obs_final = registro.observaciones
        if registro.docs_validados:
            obs_final += " [Docs físicos validados por Vigilancia]"

        payload_viaje = {
            "vehiculo_id": registro.vehiculo_id,
            "conductor_id": registro.conductor_id,
            "nombre_viaje": f"Ruta-{hora_actual[:10]}",
            "km_salida": registro.km_salida,
            "combustible_salida": registro.combustible_salida,
            "combustible_salida_gas": registro.combustible_salida_gas,
            "fecha_salida": hora_actual,
            "destino": registro.destino,
            "origen": registro.origen,
            "origen_detalle": registro.origen_detalle,
            "observaciones_salida": obs_final.strip(),
            "checklist_salida": checklist_salida
        }
        
        res_viaje = requests.post(f"{SUPABASE_URL}/rest/v1/viajes", headers=supabase_headers(), json=payload_viaje)
        if res_viaje.status_code not in [200, 201, 204]: raise HTTPException(status_code=res_viaje.status_code, detail=res_viaje.text)
        
        for componente, estado in checklist_salida.items():
            if componente == "detalles" or componente == "otros": continue
            if not estado:
                detalle_obs = registro.detalles_checklist.get(componente, "Sin detalle reportado.")
                payload_incidente = {
                    "vehiculo_id": registro.vehiculo_id,
                    "descripcion": f"Falla detectada en salida: Componente [{componente.upper()}]. Detalle: {detalle_obs}",
                    "origen": "Checklist Salida"
                }
                requests.post(f"{SUPABASE_URL}/rest/v1/incidentes", headers=supabase_headers(), json=payload_incidente)

        requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{registro.vehiculo_id}", headers=supabase_headers(), json={"estado_operativo": "En uso"})
        return {"status": "success", "message": "¡Salida autorizada y registrada con éxito!"}
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@app.patch("/registrar-retorno")
def registrar_retorno(registro: RegistroRetorno):
    try:
        res_viaje_db = requests.get(f"{SUPABASE_URL}/rest/v1/viajes?id=eq.{registro.movimiento_id}&select=*", headers=supabase_headers())
        if res_viaje_db.status_code == 200 and res_viaje_db.json():
            viaje = res_viaje_db.json()[0]
            km_salida = viaje.get("km_salida") or 0
            if registro.km_retorno < km_salida:
                raise HTTPException(status_code=400, detail=f"❌ El kilometraje de retorno ({registro.km_retorno}) no puede ser menor al de salida ({km_salida}).")

        hora_actual = datetime.now(timezone.utc).isoformat()
        checklist_retorno = {
            "brisas": registro.chk_brisas, "parachoques": registro.chk_parachoques, "llantas": registro.chk_llantas,
            "puertas": registro.chk_puertas, "luces": registro.chk_luces, "bocina": registro.chk_bocina,
            "maletero": registro.chk_maletero, "lunas": registro.chk_lunas, "limpieza": registro.chk_limpieza,
            "guardafangos": registro.chk_guardafangos, "capo": registro.chk_capo, "cinturon": registro.chk_cinturon,
            "otros": registro.chk_otros,
            "detalles": registro.detalles_checklist
        }

        payload_viaje = {
            "km_retorno": registro.km_retorno,
            "combustible_retorno": registro.combustible_retorno,
            "combustible_retorno_gas": registro.combustible_retorno_gas,
            "fecha_retorno": hora_actual,
            "reporta_gastos": registro.reporta_gastos,
            "detalle_gastos": registro.detalle_gastos,
            "observaciones_retorno": registro.observaciones_retorno,
            "detalle_taller": registro.detalle_taller,
            "checklist_retorno": checklist_retorno 
        }
        
        res_viaje = requests.patch(f"{SUPABASE_URL}/rest/v1/viajes?id=eq.{registro.movimiento_id}", headers=supabase_headers(), json=payload_viaje)
        if res_viaje.status_code not in [200, 201, 204]: raise HTTPException(status_code=res_viaje.status_code, detail=res_viaje.text)
            
        for componente, estado in checklist_retorno.items():
            if not estado:
                detalle_obs = registro.detalles_checklist.get(componente, "Sin detalle reportado.")
                payload_incidente = {
                    "vehiculo_id": registro.vehiculo_id,
                    "viaje_id": registro.movimiento_id,
                    "descripcion": f"Falla reportada en retorno: Componente [{componente.upper()}]. Detalle: {detalle_obs}",
                    "origen": "Checklist Retorno",
                    "kilometraje_incidente": registro.km_retorno
                }
                requests.post(f"{SUPABASE_URL}/rest/v1/incidentes", headers=supabase_headers(), json=payload_incidente)

        payload_veh = {
            "estado_operativo": registro.estado_llegada, 
            "kilometraje_actual": registro.km_retorno, 
            "nivel_combustible": registro.combustible_retorno
        }

        # INTEGRACIÓN: Si ocurrió un siniestro en ruta
        if registro.reporta_siniestro:
            payload_veh["estado_operativo"] = "Siniestro"
            payload_veh["notas_mantenimiento"] = "REPORTE GARITA: Siniestro reportado en ruta."
            # Necesitamos el nombre del responsable, lo sacamos del viaje abierto
            res_v = requests.get(f"{SUPABASE_URL}/rest/v1/viajes?id=eq.{registro.movimiento_id}&select=conductores(nombre)", headers=supabase_headers())
            try:
                responsable = res_v.json()[0]["conductores"]["nombre"]
            except:
                responsable = "Reportado por Garita"
            
            payload_siniestro = {
                "vehiculo_id": registro.vehiculo_id,
                "fecha_ocurrencia": hora_actual,
                "responsable": responsable,
                "descripcion": "Reportado desde Garita. Pendiente revisión y documentos.",
                "estado": "Reportado",
                "url_documentos": ""
            }
            requests.post(f"{SUPABASE_URL}/rest/v1/siniestros", headers=supabase_headers(), json=payload_siniestro)
        
        # LÓGICA INTELIGENTE: Si lo mandan a taller, inyectar la nota
        elif registro.estado_llegada == "Mantenimiento Correctivo" and registro.motivo_taller:
            payload_veh["notas_mantenimiento"] = f"REPORTE GARITA: {registro.motivo_taller}"

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
        if datos.sistema_combustible is not None: payload["sistemacombustible"] = datos.sistema_combustible
        if datos.tipo_propiedad is not None: payload["tipo_propiedad"] = datos.tipo_propiedad
        if datos.frecuencia_mantenimiento is not None: payload["frecuencia_mantenimiento"] = datos.frecuencia_mantenimiento
        if datos.ultimo_mantenimiento_km is not None: payload["ultimo_mantenimiento_km"] = datos.ultimo_mantenimiento_km
        if datos.capacidad_tanque is not None: payload["capacidad_tanque"] = datos.capacidad_tanque
        if datos.rendimiento_esperado is not None: payload["rendimiento_esperado"] = datos.rendimiento_esperado
        if datos.capacidad_tanque_gas is not None: payload["capacidadtanquegas"] = datos.capacidad_tanque_gas
        if datos.rendimiento_esperado_gas is not None: payload["rendimientoesperadogas"] = datos.rendimiento_esperado_gas
        if datos.vencimiento_soat is not None: payload["vencimiento_soat"] = datos.vencimiento_soat
        if datos.vencimiento_rt is not None: payload["vencimiento_rt"] = datos.vencimiento_rt
        if datos.vencimiento_seguro is not None: payload["vencimiento_seguro"] = datos.vencimiento_seguro
        if datos.vencimiento_gps is not None: payload["vencimiento_gps"] = datos.vencimiento_gps
        if datos.lunas_polarizadas is not None: payload["lunas_polarizadas"] = datos.lunas_polarizadas
        if datos.kilometraje_actual_test is not None: payload["kilometraje_actual"] = datos.kilometraje_actual_test
        if datos.nivel_combustible_test is not None: payload["nivel_combustible"] = datos.nivel_combustible_test

        # Obtener nota y estado actual para auditoría antes de cualquier cambio
        res_v = requests.get(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{datos.vehiculo_id}&select=notas_mantenimiento,estado_operativo,kilometraje_actual", headers=supabase_headers())
        vehiculo_actual = res_v.json()[0] if res_v.status_code == 200 and len(res_v.json()) > 0 else {}
        nota_actual = vehiculo_actual.get("notas_mantenimiento", "")
        estado_actual = vehiculo_actual.get("estado_operativo", "")
        km_actual = vehiculo_actual.get("kilometraje_actual", 0)

        # 1. Si el Jefe manda un motivo de ingreso, actualizar la alerta
        if datos.notas_mantenimiento is not None: 
            payload["notas_mantenimiento"] = datos.notas_mantenimiento

        # 2. Si el auto vuelve a estar Operativo (Libre), borramos la alerta roja
        if datos.estado_operativo == "Disponible": 
            payload["notas_mantenimiento"] = "" 

        # 3. AUDITORÍA: Si el Jefe escribió una reparación, la guardamos en el historial para siempre
        if datos.detalle_reparacion:
            es_siniestro = nota_actual and ("siniestro" in nota_actual.lower())
            origen_inc = "Siniestro" if es_siniestro else "Mantenimiento"
            prefijo = "LIBERACIÓN DE SINIESTRO:" if es_siniestro else "LIBERACIÓN TALLER:"
            
            payload_incidente = {
                "vehiculo_id": datos.vehiculo_id,
                "descripcion": f"{prefijo} {datos.detalle_reparacion}",
                "origen": origen_inc,
                "kilometraje_incidente": km_actual
            }
            requests.post(f"{SUPABASE_URL}/rest/v1/incidentes", headers=supabase_headers(), json=payload_incidente)
            
        # 4. AUDITORÍA DE CAMBIO DE ESTADO: Registrar si el estado cambia (Baja, Preventivo, etc.)
        if datos.estado_operativo and datos.estado_operativo != estado_actual:
            estados_auditables = ["Mantenimiento Preventivo", "Mantenimiento Correctivo", "Baja Temporal", "Dado de Baja"]
            if datos.estado_operativo in estados_auditables:
                motivo = f" Motivo: {datos.motivo_cambio_estado}" if datos.motivo_cambio_estado else ""
                payload_incidente = {
                    "vehiculo_id": datos.vehiculo_id,
                    "descripcion": f"[CAMBIO DE ESTADO] El vehículo pasó a {datos.estado_operativo.upper()}.{motivo}",
                    "origen": "Auditoría de Estado",
                    "kilometraje_incidente": km_actual
                }
                requests.post(f"{SUPABASE_URL}/rest/v1/incidentes", headers=supabase_headers(), json=payload_incidente)

        res = requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{datos.vehiculo_id}", headers=supabase_headers(), json=payload)
        return {"status": "success", "message": "Datos actualizados."}
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

@app.get("/reporte-gastos")
def reporte_gastos(inicio: str, fin: str):
    try:
        query = f"select=*,vehiculos(placa,nombre)&fecha_gasto=gte.{inicio}T00:00:00&fecha_gasto=lte.{fin}T23:59:59"
        res = requests.get(f"{SUPABASE_URL}/rest/v1/gastos?{query}", headers=supabase_headers())
        if res.status_code == 200:
            return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS: HISTORIALES, REPORTES Y AUDITORÍA
# ==========================================

@app.get("/vehiculo-incidentes/{vehiculo_id}")
def listar_incidentes_vehiculo(vehiculo_id: str):
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/incidentes?vehiculo_id=eq.{vehiculo_id}&order=fecha_incidente.desc", headers=supabase_headers())
        if res.status_code == 200: return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/vehiculo-gastos/{vehiculo_id}")
def vehiculo_gastos(vehiculo_id: str):
    try:
        query = f"select=*&vehiculo_id=eq.{vehiculo_id}&order=fecha_gasto.desc"
        res = requests.get(f"{SUPABASE_URL}/rest/v1/gastos?{query}", headers=supabase_headers())
        if res.status_code == 200: return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/vehiculo-historial-completo/{vehiculo_id}")
def vehiculo_historial_completo(vehiculo_id: str):
    try:
        # Incidentes
        res_i = requests.get(f"{SUPABASE_URL}/rest/v1/incidentes?vehiculo_id=eq.{vehiculo_id}", headers=supabase_headers())
        incidentes = res_i.json() if res_i.status_code == 200 else []
        
        # Siniestros
        res_s = requests.get(f"{SUPABASE_URL}/rest/v1/siniestros?vehiculo_id=eq.{vehiculo_id}", headers=supabase_headers())
        siniestros = res_s.json() if res_s.status_code == 200 else []
        
        historial = []
        for i in incidentes:
            historial.append({
                "tipo": "Incidente Mecánico",
                "fecha": i.get("fecha_incidente"),
                "conductor": i.get("origen") or "No especificado",
                "descripcion": i.get("descripcion", ""),
                "estado": "N/A",
                "docs": i.get("url_documentos", "")
            })
        for s in siniestros:
            historial.append({
                "tipo": "Siniestro",
                "fecha": s.get("fecha_ocurrencia"),
                "conductor": s.get("responsable", "No especificado"),
                "descripcion": s.get("descripcion", ""),
                "estado": s.get("estado", "Reportado"),
                "docs": s.get("url_documentos", "")
            })
        
        historial.sort(key=lambda x: x["fecha"] or "", reverse=True)
        return {"status": "success", "data": historial}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/historial-rutas")
def historial_rutas():
    try:
        query = "select=*,vehiculos(placa,nombre,capacidad_tanque,rendimiento_esperado,sistemacombustible,capacidadtanquegas,rendimientoesperadogas),conductores(nombre)&km_retorno=not.is.null&order=fecha_retorno.desc&limit=500"
        res = requests.get(f"{SUPABASE_URL}/rest/v1/viajes?{query}", headers=supabase_headers())
        if res.status_code == 200: return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/historial-global-unificado")
def historial_global_unificado():
    try:
        # Obtener incidentes
        query_i = "select=*,vehiculos(placa,nombre)&order=fecha_incidente.desc&limit=500"
        res_i = requests.get(f"{SUPABASE_URL}/rest/v1/incidentes?{query_i}", headers=supabase_headers())
        incidentes = res_i.json() if res_i.status_code == 200 else []
        
        # Obtener siniestros
        query_s = "select=*,vehiculos(placa,nombre)&order=fecha_ocurrencia.desc&limit=500"
        res_s = requests.get(f"{SUPABASE_URL}/rest/v1/siniestros?{query_s}", headers=supabase_headers())
        siniestros = res_s.json() if res_s.status_code == 200 else []
        
        historial = []
        for i in incidentes:
            historial.append({
                "id_unico": f"inc_{i.get('id', '')}",
                "tipo": "Mantenimiento / Falla",
                "fecha": i.get("fecha_incidente"),
                "placa": i.get("vehiculos", {}).get("placa", "S/P") if isinstance(i.get("vehiculos"), dict) else "S/P",
                "vehiculo": i.get("vehiculos", {}).get("nombre", "S/N") if isinstance(i.get("vehiculos"), dict) else "S/N",
                "conductor": i.get("origen") or "Mantenimiento",
                "descripcion": i.get("descripcion", ""),
                "estado": "N/A",
                "docs": i.get("url_documentos", "")
            })
        for s in siniestros:
            historial.append({
                "id_unico": f"sin_{s.get('id', '')}",
                "tipo": "Siniestro",
                "fecha": s.get("fecha_ocurrencia"),
                "placa": s.get("vehiculos", {}).get("placa", "S/P") if isinstance(s.get("vehiculos"), dict) else "S/P",
                "vehiculo": s.get("vehiculos", {}).get("nombre", "S/N") if isinstance(s.get("vehiculos"), dict) else "S/N",
                "conductor": s.get("responsable", "No especificado"),
                "descripcion": s.get("descripcion", ""),
                "estado": s.get("estado", "Reportado"),
                "docs": s.get("url_documentos", "")
            })
        
        historial.sort(key=lambda x: x["fecha"] or "", reverse=True)
        return {"status": "success", "data": historial}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS: SINIESTROS
# ==========================================

@app.get("/siniestros")
def listar_siniestros():
    try:
        query = "select=*,vehiculos(placa,nombre)&order=fecha_ocurrencia.desc"
        res = requests.get(f"{SUPABASE_URL}/rest/v1/siniestros?{query}", headers=supabase_headers())
        if res.status_code == 200: return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except HTTPException as he:
        raise he
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/registrar-siniestro")
def registrar_siniestro(datos: NuevoSiniestro):
    try:
        payload = {
            "vehiculo_id": datos.vehiculo_id,
            "fecha_ocurrencia": datos.fecha_ocurrencia,
            "responsable": datos.responsable,
            "descripcion": datos.descripcion,
            "estado": datos.estado,
            "url_documentos": datos.url_documentos
        }
        res = requests.post(f"{SUPABASE_URL}/rest/v1/siniestros", headers=supabase_headers(), json=payload)
        if res.status_code not in [200, 201, 204]: 
            raise HTTPException(status_code=res.status_code, detail=res.text)
            
        # Si el vehículo tiene un siniestro, lo marcamos en la tabla de vehículos
        # Y creamos el incidente correspondiente para la Historia Clínica
        res_v = requests.get(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{datos.vehiculo_id}&select=kilometraje_actual", headers=supabase_headers())
        veh_actual = res_v.json()[0] if res_v.status_code == 200 and len(res_v.json()) > 0 else {}
        km_actual = veh_actual.get("kilometraje_actual", 0)

        requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{datos.vehiculo_id}", headers=supabase_headers(), json={"estado_operativo": "Siniestro"})
            
        payload_incidente = {
            "vehiculo_id": datos.vehiculo_id,
            "descripcion": f"[SINIESTRO REPORTADO] {datos.descripcion}",
            "origen": "Siniestro",
            "kilometraje_incidente": km_actual
        }
        requests.post(f"{SUPABASE_URL}/rest/v1/incidentes", headers=supabase_headers(), json=payload_incidente)

        return {"status": "success", "message": "Siniestro registrado correctamente."}
    except HTTPException as he:
        raise he
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subir-documento-siniestro")
async def subir_documento_siniestro(file: UploadFile = File(...)):
    import urllib.parse
    import re
    import unicodedata
    try:
        content = await file.read()
        
        # Sanitización agresiva del nombre
        filename_nfkd = unicodedata.normalize('NFKD', file.filename).encode('ASCII', 'ignore').decode('utf-8')
        safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', filename_nfkd.replace(" ", "_"))
        file_name = f"{int(datetime.now().timestamp())}_{safe_filename}"
        
        headers = supabase_headers()
        # Sobreescribimos el content type para el upload
        headers["Content-Type"] = file.content_type
        
        # Llamada a Supabase Storage (Bucket: documentos)
        url_segura = f"{SUPABASE_URL}/storage/v1/object/documentos/{urllib.parse.quote(file_name)}"
        res = requests.post(url_segura, headers=headers, data=content)
        if res.status_code not in [200, 201]:
            raise HTTPException(status_code=res.status_code, detail=res.text)
            
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/documentos/{urllib.parse.quote(file_name)}"
        return {"status": "success", "url": public_url}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/actualizar-siniestro")
def actualizar_siniestro(datos: ActualizarSiniestro):
    try:
        payload = {}
        if datos.estado: payload["estado"] = datos.estado
        if datos.url_documentos: payload["url_documentos"] = datos.url_documentos
        if datos.nombre_taller: payload["nombre_taller"] = datos.nombre_taller
        
        # Recuperar vehiculo_id y descripcion actual para añadir observación
        res_s = requests.get(f"{SUPABASE_URL}/rest/v1/siniestros?id=eq.{datos.id}&select=descripcion,vehiculo_id", headers=supabase_headers())
        veh_id = None
        if res_s.status_code == 200 and res_s.json():
            siniestro_actual = res_s.json()[0]
            veh_id = siniestro_actual.get("vehiculo_id")
            if datos.observacion:
                if datos.sobrescribir_descripcion:
                    payload["descripcion"] = datos.observacion
                else:
                    desc_actual = siniestro_actual.get("descripcion", "")
                    estado_str = f"Cambio a {datos.estado}" if datos.estado else "Observación"
                    nueva_desc = desc_actual + f"\n\n[{datetime.now().strftime('%d/%m/%Y')} - {estado_str}]: {datos.observacion}"
                    payload["descripcion"] = nueva_desc
        
        if datos.estado == "Cerrado" and veh_id:
            payload["fecha_cierre"] = datetime.now().isoformat()
            
            # Liberar el vehículo a Mantenimiento Correctivo para que el Jefe de Mantenimiento pueda editarlo
            requests.patch(f"{SUPABASE_URL}/rest/v1/vehiculos?id=eq.{veh_id}", headers=supabase_headers(), 
json={"estado_operativo": "Mantenimiento Correctivo", "notas_mantenimiento": "Siniestro Cerrado - Requiere liberación técnica en taller."})
                
        res = requests.patch(f"{SUPABASE_URL}/rest/v1/siniestros?id=eq.{datos.id}", headers=supabase_headers(), json=payload)
        if res.status_code not in [200, 201, 204]: 
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "success", "message": "Siniestro actualizado."}
    except HTTPException as he:
        raise he
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS: GESTIÓN DE PERMISOS
# ==========================================

@app.get("/permisos")
def listar_permisos():
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios_permisos?select=*", headers=supabase_headers())
        if res.status_code == 200: return {"status": "success", "data": res.json()}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/permisos/{email}")
def obtener_permiso_usuario(email: str):
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios_permisos?email=eq.{email}&select=*", headers=supabase_headers())
        if res.status_code == 200: 
            data = res.json()
            if len(data) > 0:
                return {"status": "success", "data": data[0]}
            else:
                return {"status": "not_found", "message": "Usuario no tiene permisos asignados."}
        raise HTTPException(status_code=res.status_code, detail=res.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/permisos")
def crear_permiso(datos: NuevoPermiso):
    try:
        payload = datos.dict()
        res = requests.post(f"{SUPABASE_URL}/rest/v1/usuarios_permisos", headers=supabase_headers(), json=payload)
        if res.status_code not in [200, 201, 204]: 
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "success", "message": "Permisos asignados correctamente."}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/permisos")
def actualizar_permiso(datos: ActualizarPermiso):
    try:
        payload = {k: v for k, v in datos.dict().items() if v is not None and k != "id"}
        res = requests.patch(f"{SUPABASE_URL}/rest/v1/usuarios_permisos?id=eq.{datos.id}", headers=supabase_headers(), json=payload)
        if res.status_code not in [200, 201, 204]: 
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "success", "message": "Permisos actualizados."}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/permisos/{id}")
def eliminar_permiso(id: str):
    try:
        res = requests.delete(f"{SUPABASE_URL}/rest/v1/usuarios_permisos?id=eq.{id}", headers=supabase_headers())
        if res.status_code not in [200, 201, 204]: 
            raise HTTPException(status_code=res.status_code, detail=res.text)
        return {"status": "success", "message": "Acceso revocado."}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS: CRON JOBS Y ALERTAS
# ==========================================

def evaluar_fecha_vencimiento(fecha_str):
    if not fecha_str: return None
    try:
        fecha_venc = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hoy = datetime.now(timezone.utc).date()
        return (fecha_venc - hoy).days
    except:
        return None

def evaluar_km(actual, meta):
    if actual is None or meta is None: return None
    return meta - actual

@app.get("/cron/evaluar-vencimientos")
def evaluar_vencimientos():
    try:
        res_v = requests.get(f"{SUPABASE_URL}/rest/v1/vehiculos?select=*", headers=supabase_headers())
        if res_v.status_code != 200: raise Exception("Error al cargar vehículos")
        vehiculos = res_v.json()

        res_u = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios_permisos?recibe_alertas=eq.true&select=email", headers=supabase_headers())
        if res_u.status_code != 200: raise Exception("Error al cargar usuarios")
        destinatarios = [u["email"] for u in res_u.json()]
        
        if not destinatarios:
            destinatarios = ["mantenimiento@auricasac.com"]

        alertas = []

        for v in vehiculos:
            alertas_vehiculo = []
            
            dias_soat = evaluar_fecha_vencimiento(v.get("vencimiento_soat"))
            if dias_soat is not None and 0 <= dias_soat <= 15:
                alertas_vehiculo.append(f"<b>SOAT:</b> Vence en {dias_soat} días ({v.get('vencimiento_soat')})")
                
            dias_rt = evaluar_fecha_vencimiento(v.get("vencimiento_rt"))
            if dias_rt is not None and 0 <= dias_rt <= 15:
                alertas_vehiculo.append(f"<b>Revisión Técnica:</b> Vence en {dias_rt} días ({v.get('vencimiento_rt')})")

            dias_seguro = evaluar_fecha_vencimiento(v.get("vencimiento_seguro"))
            if dias_seguro is not None and 0 <= dias_seguro <= 15:
                alertas_vehiculo.append(f"<b>Seguro Vehicular:</b> Vence en {dias_seguro} días ({v.get('vencimiento_seguro')})")

            dias_gps = evaluar_fecha_vencimiento(v.get("vencimiento_gps"))
            if dias_gps is not None and 0 <= dias_gps <= 15:
                alertas_vehiculo.append(f"<b>Servicio GPS:</b> Vence en {dias_gps} días ({v.get('vencimiento_gps')})")

            faltan_km = evaluar_km(v.get("kilometraje_actual"), v.get("proximo_mantenimiento_km"))
            if faltan_km is not None and 0 <= faltan_km <= 1000:
                alertas_vehiculo.append(f"<b>Mantenimiento:</b> Faltan {faltan_km} Km (Actual: {v.get('kilometraje_actual')})")

            if alertas_vehiculo:
                alertas.append({
                    "placa": v.get("placa", "S/P"),
                    "nombre": v.get("nombre", "Vehículo"),
                    "detalles": alertas_vehiculo
                })

        if not alertas:
            return {"status": "success", "message": "No hay alertas pendientes hoy."}

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #e74c3c;">🚨 Alertas de Vencimiento de Flota</h2>
            <p>Se han detectado vehículos con documentos o mantenimientos próximos a vencer (15 días o menos).</p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background-color: #305da0; color: white;">
                        <th style="padding: 10px; border: 1px solid #ddd;">Vehículo</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Alertas Críticas</th>
                    </tr>
                </thead>
                <tbody>
        """
        for a in alertas:
            detalles_html = "<br>".join(a["detalles"])
            html_content += f"""
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">[{a['placa']}] {a['nombre']}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: #e74c3c;">{detalles_html}</td>
                    </tr>
            """
        html_content += """
                </tbody>
            </table>
            <p style="margin-top: 20px; font-size: 12px; color: #888;">Este es un mensaje automático del Sistema de Gestión de Flota - Grupo Aurica.</p>
        </body>
        </html>
        """

        if AZURE_TENANT_ID and AZURE_CLIENT_ID and AZURE_CLIENT_SECRET and MAIL_SENDER:
            try:
                # 1. Obtener Token
                token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
                token_data = {
                    "grant_type": "client_credentials",
                    "client_id": AZURE_CLIENT_ID,
                    "client_secret": AZURE_CLIENT_SECRET,
                    "scope": "https://graph.microsoft.com/.default"
                }
                token_res = requests.post(token_url, data=token_data)
                token_res.raise_for_status()
                access_token = token_res.json().get("access_token")

                # 2. Enviar Correo
                to_recipients = [{"emailAddress": {"address": correo.strip()}} for correo in destinatarios if correo.strip()]
                email_msg = {
                    "message": {
                        "subject": "🚨 Alerta de Vencimientos - Flota Grupo Aurica",
                        "body": {"contentType": "HTML", "content": html_content},
                        "toRecipients": to_recipients
                    },
                    "saveToSentItems": "true"
                }

                send_url = f"https://graph.microsoft.com/v1.0/users/{MAIL_SENDER}/sendMail"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                send_res = requests.post(send_url, headers=headers, json=email_msg)
                send_res.raise_for_status()

            except Exception as mail_e:
                print(f"Error enviando correo con Graph API: {mail_e}")
                return {"status": "partial", "message": "Alertas generadas pero falló el envío de correo. Ver logs."}
        else:
            print("Las variables de entorno de Azure AD no están configuradas.")

        return {"status": "success", "message": f"Se enviaron alertas de {len(alertas)} vehículos a {len(destinatarios)} destinatarios."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
