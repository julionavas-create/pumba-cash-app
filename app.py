import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Pumba Cash App", page_icon="🐗", layout="centered")

# --- CONSTANTES ---
# En la nube no usamos rutas C:\Users... usamos rutas relativas
ARCHIVO_CSV = "mis_finanzas_web.csv"

# --- FUNCIONES DE BACKEND ---
def inicializar_archivo():
    if not os.path.exists(ARCHIVO_CSV):
        df = pd.DataFrame(columns=["Fecha", "Tipo", "Categoria", "Monto", "Tasa", "Nota"])
        df.to_csv(ARCHIVO_CSV, index=False)

def cargar_datos():
    if os.path.exists(ARCHIVO_CSV):
        return pd.read_csv(ARCHIVO_CSV)
    return pd.DataFrame(columns=["Fecha", "Tipo", "Categoria", "Monto", "Tasa", "Nota"])

def guardar_registro(tipo, categoria, monto, tasa, nota):
    if monto <= 0:
        st.error("⚠️ El monto debe ser mayor a 0")
        return

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_dato = {
        "Fecha": fecha,
        "Tipo": tipo,
        "Categoria": categoria,
        "Monto": monto,
        "Tasa": tasa,
        "Nota": nota
    }
    
    # Guardar en CSV
    df = cargar_datos()
    df = pd.concat([df, pd.DataFrame([nuevo_dato])], ignore_index=True)
    df.to_csv(ARCHIVO_CSV, index=False)
    
    # Mensaje de éxito
    if tipo == "Ingreso":
        st.success(f"✅ Ingreso registrado: {categoria} (${monto})")
    elif tipo == "Gasto":
        st.warning(f"📉 Gasto registrado: {categoria} (-${monto})")
    else:
        st.info(f"🐷 Ahorro registrado: {categoria} (${monto})")

# --- INICIO DEL PROGRAMA ---
inicializar_archivo()

# --- HEADER (Imagen y Título) ---
col_img, col_title = st.columns([1, 4])
with col_img:
    # Si tienes la imagen en la misma carpeta, descomenta la siguiente línea:
    # st.image("pumba.PNG", width=80) 
    st.write("🐗") # Emoji temporal si no hay imagen
with col_title:
    st.title("Pumba Cash Web")

# --- PANEL DE RESUMEN (DASHBOARD) ---
df = cargar_datos()
if not df.empty:
    total_ingresos = df[df["Tipo"] == "Ingreso"]["Monto"].sum()
    total_gastos = df[df["Tipo"] == "Gasto"]["Monto"].sum()
    total_ahorros = df[df["Tipo"].isin(["Ahorro", "Inversion"])]["Monto"].sum() # Tratamos inversión como ahorro/activo
    disponible = total_ingresos - total_gastos - total_ahorros

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Ingresos", f"${total_ingresos:,.2f}")
    c2.metric("💸 Gastos", f"${total_gastos:,.2f}")
    c3.metric("🐷 Ahorros/Inv", f"${total_ahorros:,.2f}")
    
    st.info(f"💰 **DISPONIBLE EN MANO:** ${disponible:,.2f}")
else:
    st.info("👋 Bienvenido. Empieza a registrar tus movimientos.")

st.markdown("---")

# --- INPUTS (ENTRADAS) ---
st.subheader("📝 Nuevo Registro")

c_input1, c_input2 = st.columns(2)
with c_input1:
    monto = st.number_input("Monto ($)", min_value=0.0, step=1.0, format="%.2f")
with c_input2:
    tasa = st.number_input("Tasa (Bs)", min_value=0.0, step=0.1, format="%.2f")

nota = st.text_input("Nota (Opcional)")

# --- BOTONES DE ACCIÓN ---
st.write("Selecciona la categoría para guardar:")

# Fila 1
b1, b2 = st.columns(2)
if b1.button("⛽ Gasolina"): guardar_registro("Gasto", "Gasolina", monto, tasa, nota)
if b2.button("🚗 Mant. Carro"): guardar_registro("Gasto", "Carro Repuestos", monto, tasa, nota)

# Fila 2
b3, b4 = st.columns(2)
if b3.button("🏍️ Gastos Moto"): guardar_registro("Gasto", "Moto Repuestos", monto, tasa, nota)
if b4.button("🛍️ Pago Cashea"): guardar_registro("Gasto", "Cashea", monto, tasa, nota)

# Fila 3
b5, b6 = st.columns(2)
if b5.button("🍔 Comida"): guardar_registro("Gasto", "Comida", monto, tasa, nota)
if b6.button("🍻 Salidas"): guardar_registro("Gasto", "Entretenimiento", monto, tasa, nota)

# Fila 4
b7, b8 = st.columns(2)
if b7.button("💳 Créditos"): guardar_registro("Gasto", "Créditos", monto, tasa, nota)
if b8.button("💼 Inversión Ofic."): guardar_registro("Inversion", "Oficina", monto, tasa, nota)

# Fila 5
b9, b10 = st.columns(2)
if b9.button("💊 Salud"): guardar_registro("Gasto", "Salud", monto, tasa, nota)
if b10.button("🔧 Otros Vehículo"): guardar_registro("Gasto", "Vehículo General", monto, tasa, nota)

st.markdown("#### 💱 Divisas y Capital")
d1, d2 = st.columns(2)
if d1.button("📉 Venta Divisas (Salida)"): guardar_registro("Gasto", "Venta Divisas", monto, tasa, nota)
if d2.button("📈 Compra Divisas (Ahorro)"): guardar_registro("Ahorro", "Compra Divisas", monto, tasa, nota)

k1, k2 = st.columns(2)
if k1.button("💵 Ingreso Quincena"): guardar_registro("Ingreso", "Salario", monto, tasa, nota)
if k2.button("🐷 Otros Ahorros"): guardar_registro("Ahorro", "Fondo Ahorro", monto, tasa, nota)

# --- HISTORIAL ---
st.markdown("---")
with st.expander("📜 Ver Historial Completo"):
    if not df.empty:
        # Calculamos el total en Bs para mostrarlo
        df["Total Bs"] = df["Monto"] * df["Tasa"]
        # Ordenamos descendente para ver lo último primero
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.text("No hay datos aún.")
