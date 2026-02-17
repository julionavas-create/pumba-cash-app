import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from supabase import create_client, Client

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Pumba Cash App", page_icon="🐗", layout="centered")

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# --- INICIALIZAR CONEXIÓN CON SUPABASE ---
@st.cache_resource
def get_supabase_client():
    """Inicializa conexión con Supabase (se cachea para no repetir)"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# --- FUNCIONES DE AUTENTICACIÓN ---
def login_user(email, password):
    """Inicia sesión de usuario"""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        return None

def register_user(email, password):
    """Registra un nuevo usuario"""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except Exception as e:
        return None

def logout_user():
    """Cierra sesión del usuario"""
    st.session_state.clear()
    st.rerun()

# --- FUNCIONES DE BACKEND CON SUPABASE ---
def cargar_datos(user_id):
    """Carga datos desde Supabase para el usuario autenticado"""
    try:
        response = supabase.table("movimientos").select("*").eq("user_id", user_id).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Renombrar columnas
            if 'fecha' in df.columns:
                df.rename(columns={
                    'fecha': 'Fecha',
                    'tipo': 'Tipo',
                    'categoria': 'Categoria',
                    'monto': 'Monto',
                    'tasa': 'Tasa',
                    'descripcion': 'Nota'
                }, inplace=True)
            return df
        else:
            return pd.DataFrame(columns=["Fecha", "Tipo", "Categoria", "Monto", "Tasa", "Nota"])
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return pd.DataFrame(columns=["Fecha", "Tipo", "Categoria", "Monto", "Tasa", "Nota"])

def guardar_registro(tipo, categoria, monto, tasa, nota, user_id):
    """Guarda un nuevo registro en Supabase"""
    if monto <= 0:
        st.error("⚠️ El monto debe ser mayor a 0")
        return

        # Verificar si ya existe un registro duplicado reciente (últimos 5 segundos)
        try:

            tiempo_limite = (datetime.now() - timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
        duplicados = (supabase.table("movimientos")
            .select("*")
            .eq("user_id", user_id)
            .eq("tipo", tipo)
                    .eq("categoria", categoria)
            .eq("monto", float(monto))
            .gte("fecha", tiempo_limite)
            .execute())
                if duplicados.data:
                                    st.warning("⚠️ Ya existe un registro idéntico reciente. Evita hacer clic múltiple en el mismo botón.")
                                    return
                            except Exception as e:
        pass  # Si falla la verificación, continuar con el registro
    
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_dato = {
        "fecha": fecha,
        "tipo": tipo,
        "categoria": categoria,
        "monto": float(monto),
        "tasa": float(tasa),
        "descripcion": nota,
        "user_id": user_id
    }
    
    try:
        response = supabase.table("movimientos").insert(nuevo_dato).execute()
        
        if response.data:
            if tipo == "Ingreso":
                st.success(f"✅ Ingreso registrado: {categoria} (${monto})")
            elif tipo == "Gasto":
                st.warning(f"📉 Gasto registrado: {categoria} (-${monto})")
            else:
                st.info(f"🐷 Ahorro registrado: {categoria} (${monto})")
            st.rerun()
        else:
            st.error("❌ Error al guardar el registro")
    except Exception as e:
        st.error(f"❌ Error al guardar: {str(e)}")

# --- INTERFAZ DE LOGIN/REGISTRO ---

# --- CONFIGURAR TIMEOUT DE SESIÓN (5 minutos) ---
SESSION_TIMEOUT = 300  # 5 minutos en segundos

# Inicializar variables de sesión
if 'user' not in st.session_state:
    st.session_state.user = None
if 'last_activity' not in st.session_state:
    st.session_state.last_activity = time.time()

# Verificar timeout de inactividad
if st.session_state.user is not None:
    current_time = time.time()
    time_since_activity = current_time - st.session_state.last_activity
    
    if time_since_activity > SESSION_TIMEOUT:
        # Sesión expirada por inactividad
        st.session_state.clear()
        st.warning("⏰ Tu sesión expiró por inactividad. Por favor inicia sesión nuevamente.")
        st.rerun()
    else:
        # Actualizar tiempo de última actividad
        st.session_state.last_activity = current_time

if st.session_state.user is None:
    st.title("🐗 Pumba Cash Web")
    st.markdown("### Sistema de Control Financiero Personal")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        st.subheader("Iniciar Sesión")
        email_login = st.text_input("Email", key="email_login")
        password_login = st.text_input("Contraseña", type="password", key="password_login")
        
        if st.button("Entrar", key="login_button"):
            if email_login and password_login:
                response = login_user(email_login, password_login)
                if response and response.user:
                    st.session_state.user = response.user
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("Email o contraseña incorrectos")
            else:
                st.error("Por favor completa todos los campos")
    
    with tab2:
        st.subheader("Crear Cuenta Nueva")
        email_register = st.text_input("Email", key="email_register")
        password_register = st.text_input("Contraseña (mínimo 6 caracteres)", type="password", key="password_register")
        password_confirm = st.text_input("Confirmar Contraseña", type="password", key="password_confirm")
        
        if st.button("Crear Cuenta", key="register_button"):
            if email_register and password_register and password_confirm:
                if password_register == password_confirm:
                    if len(password_register) >= 6:
                        response = register_user(email_register, password_register)
                        if response and response.user:
                            st.success("✅ Cuenta creada! Revisa tu email para confirmar tu cuenta.")
                        else:
                            st.error("Error al crear la cuenta. El email puede estar ya registrado.")
                    else:
                        st.error("La contraseña debe tener al menos 6 caracteres")
                else:
                    st.error("Las contraseñas no coinciden")
            else:
                st.error("Por favor completa todos los campos")
else:
    # Usuario autenticado - mostrar la aplicación principal
    user_id = st.session_state.user.id
    user_email = st.session_state.user.email
    
    # Header con opción de logout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🐗 Pumba Cash Web")
    with col2:
        st.write(f"👤 {user_email}")
        if st.button("Cerrar Sesión"):
            logout_user()
    
    # Cargar datos del usuario
    df = cargar_datos(user_id)
    
    # Calcular resúmenes
    total_ingresos = df[df["Tipo"] == "Ingreso"]["Monto"].sum() if not df.empty else 0
    total_gastos = df[df["Tipo"] == "Gasto"]["Monto"].sum() if not df.empty else 0
    total_ahorros = df[df["Tipo"].str.contains("Ahorro|Inversión", na=False)]["Monto"].sum() if not df.empty else 0
    
    # Mostrar resumen
    col1, col2, col3 = st.columns(3)
    col1.metric("💚 Ingresos", f"${total_ingresos:.2f}")
    col2.metric("🍅 Gastos", f"${total_gastos:.2f}")
    col3.metric("🐷 Ahorros/Inv", f"${total_ahorros:.2f}")
    
    disponible = total_ingresos - total_gastos - total_ahorros
    st.info(f"💰 DISPONIBLE EN MANO: ${disponible:.2f}")
    
    st.markdown("---")
    
    # Formulario de nuevo registro
    st.subheader("📝 Nuevo Registro")
    
    col1, col2 = st.columns(2)
    with col1:
        monto_input = st.number_input("Monto ($)", min_value=0.00, format="%.2f", key="monto")
    with col2:
        tasa_input = st.number_input("Tasa (Bs)", min_value=0.00, format="%.2f", key="tasa")
    
    nota_input = st.text_input("Nota (Opcional)", key="nota")
    
    st.write("Selecciona la categoría para guardar:")
    
    # Botones de categorías
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⛽ Gasolina", use_container_width=True):
            guardar_registro("Gasto", "Gasolina", monto_input, tasa_input, nota_input, user_id)
        if st.button("🏍️ Gastos Moto", use_container_width=True):
            guardar_registro("Gasto", "Gastos Moto", monto_input, tasa_input, nota_input, user_id)
        if st.button("🍔 Comida", use_container_width=True):
            guardar_registro("Gasto", "Comida", monto_input, tasa_input, nota_input, user_id)
        if st.button("💳 Créditos", use_container_width=True):
            guardar_registro("Gasto", "Créditos", monto_input, tasa_input, nota_input, user_id)
        if st.button("💊 Salud", use_container_width=True):
            guardar_registro("Gasto", "Salud", monto_input, tasa_input, nota_input, user_id)
    
    with col2:
        if st.button("🚗 Mant. Carro", use_container_width=True):
            guardar_registro("Gasto", "Mant. Carro", monto_input, tasa_input, nota_input, user_id)
        if st.button("📱 Pago Cashea", use_container_width=True):
            guardar_registro("Gasto", "Pago Cashea", monto_input, tasa_input, nota_input, user_id)
        if st.button("🚀 Salidas", use_container_width=True):
            guardar_registro("Gasto", "Salidas", monto_input, tasa_input, nota_input, user_id)
        if st.button("🏢 Inversión Ofic.", use_container_width=True):
            guardar_registro("Gasto", "Inversión Ofic.", monto_input, tasa_input, nota_input, user_id)
        if st.button("🔧 Otros Vehiculo", use_container_width=True):
            guardar_registro("Gasto", "Otros Vehiculo", monto_input, tasa_input, nota_input, user_id)
    
    st.markdown("### 💱 Divisas y Capital")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Venta Divisas (Salida)", use_container_width=True):
            guardar_registro("Gasto", "Venta Divisas", monto_input, tasa_input, nota_input, user_id)
        if st.button("💵 Ingreso Quincena", use_container_width=True):
            guardar_registro("Ingreso", "Ingreso Quincena", monto_input, tasa_input, nota_input, user_id)
    with col2:
        if st.button("📥 Compra Divisas (Ahorro)", use_container_width=True):
            guardar_registro("Ahorro", "Compra Divisas", monto_input, tasa_input, nota_input, user_id)
        if st.button("💰 Otros Ahorros", use_container_width=True):
            guardar_registro("Ahorro", "Otros Ahorros", monto_input, tasa_input, nota_input, user_id)
    
    # Mostrar historial
    with st.expander("📊 Ver Historial Completo"):
        if not df.empty:
            df_display = df.copy()
            df_display["Total Bs"] = df_display["Monto"] * df_display["Tasa"]
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("No hay registros aún. ¡Empieza a registrar tus movimientos!")








