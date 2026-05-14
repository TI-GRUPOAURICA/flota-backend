import os
import requests
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from msal import ConfidentialClientApplication
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID", "").strip()
CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "").strip()
DATAVERSE_URL = os.getenv("DATAVERSE_URL", "").strip()

app = FastAPI(title="Gestión de Flotas API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

authority = f"https://login.microsoftonline.com/{TENANT_ID}"
msal_app = ConfidentialClientApplication(CLIENT_ID, authority=authority, client_credential=CLIENT_SECRET)

def get_token(scope):
    result = msal_app.acquire_token_silent(scope, account=None)
    if not result:
        result = msal_app.acquire_token_for_client(scopes=scope)
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Error de autenticación: {result.get('error_description')}")

# ==========================================
# MODELOS DE DATOS
# ==========================================
class RegistroSalida(BaseModel):
    vehiculo_id: str
    km_salida: int
    combustible_salida: int  # <-- NUEVO CAMPO
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
    combustible_retorno: int # <-- NUEVO CAMPO
    reporta_gastos: bool
    observaciones_retorno: str = ""  
    estado_llegada: int = 144280000  
    detalle_taller: str = ""

class RegistroGasto(BaseModel):
    movimiento_id: Optional[str] = None # Opcional, por si es un gasto suelto que no viene de Garita
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

# ==========================================
# ENDPOINTS DE VIGILANCIA (GARITA)
# ==========================================

@app.get("/vehiculos-activos")
def listar_vehiculos_activos():
    try:
        token = get_token([f"{DATAVERSE_URL}/.default"])
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        endpoint = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_vehiculos?$select=cr596_nombre,cr596_placa,cr596_kilometrajeactual,cr596_estadooperativo"
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return {"status": "success", "data": response.json().get("value", [])}
        else: raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/viajes-abiertos")
def listar_viajes_abiertos():
    try:
        token = get_token([f"{DATAVERSE_URL}/.default"])
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        endpoint = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_movimientos?$filter=cr596_kmretorno eq null&$select=cr596_flota_movimientoid,cr596_nombre,cr596_kmsalida,_cr596_vehiculo_value"
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            return {"status": "success", "data": response.json().get("value", [])}
        else: raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/registrar-salida")
def registrar_salida(registro: RegistroSalida):
    try:
        token = get_token([f"{DATAVERSE_URL}/.default"])
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
        hora_actual = datetime.now(timezone.utc).isoformat()
        
        endpoint_mov = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_movimientos"
        payload_mov = {
            "cr596_nombre": f"Salida-{hora_actual[:10]}",
            "cr596_kmsalida": registro.km_salida,
            "cr596_combustiblesalida": registro.combustible_salida,
            "cr596_fechahorasalida": hora_actual,
            "cr596_Vehiculo@odata.bind": f"/cr596_flota_vehiculos({registro.vehiculo_id})",
            "cr596_observaciones": registro.observaciones,
            "cr596_chk_brisas": registro.chk_brisas, "cr596_chk_parachoques": registro.chk_parachoques,
            "cr596_chk_llantas": registro.chk_llantas, "cr596_chk_puertas": registro.chk_puertas,
            "cr596_chk_luces": registro.chk_luces, "cr596_chk_bocina": registro.chk_bocina,
            "cr596_chk_maletero": registro.chk_maletero, "cr596_chk_lunas": registro.chk_lunas,
            "cr596_chk_limpieza": registro.chk_limpieza, "cr596_chk_guardafangos": registro.chk_guardafangos,
            "cr596_chk_capo": registro.chk_capo, "cr596_chk_cinturon": registro.chk_cinturon
        }
        res_mov = requests.post(endpoint_mov, headers=headers, json=payload_mov)
        if res_mov.status_code != 204: raise HTTPException(status_code=res_mov.status_code, detail=res_mov.text)

        endpoint_veh = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_vehiculos({registro.vehiculo_id})"
        requests.patch(endpoint_veh, headers=headers, json={"cr596_estadooperativo": 144280001})

        return {"status": "success", "message": "¡Salida registrada exitosamente!"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.patch("/registrar-retorno")
def registrar_retorno(registro: RegistroRetorno):
    try:
        token = get_token([f"{DATAVERSE_URL}/.default"])
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
        hora_actual = datetime.now(timezone.utc).isoformat()
        
        endpoint_mov = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_movimientos({registro.movimiento_id})"
        payload_mov = {
            "cr596_kmretorno": registro.km_retorno,
            "cr596_combustibleretorno": registro.combustible_retorno,
            "cr596_fechahoraretorno": hora_actual,
            "cr596_reportagastos": registro.reporta_gastos,
            "cr596_observacionesretorno": registro.observaciones_retorno, 
            "cr596_detalletaller": registro.detalle_taller # Guardamos el reporte del mecánico
        }
        res_mov = requests.patch(endpoint_mov, headers=headers, json=payload_mov)
        if res_mov.status_code != 204: raise HTTPException(status_code=res_mov.status_code, detail=res_mov.text)

      # Actualizamos el vehículo con el estado elegido por el vigilante y el combustible
        endpoint_veh = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_vehiculos({registro.vehiculo_id})"
        payload_veh = {
            "cr596_estadooperativo": registro.estado_llegada,
            "cr596_kilometrajeactual": registro.km_retorno,
            "cr596_nivelcombustible": registro.combustible_retorno # <-- NUEVO: Guarda el nivel de llegada
        }
        requests.patch(endpoint_veh, headers=headers, json=payload_veh)

        return {"status": "success", "message": "Retorno registrado con éxito."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ENDPOINTS DE TESORERÍA, CONTABILIDAD Y MANTENIMIENTO
# (Se mantienen exactamente igual para no romper lo que ya funciona)
# ==========================================
@app.get("/viajes-con-gastos")
def listar_viajes_con_gastos():
    token = get_token([f"{DATAVERSE_URL}/.default"])
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # NUEVO: Ahora traemos también las observaciones y el ID del vehículo para que Tesorería lo vea
    endpoint = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_movimientos?$filter=cr596_reportagastos eq true&$select=cr596_flota_movimientoid,cr596_nombre,cr596_fechahoraretorno,cr596_observacionesretorno,_cr596_vehiculo_value"
    
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200: return {"status": "success", "data": response.json().get("value", [])}
    else: raise HTTPException(status_code=response.status_code, detail=response.text)

class RegistroGasto(BaseModel):
    movimiento_id: Optional[str] = None # Opcional, por si es un gasto suelto que no viene de Garita
    vehiculo_id: str
    tipo_gasto: int
    fecha: str
    empresa: int
    proveedor: str
    comprobante: str
    monto: float
    metodo_pago: int
    observacion: str = ""

@app.post("/registrar-gasto")
def registrar_gasto(registro: RegistroGasto):
    try:
        token = get_token([f"{DATAVERSE_URL}/.default"])
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
        endpoint_gasto = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_gastorutas"
        
        payload_gasto = {
            "cr596_Vehiculo@odata.bind": f"/cr596_flota_vehiculos({registro.vehiculo_id})",
            "cr596_tipogasto": registro.tipo_gasto,
            "cr596_fecha": registro.fecha,
            "cr596_empresa": registro.empresa,
            "cr596_proveedor": registro.proveedor,
            "cr596_comprobante": registro.comprobante,
            "cr596_monto": registro.monto,
            "cr596_metodopago": registro.metodo_pago,
            "cr596_observacion": registro.observacion
        }

        # Si el gasto viene de un viaje de Garita, lo vinculamos para apagar la alerta
        if registro.movimiento_id:
            payload_gasto["cr596_Movimiento@odata.bind"] = f"/cr596_flota_movimientos({registro.movimiento_id})"

        res_gasto = requests.post(endpoint_gasto, headers=headers, json=payload_gasto)
        if res_gasto.status_code != 204: raise HTTPException(status_code=res_gasto.status_code, detail=res_gasto.text)

        # Apagamos la alerta en Garita si existía
        if registro.movimiento_id:
            endpoint_mov = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_movimientos({registro.movimiento_id})"
            requests.patch(endpoint_mov, headers=headers, json={"cr596_reportagastos": False})

        return {"status": "success", "message": "Gasto registrado correctamente."}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/reporte-gastos")
def reporte_gastos(inicio: str, fin: str):
    try:
        token = get_token([f"{DATAVERSE_URL}/.default"])
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "Prefer": "odata.include-annotations=\"*\""}
        
        # Filtramos por fecha y expandimos para traer el nombre del vehículo
        endpoint = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_gastorutas?$filter=cr596_fecha ge {inicio} and cr596_fecha le {fin}&$expand=cr596_Vehiculo($select=cr596_nombre,cr596_placa)"
        
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200: 
            return {"status": "success", "data": response.json().get("value", [])}
        else: 
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/gastos-pendientes")
def listar_gastos_pendientes():
    token = get_token([f"{DATAVERSE_URL}/.default"])
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    endpoint = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_gastorutas?$filter=cr596_validacioncontable eq null or cr596_validacioncontable eq 144280000"
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200: return {"status": "success", "data": response.json().get("value", [])}
    else: raise HTTPException(status_code=response.status_code, detail=response.text)

@app.patch("/contabilizar-gasto")
def contabilizar_gasto(registro: RegistroContable):
    token = get_token([f"{DATAVERSE_URL}/.default"])
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    endpoint = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_gastorutas({registro.gasto_id})"
    payload = {"cr596_validacioncontable": registro.estado_validacion, "cr596_numerocomprobante": registro.numero_comprobante}
    if registro.cantidad_galones is not None and registro.cantidad_galones > 0: payload["cr596_cantidadgalones"] = registro.cantidad_galones
    requests.patch(endpoint, headers=headers, json=payload)
    return {"status": "success", "message": "Registro contable actualizado."}

# ==========================================
# ENDPOINTS DE MANTENIMIENTO / DASHBOARD
# ==========================================

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
    # --- NUEVOS CAMPOS ---
    modelo: Optional[str] = None
    ano: Optional[int] = None
    tipo: Optional[str] = None
    tipo_propiedad: Optional[int] = None # Es int porque recibe el código 14428...

@app.get("/estado-flota")
def estado_flota():
    token = get_token([f"{DATAVERSE_URL}/.default"])
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # 🚨 REVISA ESTA LISTA: Aquí deben estar las 4 columnas nuevas al final
    columnas = [
        "cr596_nombre", "cr596_placa", "cr596_estadooperativo", "cr596_kilometrajeactual",
        "cr596_vencimientosoat", "cr596_vencimientorevisiontecnica", "cr596_proximomantenimientokm", 
        "cr596_vencimientogps", "cr596_vencimientoseguro", "cr596_lunaspolarizadas",
        "cr596_nivelcombustible", "cr596_tipocombustible", 
        "cr596_ultimomantenimientokm", "cr596_frecuenciamantenimiento",
        "cr596_modelo", "cr596_ano", "cr596_tipo", "cr596_tipopropiedad" # <--- ¡ESTAS 4!
    ]
    
    endpoint = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_vehiculos?$select={','.join(columnas)}"
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        return {"status": "success", "data": response.json().get("value", [])}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


@app.patch("/actualizar-vehiculo")
def actualizar_vehiculo(datos: ActualizarVehiculo):
    try:
        token = get_token([f"{DATAVERSE_URL}/.default"])
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
        
        endpoint = f"{DATAVERSE_URL}/api/data/v9.2/cr596_flota_vehiculos({datos.vehiculo_id})"
        
        payload = {}
        if datos.estado_operativo is not None: payload["cr596_estadooperativo"] = datos.estado_operativo
        if datos.vencimiento_soat: payload["cr596_vencimientosoat"] = datos.vencimiento_soat
        if datos.vencimiento_rt: payload["cr596_vencimientorevisiontecnica"] = datos.vencimiento_rt
        if datos.vencimiento_gps: payload["cr596_vencimientogps"] = datos.vencimiento_gps
        if datos.vencimiento_seguro: payload["cr596_vencimientoseguro"] = datos.vencimiento_seguro
        if datos.lunas_polarizadas is not None: payload["cr596_lunaspolarizadas"] = datos.lunas_polarizadas
            # --- NUEVOS CAMPOS ---
        if datos.modelo is not None: payload["cr596_modelo"] = datos.modelo
        if datos.ano is not None: payload["cr596_ano"] = datos.ano
        if datos.tipo is not None: payload["cr596_tipo"] = datos.tipo
        if datos.tipo_propiedad is not None: payload["cr596_tipopropiedad"] = datos.tipo_propiedad
        
        # LÓGICA INTELIGENTE DE MANTENIMIENTO:
        if datos.ultimo_mantenimiento_km is not None: payload["cr596_ultimomantenimientokm"] = datos.ultimo_mantenimiento_km
        if datos.frecuencia_mantenimiento is not None: payload["cr596_frecuenciamantenimiento"] = datos.frecuencia_mantenimiento
        
        # Si vienen ambos datos, calculamos la próxima meta de mantenimiento automáticamente:
        if datos.ultimo_mantenimiento_km is not None and datos.frecuencia_mantenimiento is not None:
            payload["cr596_proximomantenimientokm"] = datos.ultimo_mantenimiento_km + datos.frecuencia_mantenimiento

        response = requests.patch(endpoint, headers=headers, json=payload)
        
        if response.status_code == 204:
            return {"status": "success", "message": "Datos actualizados."}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
