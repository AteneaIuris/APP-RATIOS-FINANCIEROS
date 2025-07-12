import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Ratios Financieros", layout="wide")

st.title("📊 Cálculo de Ratios Financieros")
st.markdown("Carga un **Balance de Situación** y una **Cuenta de Pérdidas y Ganancias** en formato Excel para obtener los ratios automáticamente.")

# --- Función para buscar partidas ---
def buscar_valor_por_nombre(df, clave, columna_valor='Importe 2024'):
    df['Cuenta'] = df['Cuenta'].astype(str)
    coincidencias = df[df['Cuenta'].str.contains(clave, case=False, na=False)]
    if not coincidencias.empty:
        return float(coincidencias.iloc[0][columna_valor])
    return 0.0

# --- Subida de archivos ---
col1, col2 = st.columns(2)
with col1:
    balance_file = st.file_uploader("📁 Subir Balance de Situación", type=["xlsx"], key="balance")
with col2:
    pyg_file = st.file_uploader("📁 Subir Cuenta de Pérdidas y Ganancias", type=["xlsx"], key="pyg")

if balance_file and pyg_file:
    try:
        # Leer hojas
        activo_df = pd.read_excel(balance_file, sheet_name="Activo", skiprows=5)
        pasivo_df = pd.read_excel(balance_file, sheet_name="Pasivo", skiprows=5)
        pyg_df = pd.read_excel(pyg_file, sheet_name="Cuenta de Pérdidas y Ganancias", skiprows=5)

        # Renombrar columnas
        activo_df.columns = ['Cuenta', 'Importe']
        pasivo_df.columns = ['Cuenta', 'Importe 2024', 'Importe 2023']
        pyg_df.columns = ['Cuenta', 'Importe 2024', 'Importe 2023']

        # --- Extracción de partidas ---
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

        # --- Cálculo de ratios ---
        ratios = {
            "1. Liquidez General": activo_corriente / pasivo_corriente if pasivo_corriente else None,
            "2. Prueba Ácida": (activo_corriente - existencias) / pasivo_corriente if pasivo_corriente else None,
            "3. Ratio de Tesorería": (tesoreria + inversiones_cp) / pasivo_corriente if pasivo_corriente else None,
            "4. Endeudamiento Total": pasivo_total / patrimonio_neto if patrimonio_neto else None,
            "5. Cobertura de Gastos Financieros": ebit / gastos_financieros if gastos_financieros else None,
            "6. ROA": beneficio_neto / activo_total if activo_total else None,
            "7. ROS": beneficio_neto / ventas if ventas else None,
            "8. ROCE": ebit / (patrimonio_neto + pasivo_no_corriente) if (patrimonio_neto + pasivo_no_corriente) else None,
            "9. Rotación de Existencias": consumo_explotacion / existencias if existencias else None,
            "10. PMC (Clientes)": (clientes / ventas) * 365 if ventas else None,
            "11. PMP (Proveedores)": (proveedores / compras) * 365 if compras else None,
            "12. Ciclo de Conversión de Caja": (
                ((clientes / ventas) * 365 if ventas else 0) +
                (365 / (consumo_explotacion / existencias) if existencias else 0) -
                ((proveedores / compras) * 365 if compras else 0)
            ),
            "13. Apalancamiento Financiero": (
                (beneficio_neto / patrimonio_neto) / (beneficio_neto / activo_total)
                if patrimonio_neto and activo_total and beneficio_neto else None
            )
        }

        # --- Mostrar resultados ---
        st.success("✅ Ratios calculados correctamente")
        ratios_df = pd.DataFrame(ratios.items(), columns=["Ratio", "Valor"]).round(4)
        st.dataframe(ratios_df, use_container_width=True)

        # --- Exportar como Excel ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            ratios_df.to_excel(writer, index=False, sheet_name="Ratios 2024")
        st.download_button(
            label="📥 Descargar ratios en Excel",
            data=output.getvalue(),
            file_name="ratios_financieros.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error al procesar los archivos: {e}")
