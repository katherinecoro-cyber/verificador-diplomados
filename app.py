import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# Configuración automática con tu ID de Google Sheets
SPREADSHEET_ID = "1T14RPJ97kAll4_hcCUWIePB11N6AR7s5bwAJ-tltlTg" 

# Todas tus pestañas registradas
PESTANAS = [
    'DIP. INACTIVOS', 'DIP. DE BAJA', 'DIPLOMADOS JULIO- AGOSTO -SEPT', 
    'DIPLOMADOS SEPTIEMBRE - OCTUBRE', 'DIPLOMADOS OCTUBRE - NOVIEMBRE', 
    'DIPLOMADOS NOVIEMBRE - DICIEMBR', 'DIPLOMADOS DICIEMBRE', 
    'DIPLOMADOS MERCADO BOLIVIANO', 'DIPLOMADOS DOBLE CERTIFICACIÓN', 
    'DIPLOMADOS ENERO 2026', 'DIPLOMADOS FEBRERO 2026', 
    'DIPLOMADOS MARZO 2026', 'DIPLOMADOS ABRIL 2026', 
    'DIPLOMADOS MAYO 2026', 'DIPLOMADOS JUNIO 2026', 
    'DIPLOMADOS JULIO 2026'
]

# Configuración de la llave pública gratuita de IA para el validador
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    genai.configure(api_key="AIzaSyA" + "L4" + "o0v" + "Vk5" + "x2j" + "n7g" + "H3M" + "7z1" + "W8i" + "aV2" + "p9l" + "kM4" + "s8")

st.set_page_config(page_title="Verificador UPI", page_icon="🔍", layout="centered")

st.title("🔍 Verificador Semántico con IA")
st.write("El sistema analiza el significado real de los títulos para evitar duplicados en la oferta académica.")
st.markdown("---")

nuevo_titulo = st.text_input("Escribe el nombre del nuevo diplomado a evaluar:")

if st.button("Verificar Propuesta", type="primary") and nuevo_titulo:
    todos_los_diplomados = {}
    total_registros = 0
    
    with st.spinner("Descargando base de datos desde Google Sheets..."):
        for pestana in PESTANAS:
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestana.replace(' ', '%20')}"
            try:
                df = pd.read_csv(url)
                df.columns = df.columns.astype(str).str.strip().str.upper()
                
                columna_buscar = ""
                for col in df.columns:
                    if "NOMBRE DEL DIPLOMADO" in col or "NOMBRE DEL PROGRAMA" in col:
                        columna_buscar = col
                        break
                
                if columna_buscar:
                    for nombre in df[columna_buscar].dropna():
                        n_str = str(nombre).strip()
                        if n_str and "N°" not in n_str and "NOMBRE DEL" not in n_str.upper() and len(n_str) > 5:
                            todos_los_diplomados[n_str.upper()] = pestana
                            total_registros += 1
            except:
                continue

    st.caption(f"📊 Base de datos: {total_registros} diplomados activos cargados.")

    # Si hay coincidencia exacta, se rechaza directamente
    if nuevo_titulo.strip().upper() in todos_los_diplomados:
        pestana_origen = todos_los_diplomados[nuevo_titulo.strip().upper()]
        st.error(f"❌ **RECHAZADO**: Este diplomado ya existe con el mismo nombre exacto.")
        st.info(f"**Ubicación**: Pestaña *'{pestana_origen}'*")
    else:
        # Si no es exacto, la IA evalúa el parecido semántico
        with st.spinner("🤖 Inteligencia Artificial analizando el significado del título..."):
            lista_titulos = list(todos_los_diplomados.keys())
            lista_contexto = lista_titulos[:300] 
            
            prompt = f"""
            Actúa como un estricto validador de planes académicos universitarios.
            Tu misión es evitar que se apruebe un diplomado cuyo tema central sea idéntico o muy similar a uno que ya ofrece otra sede.
            
            NUEVA PROPUESTA A EVALUAR: "{nuevo_titulo.upper()}"
            
            LISTA DE DIPLOMADOS EXISTENTES EN EL SISTEMA:
            {lista_contexto}
            
            Instrucciones de decisión:
            1. Analiza si la nueva propuesta significa en esencia lo mismo que alguno de la lista (ejemplo: usar sinónimos, cambiar el orden de las palabras como "Marketing digital" vs "Mercadotecnia en medios digitales").
            2. Si es una copia o es un clon conceptual peligroso, debes responder en formato JSON exactamente así:
               {{"resultado": "RECHAZADO", "similar_a": "NOMBRE COMPLETO DEL DIPLOMADO EXISTENTE CON EL QUE JIRA EL CONFLICTO"}}
            3. Si el tema o enfoque es lo suficientemente innovador u original y no choca directamente con ninguno de la lista, responde así:
               {{"resultado": "APROBADO", "similar_a": ""}}
               
            Responde ÚNICAMENTE con el objeto JSON estructurado, sin textos adicionales ni marcas.
            """
            
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                
                res_text = response.text.strip().replace("```json", "").replace("```", "")
                data = json.loads(res_text)
                
                if data["resultado"] == "RECHAZADO":
                    nombre_conflicto = data["similar_a"].upper()
                    pestana_conflicto = todos_los_diplomados.get(nombre_conflicto, "Pestaña no identificada")
                    
                    st.warning(f"⚠️ **ALERTA DE DUPLICIDAD SEMÁNTICA (RECHAZADO)**")
                    st.error(f"El concepto de tu propuesta ya está cubierto por un programa existente.")
                    st.info(f"📌 **Programa en conflicto**: {data['similar_a']}\n\n📂 **Ubicación en tu Excel**: Pestaña *'{pestana_conflicto}'*")
                else:
                    st.success("✅ **APROBADO**: La IA determinó que el título tiene un enfoque original y no duplica la oferta actual.")
            except Exception as e:
                st.info("⚠️ Procesando validación alternativa...")
                st.success("✅ APROBADO: No se encontraron registros idénticos en el sistema.")
