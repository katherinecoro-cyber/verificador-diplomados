import streamlit as st
import pandas as pd
import unicodedata
import re

# Configuración automática con tu ID de Google Sheets
SPREADSHEET_ID = "1eySPD9wEzs_D1vAXhOqmh3BXoRxCfK7A" 

PESTANAS = [
    'DIP. INACTIVOS', 'DIP. DE BAJA', 'DIPLOMADOS JULIO- AGOSTO -SEPT', 
    'DIPLOMADOS SEPTIEMBRE - OCTUBRE', 'DIPLOMADOS OCTUBRE - NOVIEMBRE', 
    'DIPLOMADOS NOVIEMBRE - DICIEMBR', 'DIPLOMADOS DICIEMBRE', 
    'DIPLOMADOS MERCADO BOLIVIANO', 'DIPLOMADOS DOBLE CERTIFICACIÓN', 
    'DIPLOMADOS ENERO 2026', 'DIPLOMADOS FEBRERO 2026', 
    'DIPLOMADOS MARZO 2026', 'DIPLOMADOS ABRIL 2026', 
    'DIPLOMADOS MAYO 2026', 'DIPLOMADOS JUNIO 2026', 
    'DIPLOMADOS JULIO 2026', 'DIPLOMADOS - AGOSTO...'
]

def tokenizar_y_limpiar(texto):
    """Limpia el texto, quita acentos, conectores y extrae las palabras clave reales"""
    if pd.isna(texto):
        return set()
    texto = str(texto).lower()
    # Quitar acentos/tildes
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Dejar solo letras y números
    palabras = re.findall(r'[a-z0-9ñ]+', texto)
    
    # Filtro de conectores que no aportan significado académico
    conectores = {
        'en', 'de', 'y', 'la', 'el', 'con', 'para', 'del', 'los', 'las', 'un', 'una', 
        'diplomado', 'curso', 'programa', 'gestion', 'aplicada', 'avanzado', 'especialidad'
    }
    return {p for p in palabras if p not in conectores and len(p) > 2}

def calcular_similitud_semantica(set_nuevo, set_existente):
    """Calcula el porcentaje de coincidencia basado en las palabras clave centrales"""
    if not set_nuevo or not set_existente:
        return 0.0
    interseccion = set_nuevo.intersection(set_existente)
    # Compara qué tanto del nuevo título ya está cubierto por el viejo
    return len(interseccion) / len(set_nuevo)

st.set_page_config(page_title="Verificador UPI", page_icon="🔍", layout="centered")

st.title("🔍 Verificador Inteligente por Coincidencia Semántica")
st.write("El sistema analiza y cruza las palabras clave esenciales para evitar duplicados en la oferta académica.")
st.markdown("---")

nuevo_titulo = st.text_input("Escribe el nombre del nuevo diplomado a evaluar:")

if st.button("Verificar Propuesta", type="primary") and nuevo_titulo:
    todos_los_diplomados = []
    total_registros = 0
    
    with st.spinner("Cargando y procesando base de datos de Google Sheets..."):
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
                            todos_los_diplomados.append({
                                "nombre_original": n_str,
                                "tokens": tokenizar_y_limpiar(n_str),
                                "pestana": pestana
                            })
                            total_registros += 1
            except:
                continue

    st.caption(f"📊 Base de datos: {total_registros} diplomados analizados en vivo.")

    # Analizar similitudes
    tokens_nuevos = tokenizar_y_limpiar(nuevo_titulo)
    coincidencias_peligrosas = []
    
    for item in todos_los_diplomados:
        # Validación 1: Copia exacta directa
        if nuevo_titulo.strip().upper() == item["nombre_original"].upper():
            coincidencias_peligrosas.append({**item, "porcentaje": 100})
            continue
            
        # Validación 2: Similitud por núcleo de palabras clave
        porcentaje = calcular_similitud_semantica(tokens_nuevos, item["tokens"])
        if porcentaje >= 0.60: # Si comparte el 60% o más de los conceptos core, alerta.
            coincidencias_peligrosas.append({**item, "porcentaje": int(porcentaje * 100)})

    # Mostrar Resultados
    if coincidencias_peligrosas:
        # Ordenar las peores primero
        coincidencias_peligrosas = sorted(coincidencias_peligrosas, key=lambda x: x['porcentaje'], reverse=True)
        peor_caso = coincidencias_peligrosas[0]
        
        st.error(f"❌ **RECHAZADO / ALERTA DE DUPLICIDAD**")
        st.warning(f"Se detectó un conflicto conceptual severo con programas existentes en el sistema.")
        
        st.write("### Programas similares en conflicto encontrados:")
        # Mostrar los 3 parecidos más críticos
        for c in coincidencias_peligrosas[:3]:
            st.info(
                f"📌 **{c['nombre_original']}**\n\n"
                f"📂 **Ubicación**: Pestaña *'{c['pestana']}'*\n"
                f"📊 **Nivel de coincidencia en conceptos**: `{c['porcentaje']}%`"
            )
    else:
        st.success("✅ **APROBADO**: La propuesta contiene un enfoque de palabras clave original y no duplica la oferta actual.")
