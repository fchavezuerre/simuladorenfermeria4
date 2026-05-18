import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF

# Configuración de página
st.set_page_config(page_title="App Enfermería", layout="centered")

def run_query(query, params=()):
    with sqlite3.connect('pdae.db') as conn:
        return pd.read_sql_query(query, conn, params=params)

def formatear_como_lista(texto):
    if not texto: return "Sin datos"
    items = [item.strip() for item in texto.split(';') if item.strip()]
    return items

# --- NUEVA FUNCIÓN PARA GENERAR PDF ---
def crear_pdf(diagnostico, fila):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Plan de Cuidado: {diagnostico}", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"ID del Plan: {fila['id']}", ln=True, align="R")
    pdf.ln(5)

    secciones = [
        ("Valoracion", fila['valoracion_signos_sintomas']),
        ("Diagnostico de Enfermeria", fila['diagnostico_enfermeria']),
        ("Intervenciones", fila['intervenciones_colaboracion']),
        ("Evolucion", fila['respuesta_evolucion'])
    ]

    for titulo, contenido in secciones:
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 8, titulo.upper(), ln=True, fill=True)
        pdf.set_font("Arial", "", 10)
        items = [item.strip() for item in contenido.split(';') if item.strip()]
        for item in items:
            pdf.multi_cell(0, 5, f"- {item}")
        pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin-1')

st.title("🏥 Planes de Cuidado")

search_term = st.text_input("🔍 Buscar diagnóstico:", placeholder="Ej: Diabetes...")

id_dx_final = None
dx_nombre_final = ""

try:
    if search_term:
        df_res = run_query("SELECT id, nombre FROM diagnosticos_medicos WHERE nombre LIKE ?", (f"%{search_term}%",))
        if not df_res.empty:
            opciones_busqueda = {row['nombre']: row['id'] for _, row in df_res.iterrows()}
            dx_nombre_final = st.selectbox("Resultados:", options=list(opciones_busqueda.keys()))
            id_dx_final = opciones_busqueda[dx_nombre_final]
    else:
        df_div = run_query("SELECT * FROM divisiones")
        opciones_div = {row['nombre']: row['id'] for _, row in df_div.iterrows()}
        div_nombre = st.selectbox("📌 Selecciona División:", options=list(opciones_div.keys()))
        df_dx = run_query("SELECT id, nombre FROM diagnosticos_medicos WHERE divison_id = ?", (opciones_div[div_nombre],))
        if not df_dx.empty:
            opciones_dx = {row['nombre']: row['id'] for _, row in df_dx.iterrows()}
            dx_nombre_final = st.selectbox("🔎 Selecciona Diagnóstico:", options=list(opciones_dx.keys()))
            id_dx_final = opciones_dx[dx_nombre_final]

    if id_dx_final:
        df_planes = run_query("SELECT * FROM planes_cuidado WHERE id_dx = ?", (id_dx_final,))
        for _, fila in df_planes.iterrows():
            with st.expander(f"📄 PLAN ID: {fila['id']}"):
                # Mostrar en pantalla
                st.markdown("#### 📋 Valoración")
                st.write("\n".join([f"* {i}" for i in formatear_como_lista(fila['valoracion_signos_sintomas'])]))
                st.info(f"**PROBLEMA:** \n" + "\n".join([f"* {i}" for i in formatear_como_lista(fila['problema_interdependiente'])]))
                st.info(f"**Diagnóstico:** \n" + "\n".join([f"* {i}" for i in formatear_como_lista(fila['diagnostico_enfermeria'])]))
                st.info(f"**ACTIVIDAD DE ENFERMERIA:** \n" + "\n".join([f"* {i}" for i in formatear_como_lista(fila['actividad_enfermeria'])]))
                st.info(f"**RESPUESTA:** \n" + "\n".join([f"* {i}" for i in formatear_como_lista(fila['respuesta_evolucion'])]))
                # Botón de Descarga PDF
                
                pdf_bytes = crear_pdf(dx_nombre_final, fila)
                st.download_button(
                    label="📥 Descargar PDF para WhatsApp",
                    data=pdf_bytes,
                    file_name=f"Plan_{fila['id']}.pdf",
                    mime="application/pdf"
                )

except Exception as e:
    st.error(f"Error: {e}")
