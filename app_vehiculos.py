import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración inicial
st.set_page_config(page_title="Dashboard: Mercado Electrificado Chile", layout="wide")
st.title("⚡ Plataforma de Inteligencia del Mercado Electrificado en Chile")

# 2. Funciones para cargar datos
@st.cache_data
def cargar_homologados():
    df = pd.read_excel(
        "e1_Nomina_Vehiculos_Livianos_y_Medianos_Homologados_22_jun_2026.xls", 
        sheet_name="Livianos & Medianos 2013 - 2026", 
        skiprows=2
    )
    electrificados = df[df['Propulsión'].isin([
        'Vehículo eléctrico', 'Híbrido con recarga exterior', 'Híbrido sin recarga exterior'
    ])].copy()
    electrificados = electrificados.replace('-', pd.NA)
    electrificados = electrificados.dropna(axis=1, thresh=len(electrificados) * 0.20)
    electrificados = electrificados.astype(str)
    
    col_kwh = next((c for c in electrificados.columns if 'kwh' in c.lower()), None)
    if col_kwh:
        electrificados[col_kwh] = electrificados[col_kwh].str.replace(',', '.').str.strip()
        electrificados['Capacidad kWh'] = pd.to_numeric(electrificados[col_kwh], errors='coerce')
    
    col_tipo_bat = next((c for c in electrificados.columns if 'tipo' in c.lower() and 'bater' in c.lower()), None)
    if col_tipo_bat:
        electrificados['Quimica_Bateria'] = electrificados[col_tipo_bat]
        
    def clasificar_ev(tipo):
        if tipo == 'Vehículo eléctrico': return 'EV'
        elif tipo == 'Híbrido con recarga exterior': return 'PHEV'
        elif tipo == 'Híbrido sin recarga exterior': return 'HEV'
        return tipo
        
    electrificados['Tipo'] = electrificados['Propulsión'].apply(clasificar_ev)
    electrificados['Marca'] = electrificados['Marca'].str.upper().str.strip()
    return electrificados

@st.cache_data
def cargar_ventas():
    dict_ventas = pd.read_excel("Estadísticas de Ventas de Vehículos Eléctricos e Híbridos en Chile.xlsx", sheet_name=None)
    df_ventas = pd.concat(dict_ventas.values(), ignore_index=True)
    df_ventas['Marca'] = df_ventas['Marca'].astype(str).str.upper().str.strip()
    return df_ventas

@st.cache_data
def cargar_top_modelos():
    dict_top = pd.read_excel("Copia de modelos mas vendidos 2022 a 2026.xlsx", sheet_name=None)
    df_list = []
    
    for sheet, df in dict_top.items():
        column_mapping = {
            'capacidad kWh': 'kWh fabricante',
            'fabricante bateria': 'Fabricante Batería',
            'fabricante': 'Fabricante Batería',
            'quimica de la bateria': 'Química',
            'Suma Total': 'Ventas Totales',
            'voltaje fabricante': 'Voltaje',
            'voltaje': 'Voltaje',
            'V nominal': 'Voltaje Nominal',
            'voltaje nominal': 'Voltaje Nominal'
        }
        df = df.rename(columns=column_mapping)
        df['Tipo'] = sheet 
        df_list.append(df)
        
    df_top = pd.concat(df_list, ignore_index=True)
    df_top = df_top.dropna(subset=['Marca', 'Modelo'])
    
    df_top['Marca'] = df_top['Marca'].astype(str).str.upper().str.strip()
    df_top['Modelo'] = df_top['Modelo'].astype(str).str.upper().str.strip()
    df_top['kWh fabricante'] = pd.to_numeric(df_top['kWh fabricante'], errors='coerce')
    df_top['Voltaje'] = df_top['Voltaje'].astype(str).str.upper().str.strip().replace('NAN', 'DESCONOCIDO')
    df_top['Química'] = df_top['Química'].astype(str).str.upper().str.strip().replace('NAN', 'DESCONOCIDA')
    df_top['Fabricante Batería'] = df_top['Fabricante Batería'].astype(str).str.upper().str.strip().replace('NAN', 'DESCONOCIDO')
    
    return df_top

# Carga segura de archivos
try: df_homologados = cargar_homologados()
except: df_homologados = pd.DataFrame()

try: df_ventas = cargar_ventas()
except: df_ventas = pd.DataFrame()

try: df_top = cargar_top_modelos()
except: df_top = pd.DataFrame()

colores_tech = {'EV': '#00CC96', 'BEV': '#00CC96', 'PHEV': '#636EFA', 'HEV': '#EF553B'}

# --- INDICADORES TOTALES (KPIS FIJOS SUPERIORES) ---
if not df_ventas.empty:
    st.markdown("### 📊 Indicadores Clave del Parque Circulante")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    total_unidades = df_ventas['Total Acumulado'].sum()
    
    # Estimación global de energía acumulada en las calles
    homologados_kwh_kpi = df_homologados.groupby(['Marca', 'Tipo'])['Capacidad kWh'].mean().reset_index()
    ventas_kpi = df_ventas.rename(columns={'Tipo (EV/PHEV/HEV)': 'Tipo'})
    cruce_kpi = pd.merge(ventas_kpi, homologados_kwh_kpi, on=['Marca', 'Tipo'], how='inner')
    total_mwh_pais = (cruce_kpi['Total Acumulado'] * cruce_kpi['Capacidad kWh']).sum() / 1000

    with kpi1:
        st.metric(label="🚗 Total Vehículos Electrificados Vendidos", value=f"{total_unidades:,.0f} u.")
    with kpi2:
        st.metric(label="⚡ Almacenamiento Móvil Estimado", value=f"{total_mwh_pais:,.1f} MWh")
    with kpi3:
        st.metric(label="📋 Modelos Certificados en el 3CV", value=f"{len(df_homologados)} modelos")
    st.divider()

# 3. Interfaz Principal
tab_ventas, tab_tecnico, tab_catalogo, tab_insights, tab_ecosistema = st.tabs([
    "📈 Impacto Ventas", 
    "🔋 Análisis 3CV", 
    "🗂️ Buscador",
    "🧠 Homologado v/s Ventas",
    "🏭 Ecosistema de Baterías"
])

# --- PESTAÑA 1: VENTAS REALES POR PERIODO Y TECNOLOGÍA ---
with tab_ventas:
    st.header("Análisis de Ventas Reales")
    if not df_ventas.empty:
        periodos_disponibles = ['Total Acumulado', '2026 (Ene-May)', '2025', '2024', '2023', '2022', '2021 (Dic)']
        periodos_reales = [p for p in periodos_disponibles if p in df_ventas.columns]
        
        col_filtro1, col_filtro2 = st.columns(2)
        with col_filtro1:
            periodo_seleccionado = st.selectbox("📅 Filtrar por Periodo:", periodos_reales)
        with col_filtro2:
            marcas_ventas_filtro = st.multiselect("🔍 Filtrar Marcas Específicas (Opcional):", sorted(df_ventas['Marca'].unique()))
            
        col_ev, col_phev, col_hev = st.columns(3)
        
        def crear_grafico_ventas(tipo, color, titulo):
            df_filtro = df_ventas[df_ventas['Tipo (EV/PHEV/HEV)'] == tipo]
            if marcas_ventas_filtro:
                df_filtro = df_filtro[df_filtro['Marca'].isin(marcas_ventas_filtro)]
                
            ventas = df_filtro.groupby('Marca')[periodo_seleccionado].sum().reset_index()
            ventas = ventas[ventas[periodo_seleccionado] > 0].sort_values(by=periodo_seleccionado, ascending=True) 
            if len(ventas) == 0:
                fig = px.bar(title=f"{titulo} (Sin registros)"); return fig
            altura = max(400, len(ventas) * 30)
            fig = px.bar(ventas, x=periodo_seleccionado, y='Marca', orientation='h', text=periodo_seleccionado)
            fig.update_traces(marker_color=color, textposition='outside')
            fig.update_layout(title=titulo, showlegend=False, xaxis_title="Unidades", yaxis_title="", height=altura)
            return fig

        with col_ev: st.plotly_chart(crear_grafico_ventas('EV', colores_tech['EV'], '🔋 100% Eléctricos'), use_container_width=True)
        with col_phev: st.plotly_chart(crear_grafico_ventas('PHEV', colores_tech['PHEV'], '🔌 Híbridos Enchufables'), use_container_width=True)
        with col_hev: st.plotly_chart(crear_grafico_ventas('HEV', colores_tech['HEV'], '♻️ Híbridos Convencionales'), use_container_width=True)

# --- PESTAÑA 2: ANÁLISIS TÉCNICO E IMPORTADORES ---
with tab_tecnico:
    st.header("Visión General del Mercado e Importadores")
    if not df_homologados.empty:
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            hom_tipo = df_homologados['Tipo'].value_counts().reset_index()
            fig_hom_pie = px.pie(hom_tipo, values='count', names='Tipo', title="Oferta: Modelos Homologados (3CV)", hole=0.4, color='Tipo', color_discrete_map=colores_tech)
            st.plotly_chart(fig_hom_pie, use_container_width=True)
            
        with col_pie2:
            if not df_ventas.empty:
                ventas_tipo = df_ventas.groupby('Tipo (EV/PHEV/HEV)')['Total Acumulado'].sum().reset_index()
                fig_ven_pie = px.pie(ventas_tipo, values='Total Acumulado', names='Tipo (EV/PHEV/HEV)', title="Demanda: Ventas Reales Acumuladas", hole=0.4, color='Tipo (EV/PHEV/HEV)', color_discrete_map=colores_tech)
                st.plotly_chart(fig_ven_pie, use_container_width=True)
                
        st.divider()
        imp_tipo = df_homologados.dropna(subset=['Importador']).groupby(['Importador', 'Tipo']).size().reset_index(name='Cantidad')
        orden_imp = df_homologados['Importador'].value_counts().index
        fig_imp = px.bar(imp_tipo, x='Cantidad', y='Importador', color='Tipo', orientation='h', color_discrete_map=colores_tech, category_orders={'Importador': orden_imp})
        fig_imp.update_layout(title="Modelos Homologados por Importador", height=max(450, len(orden_imp)*25))
        st.plotly_chart(fig_imp, use_container_width=True)

        st.divider()
        st.subheader("Análisis Técnico y Energético de Baterías")
        tipo_tecnico = st.radio("Filtra la tecnología para ver el detalle de sus baterías y energía:", ["🔋 EV", "🔌 PHEV", "♻️ HEV"], horizontal=True)
        tipo_elegido = {"🔋 EV": "EV", "🔌 PHEV": "PHEV", "♻️ HEV": "HEV"}[tipo_tecnico]
        df_tech_filtro = df_homologados[df_homologados['Tipo'] == tipo_elegido]
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown(f"**Química de Batería ({tipo_elegido})**")
            if 'Quimica_Bateria' in df_tech_filtro.columns:
                conteo_bat = df_tech_filtro['Quimica_Bateria'].dropna().value_counts().reset_index()
                conteo_bat = conteo_bat[conteo_bat['Quimica_Bateria'] != 'nan']
                if len(conteo_bat) > 0:
                    fig_bat = px.bar(conteo_bat, x='count', y='Quimica_Bateria', orientation='h', text='count')
                    fig_bat.update_traces(marker_color=colores_tech[tipo_elegido], textposition='outside')
                    fig_bat.update_layout(xaxis_title="Modelos", yaxis_title="", height=max(350, len(conteo_bat)*40), margin=dict(l=0, r=20, t=20, b=20))
                    st.plotly_chart(fig_bat, use_container_width=True)
                else:
                    st.info("No hay datos de química legibles.")

        with col_t2:
            st.markdown(f"**Distribución Detallada de Capacidad en {tipo_elegido}**")
            if 'Capacidad kWh' in df_tech_filtro.columns:
                df_kwh_filtro = df_tech_filtro[df_tech_filtro['Capacidad kWh'].notna()].copy()
                if len(df_kwh_filtro) > 0:
                    promedio = df_kwh_filtro['Capacidad kWh'].mean()
                    maximo = df_kwh_filtro['Capacidad kWh'].max()
                    st.caption(f"⚡ **Promedio:** {promedio:.1f} kWh | **Máximo:** {maximo:.1f} kWh")
                    
                    if tipo_elegido == 'HEV':
                        bins = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 10]
                        labels = ['0 - 0.5 kWh', '0.6 - 1.0 kWh', '1.1 - 1.5 kWh', '1.6 - 2.0 kWh', '2.1 - 2.5 kWh', '2.6 - 3.0 kWh', 'Más de 3.0 kWh']
                    elif tipo_elegido == 'PHEV':
                        bins = [0, 5, 10, 15, 20, 25, 30, 40, 100]
                        labels = ['0 - 5 kWh', '6 - 10 kWh', '11 - 15 kWh', '16 - 20 kWh', '21 - 25 kWh', '26 - 30 kWh', '31 - 40 kWh', 'Más de 40 kWh']
                    else:
                        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150, 300]
                        labels = ['0-10 kWh', '11-20 kWh', '21-30 kWh', '31-40 kWh', '41-50 kWh', '51-60 kWh', '61-70 kWh', '71-80 kWh', '81-90 kWh', '91-100 kWh', '101-120 kWh', '121-150 kWh', 'Más de 150 kWh']
                    
                    df_kwh_filtro['Rango kWh'] = pd.cut(df_kwh_filtro['Capacidad kWh'], bins=bins, labels=labels, right=True)
                    conteo_rangos = df_kwh_filtro['Rango kWh'].value_counts().reset_index()
                    conteo_rangos.columns = ['Rango', 'Cantidad de Modelos']
                    
                    conteo_rangos['Rango'] = pd.Categorical(conteo_rangos['Rango'], categories=labels, ordered=True)
                    conteo_rangos = conteo_rangos.sort_values('Rango')
                    conteo_rangos = conteo_rangos[conteo_rangos['Cantidad de Modelos'] > 0]
                    
                    fig_kwh = px.bar(conteo_rangos, x='Rango', y='Cantidad de Modelos', text='Cantidad de Modelos', color_discrete_sequence=[colores_tech[tipo_elegido]])
                    fig_kwh.update_traces(textposition='outside')
                    fig_kwh.update_layout(xaxis_title="Rango de Capacidad de Batería", height=400, margin=dict(l=0, r=20, t=20, b=20))
                    st.plotly_chart(fig_kwh, use_container_width=True)

        st.divider()
        st.subheader(f"Evolución de Capacidad de Almacenamiento Inyectada a Chile ({tipo_elegido})")
        
        if not df_ventas.empty and 'Capacidad kWh' in df_homologados.columns:
            homologados_kwh = df_homologados[df_homologados['Tipo'] == tipo_elegido].groupby('Marca')['Capacidad kWh'].mean().reset_index()
            ventas_tipo = df_ventas[df_ventas['Tipo (EV/PHEV/HEV)'] == tipo_elegido]
            
            columnas_anios = ['2021 (Dic)', '2022', '2023', '2024', '2025', '2026 (Ene-May)']
            energia_por_anio = []
            
            for anio in columnas_anios:
                if anio in ventas_tipo.columns:
                    ventas_anio = ventas_tipo[['Marca', anio]].groupby('Marca').sum().reset_index()
                    cruce_anio = pd.merge(ventas_anio, homologados_kwh, on='Marca', how='inner')
                    mwh_total = (cruce_anio[anio] * cruce_anio['Capacidad kWh']).sum() / 1000
                    energia_por_anio.append({'Año': anio, 'MWh Añadidos': mwh_total})
                    
            df_energia_tech = pd.DataFrame(energia_por_anio)
            
            if not df_energia_tech.empty and df_energia_tech['MWh Añadidos'].sum() > 0:
                fig_energia_tech = px.bar(df_energia_tech, x='Año', y='MWh Añadidos', text_auto='.1f', color_discrete_sequence=[colores_tech[tipo_elegido]])
                fig_energia_tech.update_traces(textposition='outside')
                fig_energia_tech.update_layout(height=400, yaxis_title="MWh Estimados Inyectados", xaxis_title="Periodo")
                st.plotly_chart(fig_energia_tech, use_container_width=True)

        st.divider()
        st.subheader("Evolución General de Energía Inyectada a la Red (Todas las Tecnologías)")

        if not df_ventas.empty and 'Capacidad kWh' in df_homologados.columns:
            homologados_kwh_all = df_homologados.groupby(['Marca', 'Tipo'])['Capacidad kWh'].mean().reset_index()
            energia_global = []
            
            for anio in columnas_anios:
                if anio in df_ventas.columns:
                    ventas_anio_all = df_ventas[['Marca', 'Tipo (EV/PHEV/HEV)', anio]].groupby(['Marca', 'Tipo (EV/PHEV/HEV)']).sum().reset_index()
                    ventas_anio_all = ventas_anio_all.rename(columns={'Tipo (EV/PHEV/HEV)': 'Tipo'})
                    
                    cruce_anio_all = pd.merge(ventas_anio_all, homologados_kwh_all, on=['Marca', 'Tipo'], how='inner')
                    cruce_anio_all['MWh Añadidos'] = (cruce_anio_all[anio] * cruce_anio_all['Capacidad kWh']) / 1000
                    
                    resumen_tipo = cruce_anio_all.groupby('Tipo')['MWh Añadidos'].sum().reset_index()
                    resumen_tipo['Año'] = anio
                    
                    for _, row in resumen_tipo.iterrows():
                        if row['MWh Añadidos'] > 0:
                            energia_global.append({'Año': row['Año'], 'Tipo': row['Tipo'], 'MWh Añadidos': row['MWh Añadidos']})
                            
            df_energia_global = pd.DataFrame(energia_global)
            
            if not df_energia_global.empty:
                df_energia_global['Tipo'] = pd.Categorical(df_energia_global['Tipo'], categories=['EV', 'PHEV', 'HEV'], ordered=True)
                df_energia_global = df_energia_global.sort_values(['Año', 'Tipo'])
                
                fig_energia_global = px.bar(df_energia_global, x='Año', y='MWh Añadidos', color='Tipo', color_discrete_map=colores_tech, text_auto='.1f')
                fig_energia_global.update_traces(textposition='inside') 
                fig_energia_global.update_layout(height=500, yaxis_title="MWh Totales Estimados", xaxis_title="Periodo")
                st.plotly_chart(fig_energia_global, use_container_width=True)

# --- PESTAÑA 3: CATÁLOGO CON EXPORTADOR ---
with tab_catalogo:
    st.header("🗂️ Base de Datos Completa (3CV)")
    if not df_homologados.empty:
        df_mostrar = df_homologados.copy()
        
        busqueda = st.text_input("🔍 Búsqueda rápida (ej: Ioniq 5, Kaufmann, Tesla...)")
        if busqueda: 
            df_mostrar = df_mostrar[df_mostrar.apply(lambda row: row.astype(str).str.contains(busqueda, case=False, na=False).any(), axis=1)]
        
        with st.expander("🛠️ Mostrar Filtros Avanzados"):
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1: marcas_sel = st.multiselect("🏷️ Marca", sorted(df_mostrar['Marca'].dropna().unique()))
            with col_f2: importadores_sel = st.multiselect("🏢 Importadora", sorted(df_mostrar['Importador'].dropna().unique()))
            with col_f3:
                if 'Quimica_Bateria' in df_mostrar.columns:
                    quimicas_disp = [q for q in df_mostrar['Quimica_Bateria'].dropna().unique() if str(q).lower() not in ['nan', '<na>']]
                    quimicas_sel = st.multiselect("🔋 Química de Batería", sorted(quimicas_disp))
                else: quimicas_sel = []
            with col_f4:
                if 'Capacidad kWh' in df_mostrar.columns and not df_mostrar['Capacidad kWh'].dropna().empty:
                    max_kwh = float(df_mostrar['Capacidad kWh'].max())
                    rango_kwh = st.slider("⚡ Capacidad Batería (kWh)", min_value=0.0, max_value=max_kwh, value=(0.0, max_kwh), step=5.0)
                else: rango_kwh = None

        if marcas_sel: df_mostrar = df_mostrar[df_mostrar['Marca'].isin(marcas_sel)]
        if importadores_sel: df_mostrar = df_mostrar[df_mostrar['Importador'].isin(importadores_sel)]
        if quimicas_sel: df_mostrar = df_mostrar[df_mostrar['Quimica_Bateria'].isin(quimicas_sel)]
        if rango_kwh:
            if rango_kwh[0] > 0.0 or rango_kwh[1] < max_kwh:
                df_mostrar = df_mostrar[(df_mostrar['Capacidad kWh'].notna()) & (df_mostrar['Capacidad kWh'] >= rango_kwh[0]) & (df_mostrar['Capacidad kWh'] <= rango_kwh[1])]

        # --- BOTÓN DE DESCARGA ---
        csv_catalogo = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Exportar Resultados Filtrados a CSV", data=csv_catalogo, file_name="catalogo_3cv_filtrado.csv", mime="text/csv")

        tab_cat_ev, tab_cat_phev, tab_cat_hev = st.tabs(["🔋 EV (100% Eléctricos)", "🔌 PHEV (Enchufables)", "♻️ HEV (Convencionales)"])
        def renderizar_catalogo(df_filtrado):
            st.markdown(f"**Resultados encontrados:** {len(df_filtrado)} modelos")
            st.dataframe(df_filtrado, width='stretch', height=400)
            
        with tab_cat_ev: renderizar_catalogo(df_mostrar[df_mostrar['Tipo'] == 'EV'])
        with tab_cat_phev: renderizar_catalogo(df_mostrar[df_mostrar['Tipo'] == 'PHEV'])
        with tab_cat_hev: renderizar_catalogo(df_mostrar[df_mostrar['Tipo'] == 'HEV'])

# --- PESTAÑA 4: INSIGHTS ESTRATÉGICOS ---
with tab_insights:
    st.header("Cruce de Homologaciones vs Ventas")
    if not df_ventas.empty and not df_homologados.empty:
        homologados_count = df_homologados[df_homologados['Tipo'] == 'EV'].groupby('Marca').size().reset_index(name='Modelos Homologados')
        ventas_ev = df_ventas[df_ventas['Tipo (EV/PHEV/HEV)'] == 'EV'].groupby('Marca')['Total Acumulado'].sum().reset_index()
        cruce = pd.merge(homologados_count, ventas_ev, on='Marca', how='inner')
        cruce = cruce[cruce['Total Acumulado'] > 0]
        
        fig_scatter = px.scatter(
            cruce, x='Modelos Homologados', y='Total Acumulado', size='Total Acumulado', 
            color='Marca', hover_name='Marca', text='Marca', size_max=60, title="Eficiencia de Catálogo (Solo EV)"
        )
        fig_scatter.update_traces(textposition='top center')
        fig_scatter.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig_scatter, use_container_width=True)

# --- PESTAÑA 5: ECOSISTEMA DE BATERÍAS Y ARQUITECTURA DE VOLTAJE ---
with tab_ecosistema:
    st.header("🏭 Ecosistema de Baterías: Modelos Más Vendidos")
    st.markdown("*(Análisis basado exclusivamente en la nómina de los modelos más vendidos en Chile)*")
    
    if not df_top.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1: tipo_eco = st.radio("Filtra la tecnología para el ecosistema:", ["Todos", "BEV", "PHEV", "HEV"], horizontal=True)
        with col_f2:
            opciones_periodo = ['Ventas Totales', '2026 (a Mayo)', '2025', '2024', '2023', '2022']
            periodos_reales_eco = [p for p in opciones_periodo if p in df_top.columns]
            periodo_eco = st.selectbox("📅 Analizar Ecosistema en el Periodo:", periodos_reales_eco)

        df_eco = df_top.copy() if tipo_eco == "Todos" else df_top[df_top['Tipo'] == tipo_eco].copy()
        df_eco[periodo_eco] = pd.to_numeric(df_eco[periodo_eco], errors='coerce').fillna(0)
        df_eco_filtrado = df_eco[df_eco[periodo_eco] > 0].copy()
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.subheader(f"Top 10 Modelos ({periodo_eco})")
            if not df_eco_filtrado.empty:
                df_eco_filtrado['Auto'] = df_eco_filtrado['Marca'] + " " + df_eco_filtrado['Modelo']
                top_modelos = df_eco_filtrado.sort_values(by=periodo_eco, ascending=False).head(10)
                fig_modelos = px.bar(top_modelos, x=periodo_eco, y='Auto', orientation='h', text=periodo_eco, color='Tipo', color_discrete_map=colores_tech)
                fig_modelos.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=True, height=450, yaxis_title="")
                st.plotly_chart(fig_modelos, use_container_width=True)
            else: st.info("No hay registros.")

        with col_m2:
            st.subheader("Crecimiento de Energía (MWh por Año)")
            anios = ['2022', '2023', '2024', '2025', '2026 (a Mayo)']
            energia_anios = []
            for anio in anios:
                if anio in df_eco.columns:
                    ventas_anio = pd.to_numeric(df_eco[anio], errors='coerce').fillna(0)
                    mwh_anio = (ventas_anio * df_eco['kWh fabricante']).sum() / 1000
                    energia_anios.append({'Año': anio, 'MWh': mwh_anio})
            df_energia = pd.DataFrame(energia_anios)
            fig_energia = px.bar(df_energia, x='Año', y='MWh', text_auto='.1f', color_discrete_sequence=['#F4D03F'])
            fig_energia.update_traces(textposition='outside')
            fig_energia.update_layout(height=450, yaxis_title="MWh Estimados")
            st.plotly_chart(fig_energia, use_container_width=True)

        st.divider()
        st.subheader(f"⚡ Arquitectura Eléctrica y Tensión ({periodo_eco})")
        st.markdown("*(Distribución de los niveles de voltaje nominales ponderados por volumen de ventas reales)*")
        
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            if not df_eco_filtrado.empty and 'Voltaje' in df_eco_filtrado.columns:
                df_voltaje = df_eco_filtrado.groupby('Voltaje')[periodo_eco].sum().reset_index()
                df_voltaje = df_voltaje[df_voltaje['Voltaje'] != 'DESCONOCIDO'].sort_values(by=periodo_eco, ascending=False)
                if not df_voltaje.empty:
                    fig_v = px.bar(df_voltaje, x='Voltaje', y=periodo_eco, text=periodo_eco, color='Voltaje', title="Modelos en Circulación por Nivel de Voltaje")
                    fig_v.update_traces(textposition='outside')
                    fig_v.update_layout(yaxis_title="Unidades Vendidas", showlegend=False, height=400)
                    st.plotly_chart(fig_v, use_container_width=True)
                else: st.info("Sin registros de voltaje legibles.")

        with col_v2:
            st.markdown("💡 **Importancia de la Arquitectura de Voltaje para aplicaciones de Red y Segunda Vida:**")
            st.markdown("""
            * **Compatibilidad V2G:** Los vehículos con arquitecturas de alta tensión exigen parámetros específicos de acoplamiento front-end en cargadores bidireccionales.
            * **Segunda Vida:** Agrupar celdas retiradas procedentes de un mismo umbral de voltaje simplifica las tareas de reconfiguración de packs para sistemas de almacenamiento estacionario.
            """)

        st.divider()
        st.subheader(f"Cadena de Suministro Real ({periodo_eco})")
        col_b1, col_b2 = st.columns(2)
        
        with col_b1:
            if not df_eco_filtrado.empty:
                quimica_ventas = df_eco_filtrado.groupby('Química')[periodo_eco].sum().reset_index()
                quimica_ventas = quimica_ventas[quimica_ventas['Química'] != 'DESCONOCIDA'].sort_values(by=periodo_eco, ascending=False)
                if not quimica_ventas.empty:
                    fig_quimica = px.pie(quimica_ventas, values=periodo_eco, names='Química', title=f"Química Dominante en {periodo_eco}", hole=0.4)
                    st.plotly_chart(fig_quimica, use_container_width=True)
            
        with col_b2:
            if not df_eco_filtrado.empty:
                fab_ventas = df_eco_filtrado.groupby('Fabricante Batería')[periodo_eco].sum().reset_index()
                fab_ventas = fab_ventas[fab_ventas['Fabricante Batería'] != 'DESCONOCIDO'].sort_values(by=periodo_eco, ascending=True).tail(10) 
                if not fab_ventas.empty:
                    fig_fab = px.bar(fab_ventas, x=periodo_eco, y='Fabricante Batería', orientation='h', text=periodo_eco, title=f"Top Fabricantes en {periodo_eco}")
                    fig_fab.update_traces(marker_color='#8E44AD')
                    fig_fab.update_layout(yaxis_title="", height=450)
                    st.plotly_chart(fig_fab, use_container_width=True)
