import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

# ===== CONFIGURACIÓN GENERAL =====
st.set_page_config(page_title="Ratios Financieros Avanzados", layout="wide")
st.title("📊 Dashboard de Ratios Financieros")
st.markdown("Esta herramienta permite calcular, interpretar y visualizar ratios financieros clave a partir de un balance de situación y cuenta de pérdidas y ganancias en formato Excel.")

# ===== USUARIOS AUTORIZADOS =====
USUARIOS = {
    "Sergio": "ateneaiuris",
    "Miguel": "ateneaiuris"
}

# ===== FUNCIÓN DE AUTENTICACIÓN =====
def autenticar():
    st.markdown("## 🔐 Acceso restringido")
    usuario = st.text_input("Usuario", key="usuario_login")
    contrasena = st.text_input("Contraseña", type="password", key="clave_login")

    if st.button("Iniciar sesión"):
        if usuario in USUARIOS and USUARIOS[usuario] == contrasena:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario
            st.session_state["acceso_concedido"] = True  # bandera de acceso
        else:
            st.error("❌ Usuario o contraseña incorrectos")

# ===== CONTROL DE ACCESO =====
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    autenticar()
    st.stop()

# ===== TRANSICIÓN POST-LOGIN (una sola vez) =====
if st.session_state.get("acceso_concedido"):
    st.success(f"✅ Bienvenido, {st.session_state['usuario']}. Accediendo al entorno...")
    st.session_state["acceso_concedido"] = False
    st.stop()

# ===== PERFIL ACTIVO Y CIERRE DE SESIÓN =====
usuario_actual = st.session_state.get("usuario", "Usuario")
with st.sidebar:
    st.markdown(f"👤 Usuario: **{usuario_actual}**")
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.success("🔒 Sesión cerrada correctamente.")
        st.stop()

# ===== FUNCIONES =====
def buscar_valor_por_nombre(df, clave, columna_valor='Importe 2024'):
    df['Cuenta'] = df['Cuenta'].astype(str)
    coincidencias = df[df['Cuenta'].str.contains(clave, case=False, na=False)]
    if not coincidencias.empty:
        return float(coincidencias.iloc[0][columna_valor])
    return 0.0

def safe_div(numerador, denominador):
    try:
        return numerador / denominador if denominador != 0 else None
    except:
        return None

def evaluar_ratio(nombre, valor):
    if valor is None:
        return "🔘", "No disponible"
    if nombre == "Liquidez General":
        if valor > 1.5: return "🟢", "Buena capacidad de pago a corto plazo."
        elif valor >= 1.0: return "🟡", "Liquidez aceptable, debe vigilarse."
        else: return "🔴", "Posible insolvencia a corto plazo."
    elif nombre == "Prueba Ácida":
        if valor > 1.0: return "🟢", "Suficiencia inmediata sin existencias."
        elif valor >= 0.8: return "🟡", "Liquidez justa sin inventario."
        else: return "🔴", "Insuficiencia para cubrir pasivos inmediatos."
    elif nombre == "Ratio de Tesorería":
        if valor > 0.5: return "🟢", "Buena cobertura de pasivo con caja."
        elif valor >= 0.2: return "🟡", "Cierta tensión en tesorería."
        else: return "🔴", "Riesgo de falta de efectivo."
    elif nombre == "Endeudamiento Total":
        if valor < 1.0: return "🟢", "Bajo nivel de apalancamiento."
        elif valor <= 2.0: return "🟡", "Endeudamiento moderado."
        else: return "🔴", "Alta dependencia de deuda."
    elif nombre == "Cobertura de Gastos Financieros":
        if valor > 3.0: return "🟢", "Intereses cubiertos cómodamente."
        elif valor >= 1.5: return "🟡", "Cobertura ajustada."
        else: return "🔴", "Peligro financiero: EBIT insuficiente."
    elif nombre == "ROA":
        if valor > 0.05: return "🟢", "Buena rentabilidad de los activos."
        elif valor >= 0.02: return "🟡", "Rentabilidad discreta."
        else: return "🔴", "Baja eficiencia del capital invertido."
    elif nombre == "ROS":
        if valor > 0.07: return "🟢", "Margen neto adecuado."
        elif valor >= 0.03: return "🟡", "Rentabilidad limitada."
        else: return "🔴", "Margen muy reducido."
    elif nombre == "ROCE":
        if valor > 0.10: return "🟢", "Buen rendimiento del capital operativo."
        elif valor >= 0.05: return "🟡", "Rendimiento aceptable."
        else: return "🔴", "Rentabilidad insuficiente sobre el capital."
    elif nombre == "Rotación de Existencias":
        if valor > 5: return "🟢", "Almacén eficiente y dinámico."
        elif valor >= 3: return "🟡", "Rotación adecuada pero mejorable."
        else: return "🔴", "Riesgo de acumulación de existencias."
    elif nombre in ["PMC (Clientes)", "PMP (Proveedores)"]:
        if valor < 90: return "🟢", "Ciclo de cobro/pago saludable."
        elif valor <= 120: return "🟡", "Periodo algo prolongado."
        else: return "🔴", "Cobro o pago excesivamente lento."
    elif nombre == "Ciclo de Conversión de Caja":
        if valor < 60: return "🟢", "Ciclo financiero eficiente."
        elif valor <= 120: return "🟡", "Ciclo medio controlado."
        else: return "🔴", "Ciclo de caja muy largo."
    elif nombre == "Apalancamiento Financiero":
        if 1.0 <= valor <= 1.5: return "🟢", "Apalancamiento equilibrado."
        elif 0.8 <= valor <= 1.0 or 1.5 < valor <= 2.0: return "🟡", "Moderado, requiere atención."
        else: return "🔴", "Riesgo alto o escasa ventaja del apalancamiento."
    return "🔘", "Interpretación no definida."

# ===== CARGA DE ARCHIVOS =====
col1, col2 = st.columns(2)
with col1:
    balance_file = st.file_uploader("📁 Subir Balance de Situación", type=["xlsx"], key="balance")
with col2:
    pyg_file = st.file_uploader("📁 Subir Cuenta de Pérdidas y Ganancias", type=["xlsx"], key="pyg")

if balance_file and pyg_file:
    try:
        activo_df = pd.read_excel(balance_file, sheet_name="Activo", skiprows=5)
        pasivo_df = pd.read_excel(balance_file, sheet_name="Pasivo", skiprows=5)
        pyg_df = pd.read_excel(pyg_file, sheet_name="Cuenta de Pérdidas y Ganancias", skiprows=5)

        activo_df.columns = ['Cuenta', 'Importe']
        pasivo_df.columns = ['Cuenta', 'Importe 2024', 'Importe 2023']
        pyg_df.columns = ['Cuenta', 'Importe 2024', 'Importe 2023']

        activo_corriente = buscar_valor_por_nombre(activo_df, "ACTIVO CORRIENTE", "Importe")
        existencias = buscar_valor_por_nombre(activo_df, "EXISTENCIAS", "Importe")
        tesoreria = buscar_valor_por_nombre(activo_df, "TESORERÍA", "Importe")
        inversiones_cp = buscar_valor_por_nombre(activo_df, "INVERSIONES FINANCIERAS A CORTO", "Importe")
        activo_total = buscar_valor_por_nombre(activo_df, "TOTAL ACTIVO", "Importe")
        clientes = buscar_valor_por_nombre(activo_df, "CLIENTES", "Importe")

        pasivo_corriente = buscar_valor_por_nombre(pasivo_df, "PASIVO CORRIENTE")
        pasivo_no_corriente = buscar_valor_por_nombre(pasivo_df, "PASIVO NO CORRIENTE")
        pasivo_total = buscar_valor_por_nombre(pasivo_df, "TOTAL PASIVO")
        patrimonio_neto = buscar_valor_por_nombre(pasivo_df, "PATRIMONIO NETO")
        proveedores = buscar_valor_por_nombre(pasivo_df, "PROVEEDORES")

        ventas = buscar_valor_por_nombre(pyg_df, "VENTAS")
        compras = buscar_valor_por_nombre(pyg_df, "COMPRAS")
        consumo_explotacion = buscar_valor_por_nombre(pyg_df, "CONSUMO DE EXPLOTACIÓN")
        gastos_financieros = abs(buscar_valor_por_nombre(pyg_df, "GASTOS FINANCIEROS"))
        ebit = buscar_valor_por_nombre(pyg_df, "RESULTADO DE EXPLOTACIÓN")
        beneficio_neto = buscar_valor_por_nombre(pyg_df, "RESULTADO DEL EJERCICIO")

        ratios = {
            "Liquidez General": safe_div(activo_corriente, pasivo_corriente),
            "Prueba Ácida": safe_div((activo_corriente - existencias), pasivo_corriente),
            "Ratio de Tesorería": safe_div((tesoreria + inversiones_cp), pasivo_corriente),
            "Endeudamiento Total": safe_div(pasivo_total, patrimonio_neto),
            "Cobertura de Gastos Financieros": safe_div(ebit, gastos_financieros),
            "ROA": safe_div(beneficio_neto, activo_total),
            "ROS": safe_div(beneficio_neto, ventas),
            "ROCE": safe_div(ebit, patrimonio_neto + pasivo_no_corriente),
            "Rotación de Existencias": safe_div(consumo_explotacion, existencias),
            "PMC (Clientes)": safe_div(clientes, ventas) * 365 if ventas else None,
            "PMP (Proveedores)": safe_div(proveedores, compras) * 365 if compras else None,
            "Ciclo de Conversión de Caja": (
                (safe_div(clientes, ventas) * 365 if ventas else 0) +
                (365 / safe_div(consumo_explotacion, existencias) if existencias and consumo_explotacion else 0) -
                (safe_div(proveedores, compras) * 365 if compras else 0)
            ),
            "Apalancamiento Financiero": safe_div(
                safe_div(beneficio_neto, patrimonio_neto),
                safe_div(beneficio_neto, activo_total)
            ) if beneficio_neto and patrimonio_neto and activo_total else None
        }

        # ===== TABLA COMPLETA CON INTERPRETACIÓN =====
        st.subheader("📄 Tabla Detallada con Interpretación")
        tabla_ratios = []
        for nombre, valor in ratios.items():
            icono, comentario = evaluar_ratio(nombre, valor)
            tabla_ratios.append({
                "Ratio": nombre,
                "Valor": round(valor, 4) if valor is not None else "N/A",
                "Evaluación": icono,
                "Comentario": comentario
            })

        tabla_df = pd.DataFrame(tabla_ratios)
        st.dataframe(tabla_df, use_container_width=True)

        # ===== REPRESENTACIÓN GRÁFICA SEPARADA POR TIPO DE RATIO =====
        st.subheader("📈 Representación Gráfica por Categoría de Ratios")

        grafico_df = tabla_df[tabla_df["Valor"] != "N/A"].copy()
        grafico_df["Valor"] = pd.to_numeric(grafico_df["Valor"], errors="coerce")

        ratios_dias = grafico_df[grafico_df["Ratio"].str.contains("PMC|PMP|Ciclo", case=False)]
        ratios_prop = grafico_df[~grafico_df["Ratio"].str.contains("PMC|PMP|Ciclo", case=False)]

        st.markdown("### 📊 Ratios Proporcionales (Escala Normalizada)")
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        ax1.barh(ratios_prop["Ratio"], ratios_prop["Valor"], color="steelblue")
        ax1.set_xlabel("Valor")
        ax1.set_title("Ratios Financieros - Proporciones")
        ax1.grid(axis='x', linestyle='--', alpha=0.4)
        st.pyplot(fig1)

        st.markdown("### 🕒 Ratios de Plazo (en días)")
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        ax2.barh(ratios_dias["Ratio"], ratios_dias["Valor"], color="darkorange")
        ax2.set_xlabel("Días")
        ax2.set_title("Ratios Financieros - Periodos")
        ax2.grid(axis='x', linestyle='--', alpha=0.4)
        st.pyplot(fig2)

        # ===== EXPORTACIÓN EXCEL =====
        st.subheader("📥 Exportar Resultados")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            tabla_df.to_excel(writer, index=False, sheet_name="Ratios Financieros")
        st.download_button(
            label="📤 Descargar en Excel",
            data=output.getvalue(),
            file_name="ratios_financieros.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error al procesar los archivos: {e}")
