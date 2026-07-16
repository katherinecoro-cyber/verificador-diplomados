import streamlit as st
import pandas as pd
import unicodedata
from difflib import SequenceMatcher

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
    """Limpia el texto quitando tildes, mayúsculas y espacios innecesarios"""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    # Quitar tildes
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Quitar palabras vacías comunes para comparar mejor el núcleo del título
    palabras_a_quitar = ["en", "de", "y", "la", "el", "con", "para", "del", "los", "las"]
    palabras = [p for p in texto.split() if p not in palabras_a_quitar]
    return " ".join(palabras)

def calcular_similitud(texto1, texto2):
    """Calcula el porcentaje de similitud entre dos textos (de 0.0 a 1.0)"""
    t1 = limpiar_texto(texto1)
    t2 = limpiar_texto(texto2)
    
    # 1. Similitud por secuencia de caracteres (Levenshtein)
    similitud_base = SequenceMatcher(None, t1, t2).ratio()
    
    # 2. Similitud por intersección de palabras (por si cambian el orden de los factores)
    palabras1 = set(t1.split())
    palabras2 = set(t2.split())
    
    if not palabras1 or not palabras2:
        return similitud_base
        
    interseccion = palabras1.intersection(palabras2)
    similitud_palabras = len(interseccion) / max(len(palabras1), len(palabras2))
    
    # Promediamos ambas lógicas para un resultado más exacto
    return (similitud_base * 0.4) + (similitud_palabras * 0.6)

st.set_page_config(page_title="Verificador UPI", page_icon="🔍", layout="centered")

st.title("🔍 Verificador Inteligente de Diplomados")
st.write("Esta aplicación busca duplicados y **títulos similares** en tiempo real en todas las pestañas.")
st.markdown("---")

# Barra para que el usuario controle qué tan estricta es la IA (Por defecto 65%)
umbral_sensibilidad = st.slider(
    "Sensibilidad del detector de parecido (Recomendado: 65%)", 
    min_value=40, max_value=95, value=65, step=5,
    help="Un valor más bajo detectará parecidos más lejanos. Un valor más alto solo alertará si son casi idénticos."
)

nuevo_titulo = st.text_input("Escribe el nombre del nuevo diplomado a evaluar:")

if st.button("Verificar Propuesta", type="primary") and nuevo_titulo:
    coincidencias = []
    total_diplomados_cargados = 0
    umbral_decimal = umbral_sensibilidad / 100.0
    
    with st.spinner("Analizando similitud en toda la base de datos..."):
        for pestana in PESTANAS:
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestana.replace(' ', '%20')}"
            try:
                df = pd.read_csv(url)
                df.columns = df.columns.astype(str).str.strip().str.upper()
                
                # Identificar la columna de nombres
                columna_buscar = ""
                for col in df.columns:
                    if "NOMBRE DEL DIPLOMADO" in col or "NOMBRE DEL PROGRAMA" in col:
                        columna_buscar = col
                        break
                
                if columna_buscar:
                    for nombre in df[columna_buscar].dropna():
                        nombre_str = str(nombre).strip()
                        if not nombre_str or "N°" in nombre_str or "NOMBRE DEL" in nombre_str.upper():
                            continue
                        
                        total_diplomados_cargados += 1
                        
                        # Calcular porcentaje de parecido
                        porcentaje_parecido = calcular_similitud(nuevo_titulo, nombre_str)
                        
                        if porcentaje_parecido >= umbral_decimal:
                            coincidencias.append({
                                "nombre_existente": nombre_str,
                                "pestana": pestana,
                                "similitud": int(porcentaje_parecido * 100)
                            })
            except Exception as e:
                continue

    # Ordenar las coincidencias de mayor a menor parecido
    coincidencias = sorted(coincidencias, key=lambda x: x['similitud'], reverse=True)

    st.caption(f"📊 Diagnóstico: Se analizaron y compararon {total_diplomados_cargados} registros activos.")

    # Mostrar resultados basados en el parecido
    if coincidencias:
        # Si hay un parecido del 95% o más, es un rechazo directo e idéntico
        if coincidencias[0]['similitud'] >= 95:
            st.error(f"❌ **RECHAZADO**: Este diplomado ya existe exactamente en el sistema.")
        else:
            st.warning(f"⚠️ **ALERTA DE SIMILITUD**: Se encontraron programas muy parecidos que podrían duplicar la oferta académica.")
        
        # Mostrar la lista de sospechosos
        st.write("### Programas similares detectados:")
        for co in coincidencias[:3]: # Muestra los 3 parecidos más peligrosos
            st.info(
                f"• **{co['nombre_existente']}**\n"
                f"  - **Pestaña**: *'{co['pestana']}'*\n"
                f"  - **Nivel de parecido**: `{co['similitud']}%`"
            )
    else:
        st.success("✅ **APROBADO**: El título es original y no tiene conflicto con la oferta actual.")
