import streamlit as st
import pandas as pd
import unicodedata

# Configuración automática con tu ID de Google Sheets
SPREADSHEET_ID = "1eySPD9wEzs_D1vAXhOqmh3BXoRxCfK7A" 

# Listado de pestañas a verificar
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

def limpiar_texto(texto):
    """Elimina espacios, tildes y lo pasa a minúsculas para una comparación perfecta"""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    # Eliminar acentos/tildes
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

st.set_page_config(page_title="Verificador UPI", page_icon="🔍", layout="centered")

st.title("🔍 Verificador Inteligente de Diplomados")
st.write("Esta aplicación busca duplicados en tiempo real en todas las pestañas de tu Google Sheets.")
st.markdown("---")

nuevo_titulo = st.text_input("Escribe el nombre del nuevo diplomado a evaluar:")

if st.button("Verificar Propuesta", type="primary") and nuevo_titulo:
    nuevo_titulo_clean = limpiar_texto(nuevo_titulo)
    encontrado = False
    pestana_encontrada = ""
    nombre_exacto = ""
    total_diplomados_cargados = 0
    
    with st.spinner("Buscando en todas las pestañas de Google Sheets..."):
        for pestana in PESTANAS:
            # Formatear la URL para descargar la pestaña como CSV público
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestana.replace(' ', '%20')}"
            try:
                df = pd.read_csv(url)
                # Limpiar los nombres de las columnas (quitar espacios y pasarlo a mayúsculas para buscar)
                df.columns = df.columns.astype(str).str.strip().str.upper()
                
                # Identificar la columna de nombres de diplomados
                columna_buscar = ""
                for col in df.columns:
                    if "NOMBRE DEL DIPLOMADO" in col or "NOMBRE DEL PROGRAMA" in col:
                        columna_buscar = col
                        break
                
                if columna_buscar:
                    for nombre in df[columna_buscar].dropna():
                        total_diplomados_cargados += 1
                        if limpiar_texto(nombre) == nuevo_titulo_clean:
                            encontrado = True
                            pestana_encontrada = pestana
                            nombre_exacto = str(nombre).strip()
                            break
            except Exception as e:
                continue
            if encontrado:
                break

    # Imprimir diagnóstico en la pantalla para saber si leyó los datos
    st.caption(f"📊 Diagnóstico: Se revisaron {total_diplomados_cargados} registros en total a lo largo de las pestañas.")

    # Mostrar resultados en pantalla
    if encontrado:
        st.error(f"❌ **RECHAZADO**: Este diplomado ya existe en el sistema.")
        st.info(f"**Nombre registrado**: {nombre_exacto}\n\n**Ubicación**: Pestaña *'{pestana_encontrada}'*")
    else:
        st.success("✅ **APROBADO**: El título es original y no se encuentra registrado en ninguna pestaña actual.")
