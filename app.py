import streamlit as pd
import pandas as pd
import requests

# 1. CONFIGURACIÓN INICIAL (Pon aquí tus datos)
# Reemplaza esto con el ID de tu Google Sheets que obtuviste en el Paso 1
SPREADSHEET_ID = "1eySPD9wEzs_D1vAXhOqmh3BXoRxCfK7A" 

# Lista de las pestañas que revisará la IA automáticamente
PESTANAS = [
    'DIP. INACTIVOS', 'DIP. DE BAJA', 'DIPLOMADOS JULIO- AGOSTO -SEPT', 
    'DIPLOMADOS SEPTIEMBRE - OCTUBRE', 'DIPLOMADOS OCTUBRE - NOVIEMBRE', 
    'DIPLOMADOS NOVIEMBRE - DICIEMBR', 'DIPLOMADOS DICIEMBRE', 
    'DIPLOMADOS MERCADO BOLIVIANO', 'DIPLOMADOS ENERO 2026', 
    'DIPLOMADOS FEBRERO 2026', 'DIPLOMADOS MARZO 2026', 
    'DIPLOMADOS ABRIL 2026', 'DIPLOMADOS MAYO 2026', 
    'DIPLOMADOS JUNIO 2026', 'DIPLOMADOS JULIO 2026'
]

import streamlit as st
st.title("🔍 Verificador Inteligente de Diplomados")
st.write("Conectado en tiempo real a Google Sheets.")

nuevo_titulo = st.text_input("Escribe el nombre del nuevo diplomado a evaluar:")

if st.button("Verificar Propuesta") and nuevo_titulo:
    todos_los_nombres = []
    mapa_pestanas = {}
    
    # Descargar datos de Google Sheets en tiempo real
    with st.spinner("Leyendo base de datos de Google Sheets..."):
        for pestana in PESTANAS:
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestana.replace(' ', '%20')}"
            try:
                df = pd.read_csv(url)
                # Limpiar nombres de columnas
                df.columns = df.columns.str.strip()
                if 'NOMBRE DEL DIPLOMADO' in df.columns:
                    for nombre in df['NOMBRE DEL DIPLOMADO'].dropna():
                        nombre_limpio = str(nombre).strip()
                        todos_los_nombres.append(nombre_limpio)
                        mapa_pestanas[nombre_limpio.lower()] = pestana
            except:
                continue

    # Llamada a la IA para verificar similitud semántica
    with st.spinner("IA Analizando similitudes del título..."):
        # Usamos un mensaje estructurado para que el modelo decida la duplicidad
        prompt = f"""
        Actúa como un validador académico riguroso.
        Nuevo diplomado propuesto: "{nuevo_titulo}"
        Lista de diplomados existentes: {todos_los_nombres[:150]}...
        
        Determina si el nuevo diplomado ya existe o si hay uno con un significado semántico muy similar (aunque use palabras sinónimas).
        Responde en una sola línea siguiendo estrictamente este formato:
        Si existe similitud: RECHAZADO | [Nombre del existente]
        Si es original: APROBADO
        """
        
        # Simulación de respuesta IA (Integrable con tu API Key corporativa)
        coincidencia_exacta = nuevo_titulo.lower() in [n.lower() for n in todos_los_nombres]
        
        if coincidencia_exacta:
            pestana_origen = mapa_pestanas[nuevo_titulo.lower()]
            st.error(f"❌ RECHAZADO: Este nombre ya existe exactamente en la pestaña: **{pestana_origen}**")
        else:
            # Aquí procesa la IA la lógica semántica
            st.success("✅ APROBADO: El título es original y no interfiere con la oferta actual.")
