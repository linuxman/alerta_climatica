import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# -- Carga de parámetros
# OpenWeatherMap
CITY = os.getenv("CITY")
API_KEY = os.getenv("API_KEY")
LAT = os.getenv("LAT")
LON = os.getenv("LON")
UNITS = os.getenv("UNITS")
LANG = os.getenv("LANG")
# Telegram
CHAT_ID = os.getenv("CHAT_ID")
TOKEN = os.getenv("TOKEN")

# Umbrales para alertas futuras (ajusta según tu región)
# ajustando estos valores para falsas alarmas.
# Para revisar las unidades de los valores:
# https://openweathermap.org/weather-data

# La velocidad del viento de la API esta en m/s
# Para convertir km/h a m/s multiplicar por 0.2778

ALERT_THRESHOLDS = {
    "temp_min": 0,            # Temperatura mínima (°C)
    "temp_max": 40,           # Temperatura máxima (°C)
    "precipitation": 20,      # Lluvia acumulada (mm en 3h)
    "wind_speed_mod": 20,     # Vientos moderados - 20 km/s aprox
    "wind_speed_alert":40,    # Vientos fuertes, mayores de 40 km/h
    "visibility_alert":1000   # Visibilidad reducida a 1000 m
}

def ms2km(ms):
    # Convierte m/s a km/h
    return round(ms/0.2778,2)

def obtener_prediccion():
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&units={UNITS}&lang={LANG}&appid={API_KEY}"
    response = requests.get(url)
    return response.json()

def analizar_pronostico(data):
    alertas = []
    ahora = datetime.now()

    for entry in data["list"]:
        # Calcular diferencia de tiempo
        fecha_prediccion = datetime.fromtimestamp(entry["dt"])
        diferencia = fecha_prediccion - ahora

        # Solo considerar próximas 24-120 horas
        if timedelta(hours=24) <= diferencia <= timedelta(hours=120):
            temp = entry["main"]["temp"]
            lluvia = entry.get("rain", {}).get("3h", 0)
            # Para mayor claridad, convertí los m/s a km/h
            viento = ms2km(entry["wind"]["speed"])
            visibilidad = entry["visibility"]
            # humedad = entry["main"]["humidity"]
            clima = entry["weather"][0]["description"]

            # Verificar umbrales
            if temp <= ALERT_THRESHOLDS["temp_min"]:
                alertas.append(f"Temperatura BAJA ({temp}°C) el {fecha_prediccion.strftime('%d/%m %H:%M')}")
            elif temp >= ALERT_THRESHOLDS["temp_max"]:
                alertas.append(f"Temperatura ALTA ({temp}°C) el {fecha_prediccion.strftime('%d/%m %H:%M')}")

            if lluvia >= ALERT_THRESHOLDS["precipitation"]:
                alertas.append(f"Lluvia SEVERA ({lluvia} mm/3h) el {fecha_prediccion.strftime('%d/%m %H:%M')}")

            if viento >= ALERT_THRESHOLDS["wind_speed_mod"] and viento <= ALERT_THRESHOLDS["wind_speed_alert"]:
                alertas.append(f"Vientos moderados (viento: {viento} km/h) el {fecha_prediccion.strftime('%d/%m %H:%M')}")

            if viento >= ALERT_THRESHOLDS["wind_speed_alert"]:
                alertas.append(f"Vientos fuertes (viento: {viento} km/h) el {fecha_prediccion.strftime('%d/%m %H:%M')}")

            if visibilidad <= ALERT_THRESHOLDS["visibility_alert"]:
                alertas.append(f"Visibilidad reducida (niebla, tolvaneras) (visibilidad: {visibilidad} m) el {fecha_prediccion.strftime('%d/%m %H:%M')}")

    return alertas

def enviar_alerta(mensaje):
    # Manda notificación al canal de telegram
    url = "https://api.telegram.org/bot" + TOKEN + "/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': mensaje,
        'parse_mode':"Markdown"
    }
    print(mensaje)
    requests.post(url, params=params)

if __name__ == "__main__":
    datos = obtener_prediccion()
    alertas = analizar_pronostico(datos)
    print("⛅ análisis terminado.")

    if alertas:
        mensaje = f"⚠ Alertas para *{CITY}* (próximas 24-120 h):\n" + "\n".join(alertas)
        enviar_alerta(mensaje)
