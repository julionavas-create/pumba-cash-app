import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
import base64

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Pumba Cash App", page_icon="🐗", layout="centered")

# --- CONFIGURACIÓN DE GITHUB ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
GITHUB_BRANCH = st.secrets["GITHUB_BRANCH"]
CSV_FILE = st.secrets["CSV_FILE"]

# --- FUNCIONES DE BACKEND CON GITHUB ---
@st.cache_resource
def get_github_repo():
    """Inicializa conexión con GitHub (se cachea para no repetir)"""
    g = Github(GITHUB_TOKEN)
    return g.get_repo(GITHUB_REPO)

def leer_csv_desde_github():
    """Lee el archivo CSV desde GitHub"""
    try:
        repo = get_github_repo()
        file_content = repo.get_contents(CSV_FILE, ref=GITHUB_BRANCH)
        csv_data = base64.b64decode(file_content.content).decode('utf-8')
        
        # Convertir CSV string a DataFrame
        from io import StringIO
        df = pd.read_csv(StringIO(csv_data))
        return df, file_content.sha
    except Exception as e:
        # Si el archivo no existe o hay error, retornamos DataFrame vacío
        st.warning(f"Leyendo archivo desde GitHub... {str(e)}")
        return pd.DataFrame(columns=["Fecha", "Tipo", "Categoria", "Monto", "Tasa", "Nota"]), None

def guardar_csv_en_github(df, sha=None):
    """Guarda el DataFrame en GitHub"""
    try:
        repo = get_github_repo()
        
        # Convertir DataFrame a CSV string
        csv_content = df.to_csv(index=False)
        
        # Actualizar o crear el archivo en GitHub
        if sha:
            # Actualizar archivo existente
            repo.update_file(
                path=CSV_FILE,
                message=f"Actualizar registros - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=csv_content,
                sha=sha,
                branch=GITHUB_BRANCH
            )
        else:
            # Crear archivo nuevo
            repo.create_file(
                path=CSV_FILE,
                message=f"Crear archivo de registros - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=csv_content,
                branch=GITHUB_BRANCH
            )
        return True
    except Exception as e:
        st.error(f"Error al guardar en GitHub: {str(e)}")
        return False

def cargar_datos():
    """Carga datos desde GitHub"""
    df, _ = leer_csv_desde_github()
    return df

def guardar_registro(tipo, categoria, monto, tasa, nota):
    """Guarda un nuevo registro en GitHub"""
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
    
    # Cargar datos actuales desde GitHub
    df, sha = leer_csv_desde_github()
    
    # Agregar nuevo registro
    df = pd.concat([df, pd.DataFrame([nuevo_dato])], ignore_index=True)
    
    # Guardar en GitHub
    if guardar_csv_en_github(df, sha):
        # Mensaje de éxito
        if tipo == "Ingreso":
            st.success(f"✅ Ingreso registrado: {categoria} (${monto})")
        elif tipo == "Gasto":
            st.warning(f"📉 Gasto registrado: {categoria} (-${monto})")
        else:
            st.info(f"🐷 Ahorro registrado: {categoria} (${monto})")
        
        # Limpiar cache para recargar datos
        st.cache_resource.clear()
        st.rerun()
    else:
        st.error("❌ Error al guardar el registro")

# --- HEADER (Imagen y Título) ---
col_img, col_title = st.columns([1, 4])
with col_img:
    try:
        st.image("pumba.png", width=80)
    except:
        st.write("🐗")
with col_title:
    st.title("Pumba Cash Web")

# --- PANEL DE RESUMEN (DASHBOARD) ---
df = cargar_datos()
if not df.empty:
    total_ingresos = df[df["Tipo"] == "Ingreso"]["Monto"].sum()
    total_gastos = df[df["Tipo"] == "Gasto"]["Monto"].sum()
    total_ahorros = df[df["Tipo"].isin(["Ahorro", "Inversion"])]["Monto"].sum()
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
