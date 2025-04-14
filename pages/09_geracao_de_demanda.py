import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO

# Configura a página para modo wide
st.set_page_config(layout="wide")

# Carrega os dados da planilha
@st.cache_data

def carregar_dados():
    caminho_arquivo = 'datasets/dados_gd.xlsx'
    aba = 'import'
    df = pd.read_excel(caminho_arquivo, sheet_name=aba)

    # Formata colunas de data para dd/mm/yyyy
    for coluna in ['Plantio', 'Colheita']:
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna]).dt.strftime('%d/%m/%Y')

    return df

# Função para exportar para Excel
def converter_para_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtrado')
    return output.getvalue()

# Botão para recarregar os dados
if st.button("🔄 Recarregar Dados"):
    st.cache_data.clear()
    st.success("✅ Dados atualizados com sucesso!")

# Carregando os dados
df = carregar_dados()

# Cria duas colunas com proporção 15% e 85%
col_filtros, col_tabela = st.columns([0.15, 0.85])

with col_filtros:
    st.header("Filtros")

    # Checkboxes diretos com múltipla escolha
    checkbox_colunas = {
        "Macro": "Macro",
        "REC": "REC",
        "Região": "Região",
        "Regional": "Regional",
        "Gerente": "Gerente",
        "Time": "Time",
        "Irrigacao": "Irrigação",
        "Textura do Solo": "Textura do Solo",
        "Fertilidade do Solo": "Fertilidade do Solo",
        "Investimento": "Investimento"
    }
    for coluna, label in checkbox_colunas.items():
        if coluna in df.columns:
            with st.expander(label):
                opcoes = df[coluna].dropna().unique().tolist()
                selecionados = st.multiselect(f"Selecionar {label}", options=opcoes, default=opcoes)
                df = df[df[coluna].isin(selecionados)]

    # Multiselect vazios por padrão
    multiselect_colunas = {
        "nome_estado": "Estado",
        "Cidade": "Cidade",
        "Produtor": "Produtor",
        "Fazenda": "Fazenda",
        "Cultivar": "Cultivar"
    }
    for coluna, label in multiselect_colunas.items():
        if coluna in df.columns:
            with st.expander(label):
                opcoes = df[coluna].dropna().unique().tolist()
                selecionados = st.multiselect(f"Selecionar {label}", options=opcoes)
                if selecionados:
                    df = df[df[coluna].isin(selecionados)]

    # Filtro GM
    if 'GM' in df.columns:
        with st.expander("GM"):
            min_val = int(df['GM'].min())
            max_val = int(df['GM'].max())
            if min_val == max_val:
                st.info(f"Apenas um valor disponível para GM: {min_val}")
            else:
                valor = st.slider(
                    "Selecionar faixa de GM",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),
                    step=1
                )
                df = df[(df['GM'] >= valor[0]) & (df['GM'] <= valor[1])]


    # Filtro Altitude
    if 'altitude' in df.columns:
        with st.expander("Altitude"):
            min_val = int(df['altitude'].min())
            max_val = int(df['altitude'].max())
            if min_val == max_val:
                st.info(f"Apenas um valor disponível para Altitude: {min_val} m")
            else:
                valor = st.slider(
                    "Selecionar faixa de Altitude",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),
                    step=1
                )
                df = df[(df['altitude'] >= valor[0]) & (df['altitude'] <= valor[1])]


# Aplica filtro adicional por coluna numérica (caso alguma_coluna_numerica exista)
if 'alguma_coluna_numerica' in df.columns:
    df_filtrado = df[df['alguma_coluna_numerica'] >= 0.15]
else:
    df_filtrado = df

# Lista para uso interno
colunas_visiveis = [
    "macro", "rec","UF","nome_estado","Cidade", "regiao","Cultivar", "GM","Plantio", "Colheita",
    "Pop Final plts/ha","Umidade",
    "prod_kg_ha_corr", "prod_sc_ha_corr",   
]

#colunas_visiveis = [
#    "Produtor", "Fazenda", "Tipo Teste", "Plantio", "Colheita", "UF", "Cultivar", "Trait", "GM",
#    "Pop Final", "Pop Final plts/ha", "Area", "Umidade", "prod_kg_ha", "prod_kg_ha_corr",
#    "prod_sc_ha_corr", "altitude", "latitude", "longitude", "Irrigacao", "Textura do Solo",
#    "Fertilidade do Solo", "Investimento", "Colaborador", "Time", "Gerente", "macro", "rec",
#   "nome_estado", "regiao"
#]

rotulos_renomear = {
    "Produtor": "Produtor",
    "Fazenda": "Fazenda",
    "Tipo Teste": "Tipo Teste",
    "Plantio": "Plantio",
    "Colheita": "Colheita",
    "UF": "UF",
    "Cultivar": "Cultivar",
    "Trait": "Trait",
    "GM": "GM",
    "Pop Final": "Pop Final",
    "Pop Final plts/ha": "Pop Final plts/ha",
    "Area": "Área",
    "Umidade": "Umidade",
    "prod_kg_ha": "Produtividade kg/ha",
    "prod_kg_ha_corr": "Prod kg/ha",
    "prod_sc_ha_corr": "Prod sc/ha ",
    "altitude": "Altitude",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "Irrigacao": "Irrigação",
    "Textura do Solo": "Textura do Solo",
    "Fertilidade do Solo": "Fertilidade do Solo",
    "Investimento": "Investimento",
    "Colaborador": "Colaborador",
    "Time": "Time",
    "Gerente": "Gerente",
    "macro": "Macro",
    "rec": "REC",
    "nome_estado": "Estado",
    "regiao": "Região"
}

# Aplica colunas visíveis e renomeia colunas
df_exibicao = df_filtrado.copy()
if all(col in df_exibicao.columns for col in colunas_visiveis):
    df_exibicao = df_exibicao[colunas_visiveis].rename(columns=rotulos_renomear)

with col_tabela:
    st.header("Tabela Filtrada")

    # Configuração do AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_exibicao)
    gb.configure_default_column(
        enableRowGroup=True,
        enablePivot=True,
        enableValue=True,
        sortable=True,
        filter=True,
        editable=False,
        resizable=True
    )
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()

    # Estilo do cabeçalho
    custom_css = {
        ".ag-header-cell-text": {
            "font-weight": "bold",
            "color": "black"
        }
    }

    AgGrid(
        df_exibicao,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        height=600,
        custom_css=custom_css,
        allow_unsafe_jscode=True,
        update_mode="SELECTION_CHANGED",
        theme="streamlit"
    )

  


    # Botão de exportação para Excel (após a tabela)
    excel_data = converter_para_excel(df_exibicao)
    st.download_button(
        label="📥 Exportar para Excel",
        data=excel_data,
        file_name="dados_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    
   # RESUMO AGRUPADO POR CULTIVAR
    st.markdown("### 📊 Resumo por Cultivar")

    colunas_resumo = ['Cultivar', 'Umidade', 'prod_kg_ha', 'prod_sc_ha_corr', 'Pop Final plts/ha']
    colunas_presentes = [col for col in colunas_resumo if col in df_filtrado.columns]

    if all(col in df_filtrado.columns for col in colunas_resumo):
        df_resumo = (
            df_filtrado[colunas_resumo]
            .groupby('Cultivar', as_index=False)
            .mean(numeric_only=True)
            .round(2)
            .rename(columns={
                "prod_kg_ha": "Prod kg/ha@13%",
                "prod_sc_ha_corr": "Prod sc/ha@13%"
            })
        )

        # AgGrid para o resumo
        gb_resumo = GridOptionsBuilder.from_dataframe(df_resumo)
        gb_resumo.configure_default_column(
            enableRowGroup=True,
            enablePivot=True,
            enableValue=True,
            sortable=True,
            filter=True,
            editable=False,
            resizable=True
        )
        gb_resumo.configure_grid_options(domLayout='normal')
        grid_options_resumo = gb_resumo.build()

        AgGrid(
            df_resumo,
            gridOptions=grid_options_resumo,
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=True,
            height=400,
            custom_css={
                ".ag-header-cell-text": {
                    "font-weight": "bold",
                    "color": "black"
                }
            },
            allow_unsafe_jscode=True,
            update_mode="SELECTION_CHANGED",
            theme="streamlit"
        )

        # Exportar resumo para Excel
        resumo_excel = converter_para_excel(df_resumo)
        st.download_button(
            label="📥 Exportar Resumo por Cultivar",
            data=resumo_excel,
            file_name="resumo_por_cultivar.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Nem todas as colunas necessárias estão disponíveis para gerar o resumo.")




   

    # 📊 Histograma por faixa de Pop Final
    st.markdown("### 📊 Distribuição de População Final com Produtividade Média")
    import plotly.express as px
    import numpy as np

    if not df_filtrado.empty and "Pop Final plts/ha" in df_filtrado.columns and "prod_sc_ha_corr" in df_filtrado.columns:

        # Limites para slider
        min_pop = int(df_filtrado["Pop Final plts/ha"].min())
        max_pop = int(df_filtrado["Pop Final plts/ha"].max())

        faixa_pop = st.slider(
            "Selecionar faixa de População Final (plts/ha) para exibir no gráfico:",
            min_value=min_pop,
            max_value=max_pop,
            value=(0, 450000),
            step=10000
        )

        df_pop_filtrado = df_filtrado[
            (df_filtrado["Pop Final plts/ha"] >= faixa_pop[0]) &
            (df_filtrado["Pop Final plts/ha"] <= faixa_pop[1])
        ].copy()

        # Bins e categorias
        bin_step = 50000
        bins = list(range(faixa_pop[0], faixa_pop[1] + bin_step, bin_step))
        categorias = pd.cut(df_pop_filtrado["Pop Final plts/ha"], bins=bins)

        # Rotulos customizados
        labels_k = [f"{int(interval.left/1000)}K - {int(interval.right/1000)}K" for interval in categorias.cat.categories]
        df_pop_filtrado["Faixa_Pop_K"] = pd.cut(df_pop_filtrado["Pop Final plts/ha"], bins=bins, labels=labels_k)

        # Agrupamento
        grupo = df_pop_filtrado.groupby("Faixa_Pop_K").agg({
            "Pop Final plts/ha": "count",
            "prod_sc_ha_corr": "mean"
        }).rename(columns={
            "Pop Final plts/ha": "Frequência",
            "prod_sc_ha_corr": "Prod_média"
        }).reset_index()

        # Gráfico
        fig_hist = px.bar(
            grupo,
            x="Faixa_Pop_K",
            y="Frequência",
            text=grupo["Prod_média"].apply(lambda x: f"{x:.1f} sc/ha" if pd.notna(x) else ""),
            labels={"Faixa_Pop_K": "População Final (plts/ha)", "Frequência": "Frequência"},
            title="Distribuição de População Final com Produtividade Média"
        )

        fig_hist.update_traces(
            textposition="outside",
            textfont=dict(size=18, family="Arial Black", color="black")
        )

        fig_hist.update_layout(
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(size=18, family="Arial Black", color="black"),
                title=dict(text="<b>População Final (plts/ha)</b>", font=dict(size=20, family="Arial Black"))
            ),
            yaxis=dict(
                tickfont=dict(size=18, family="Arial Black", color="black"),
                title=dict(text="<b>Frequência</b>", font=dict(size=20, family="Arial Black"))
            ),
            font=dict(size=16, family="Arial Black"),
            height=800
        )

        st.plotly_chart(fig_hist, use_container_width=True)







    

    # Seção de Análise Head to Head entre Cultivares
    st.markdown("---")
    st.markdown("### ⚔️ Análise Head to Head entre Cultivares")
    st.markdown("""
    <small>
    A Análise Head to Head compara o desempenho de dois cultivares em cada local de avaliação. 
    Ela mostra o número de vitórias, derrotas e empates (diferenças entre -1 e 1 sc/ha), 
    ajudando a entender qual cultivar teve melhor performance em diferentes condições.
    </small>
    """, unsafe_allow_html=True)

    if st.button("🔁 Rodar Análise Head to Head"):
        if not df_filtrado.empty:
            df_filtrado = df_filtrado.copy()
            df_filtrado["Local"] = df_filtrado["Fazenda"].astype(str) + "_" + df_filtrado["Cidade"].astype(str)

            df_h2h = df_filtrado[["Local", "Cultivar", "prod_sc_ha_corr", "Pop Final plts/ha", "Umidade"]].dropna()
            df_h2h = df_h2h[df_h2h["prod_sc_ha_corr"] > 0]

            resultados_h2h = []

            for local, grupo in df_h2h.groupby("Local"):
                cultivares = grupo["Cultivar"].unique()
                for head in cultivares:
                    head_row = grupo[grupo["Cultivar"] == head]
                    if head_row.empty:
                        continue

                    prod_head = head_row["prod_sc_ha_corr"].values[0]
                    pop_head = head_row["Pop Final plts/ha"].values[0]
                    umid_head = head_row["Umidade"].values[0]

                    for check in cultivares:
                        if head == check:
                            continue
                        check_row = grupo[grupo["Cultivar"] == check]
                        if check_row.empty:
                            continue

                        prod_check = check_row["prod_sc_ha_corr"].values[0]
                        pop_check = check_row["Pop Final plts/ha"].values[0]
                        umid_check = check_row["Umidade"].values[0]

                        diff = prod_head - prod_check
                        win = int(diff > 1)
                        draw = int(-1 <= diff <= 1)

                        resultados_h2h.append({
                            "Head": head,
                            "Check": check,
                            "Head_Mean": round(prod_head, 1),
                            "Check_Mean": round(prod_check, 1),
                            "Pop_Final_Head": round(pop_head, 0),
                            "Umidade_Head": round(umid_head, 1),
                            "Pop_Final_Check": round(pop_check, 0),
                            "Umidade_Check": round(umid_check, 1),
                            "Difference": round(diff, 1),
                            "Number_of_Win": win,
                            "Is_Draw": draw,
                            "Percentage_of_Win": 100.0 if win else 0.0,
                            "Number_of_Comparison": 1,
                            "Local": local
                        })

            df_resultado_h2h = pd.DataFrame(resultados_h2h)
            st.session_state["df_resultado_h2h"] = df_resultado_h2h
            st.success("✅ Análise concluída com sucesso!")

        else:
            st.warning("⚠️ Dados filtrados estão vazios para executar análise Head to Head.")

        ...

        

    # Exibição interativa da Tabela Head-to-Head
    if "df_resultado_h2h" in st.session_state:
        df_resultado_h2h = st.session_state["df_resultado_h2h"]
        colunas_visiveis = st.session_state.get("colunas_visiveis_h2h", df_resultado_h2h.columns.tolist())

        import numpy as np

        st.markdown("### 🎯 Selecione os cultivares para exibir na Tabela")
        col1, col2 = st.columns(2)
        with col1:
            head_filtrado = st.selectbox("Cultivar Head", sorted(df_resultado_h2h["Head"].unique()), key="head_tabela")
        with col2:
            check_filtrado = st.selectbox("Cultivar Check", sorted(df_resultado_h2h["Check"].unique()), key="check_tabela")

        df_filtrado = df_resultado_h2h[
            (df_resultado_h2h["Head"] == head_filtrado) & (df_resultado_h2h["Check"] == check_filtrado)
        ]

        st.markdown(f"### 📋 Tabela Head to Head: <b>{head_filtrado} x {check_filtrado}</b>", unsafe_allow_html=True)

        if not df_filtrado.empty:
            df_h2h_fmt = df_filtrado[colunas_visiveis].copy()

            from st_aggrid import JsCode

            cell_style_js = JsCode("""
            function(params) {
                let value = params.value;
                let min = 0;
                let max = 100;
                let ratio = (value - min) / (max - min);

                let r, g, b;
                if (ratio < 0.5) {
                    r = 253;
                    g = 98 + ratio * 2 * (200 - 98);
                    b = 94 + ratio * 2 * (15 - 94);
                } else {
                    r = 242 - (ratio - 0.5) * 2 * (242 - 1);
                    g = 200 - (ratio - 0.5) * 2 * (200 - 184);
                    b = 15 + (ratio - 0.5) * 2 * (170 - 15);
                }

                return {
                    'backgroundColor': 'rgb(' + r + ',' + g + ',' + b + ')',
                    'color': 'black',
                    'fontWeight': 'bold',
                    'fontSize': '16px'
                }
            }
            """)

            gb = GridOptionsBuilder.from_dataframe(df_h2h_fmt)
            gb.configure_column("Pop_Final_Head", type=["numericColumn"], valueFormatter="x.toFixed(0)")
            gb.configure_column("Pop_Final_Check", type=["numericColumn"], valueFormatter="x.toFixed(0)")
            gb.configure_column("Umidade_Head", type=["numericColumn"], valueFormatter="x.toFixed(1)")
            gb.configure_column("Umidade_Check", type=["numericColumn"], valueFormatter="x.toFixed(1)")
            gb.configure_column("Head_Mean", type=["numericColumn"], valueFormatter="x.toFixed(1)", cellStyle=cell_style_js)
            gb.configure_column("Check_Mean", type=["numericColumn"], valueFormatter="x.toFixed(1)", cellStyle=cell_style_js)

            for col in df_h2h_fmt.select_dtypes(include=["float"]).columns:
                if col not in ["Pop_Final_Head", "Pop_Final_Check", "Umidade_Head", "Umidade_Check", "Head_Mean", "Check_Mean"]:
                    gb.configure_column(field=col, type=["numericColumn"], valueFormatter="x.toFixed(1)")

            gb.configure_default_column(cellStyle={'fontSize': '14px'})
            gb.configure_grid_options(headerHeight=30)

            custom_css = {
                ".ag-header-cell-label": {
                    "font-weight": "bold",
                    "font-size": "15px",
                    "color": "black"
                }
            }

            AgGrid(
                df_h2h_fmt,
                gridOptions=gb.build(),
                height=800,
                custom_css=custom_css,
                allow_unsafe_jscode=True
            )
        else:
            st.warning("⚠️ Nenhum dado disponível para essa combinação.")

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_resultado_h2h.to_excel(writer, sheet_name="head_to_head", index=False)
        st.download_button(
            label="📅 Baixar Resultado Head to Head",
            data=buffer.getvalue(),
            file_name="resultado_head_to_head.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_filtrado.to_excel(writer, sheet_name="head_to_head_filtrado", index=False)
        
        
        ...

        st.download_button(
            label="📥 Baixar Resultado Filtrado",
            data=buffer.getvalue(),
            file_name=f"head_to_head_{head_filtrado}_vs_{check_filtrado}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown("### 🔹 Selecione os cultivares para comparação Head to Head")
        cultivares_unicos = sorted(df_resultado_h2h["Head"].unique())
        col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

        with col1:
            head_select = st.selectbox("Selecionar Cultivar Head", options=cultivares_unicos, key="head_select")
        with col2:
            st.markdown("<h1 style='text-align: center;'>X</h1>", unsafe_allow_html=True)
        with col3:
            check_select = st.selectbox("Selecionar Cultivar Check", options=cultivares_unicos, key="check_select")

        if head_select and check_select and head_select != check_select:
            df_selecionado = df_resultado_h2h[(df_resultado_h2h["Head"] == head_select) & (df_resultado_h2h["Check"] == check_select)]

            num_locais = df_selecionado["Local"].nunique()
            vitorias = df_selecionado[df_selecionado["Difference"] > 1].shape[0]
            derrotas = df_selecionado[df_selecionado["Difference"] < -1].shape[0]
            empates = df_selecionado[df_selecionado["Difference"].between(-1, 1)].shape[0]

            max_diff = df_selecionado["Difference"].max() if not df_selecionado.empty else 0
            min_diff = df_selecionado["Difference"].min() if not df_selecionado.empty else 0
            media_diff_vitorias = df_selecionado[df_selecionado["Difference"] > 1]["Difference"].mean() or 0
            media_diff_derrotas = df_selecionado[df_selecionado["Difference"] < -1]["Difference"].mean() or 0

            col4, col5, col6, col7 = st.columns(4)

            with col4:
                st.markdown(f"""
                    <div style="background-color:#f2f2f2; padding:15px; border-radius:10px; text-align:center;">
                        <h5 style="font-weight:bold; color:#333;">📍 Número de Locais</h5>
                        <div style="font-size: 20px; font-weight:bold; color:#f2f2f2;">&nbsp;</div>
                        <h2 style="margin: 10px 0; color:#333; font-weight:bold; font-size: 4em;">{num_locais}</h2>
                        <div style="font-size: 20px; font-weight:bold; color:#f2f2f2;">&nbsp;</div>
                    </div>
                """, unsafe_allow_html=True)

            with col5:
                st.markdown(f"""
                    <div style="background-color:#01B8AA80; padding:15px; border-radius:10px; text-align:center;">
                        <h5 style="font-weight:bold; color:#004d47;">✅ Vitórias</h5>
                        <div style="font-size: 20px; font-weight:bold; color:#004d47;">Max: {max_diff:.1f} sc/ha</div>
                        <h2 style="margin: 10px 0; color:#004d47; font-weight:bold; font-size: 4em;">{vitorias}</h2>
                        <div style="font-size: 20px; font-weight:bold; color:#004d47;">Média: {media_diff_vitorias:.1f} sc/ha</div>
                    </div>
                """, unsafe_allow_html=True)

            with col6:
                st.markdown(f"""
                    <div style="background-color:#F2C80F80; padding:15px; border-radius:10px; text-align:center;">
                        <h5 style="font-weight:bold; color:#8a7600;">➖ Empates</h5>
                        <div style="font-size: 20px; font-weight:bold; color:#8a7600;">Entre -1 e 1 sc/ha</div>
                        <h2 style="margin: 10px 0; color:#8a7600; font-weight:bold; font-size: 4em;">{empates}</h2>
                        <div style="font-size: 20px; font-weight:bold; color:#F2C80F80;">&nbsp;</div>
                    </div>
                """, unsafe_allow_html=True)

            with col7:
                st.markdown(f"""
                    <div style="background-color:#FD625E80; padding:15px; border-radius:10px; text-align:center;">
                        <h5 style="font-weight:bold; color:#7c1f1c;">❌ Derrotas</h5>
                        <div style="font-size: 20px; font-weight:bold; color:#7c1f1c;">Min: {min_diff:.1f} sc/ha</div>
                        <h2 style="margin: 10px 0; color:#7c1f1c; font-weight:bold; font-size: 4em;">{derrotas}</h2>
                        <div style="font-size: 20px; font-weight:bold; color:#7c1f1c;">Média: {media_diff_derrotas:.1f} sc/ha</div>
                    </div>
                """, unsafe_allow_html=True)

            col7, col8, col9 = st.columns([1, 2, 1])
            with col8:
                st.markdown("""
                    <div style="background-color: #f9f9f9; padding: 10px; border-radius: 12px; 
                                box-shadow: 0px 2px 5px rgba(0,0,0,0.1); text-align: center;">
                        <h4 style="margin-bottom: 0.5rem;">Resultado Geral do Head</h4>
                """, unsafe_allow_html=True)

                import plotly.graph_objects as go

                fig = go.Figure(data=[go.Pie(
                    labels=["Vitórias", "Empates", "Derrotas"],
                    values=[vitorias, empates, derrotas],
                    marker=dict(colors=["#01B8AA", "#F2C80F", "#FD625E"]),
                    hole=0.6,
                    textinfo='label+percent',
                    textposition='outside',
                    textfont=dict(size=20, color="black", family="Arial Black"),
                )])

                fig.update_layout(
                    margin=dict(t=10, b=60, l=10, r=10),
                    height=330,
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"### <b>📊 Diferença de Produtividade por Local - {head_select} X {check_select}</b>", unsafe_allow_html=True)
            st.markdown("""
            ### 📌 Dica: para melhor visualização dos rótulos, filtre para um número menor de locais.
            """)

            df_selecionado = df_selecionado[
                (df_selecionado["Head_Mean"] > 0) & (df_selecionado["Check_Mean"] > 0)
            ]

            df_selecionado_sorted = df_selecionado.sort_values("Difference")

            fig_diff_local = go.Figure()

            cores_local = df_selecionado_sorted["Difference"].apply(
                lambda x: "#01B8AA" if x > 1 else "#FD625E" if x < -1 else "#F2C80F"
            )

            fig_diff_local.add_trace(go.Bar(
                y=df_selecionado_sorted["Local"],
                x=df_selecionado_sorted["Difference"],
                orientation='h',
                text=df_selecionado_sorted["Difference"].round(1),
                textposition="outside",
                textfont=dict(size=20, family="Arial Black", color="black"),
                marker_color=cores_local
            ))

            fig_diff_local.update_layout(
                title=dict(
                    text=f"<b>📍 Diferença de Produtividade por Local — {head_select} X {check_select}</b>",
                    font=dict(size=20, family="Arial Black", color="black")
                ),
                xaxis=dict(
                    title=dict(text="<b>Diferença (sc/ha)</b>", font=dict(size=20, family="Arial Black", color="black")),
                    tickfont=dict(size=20, family="Arial Black", color="black")
                ),
                yaxis=dict(
                    title=dict(text="<b>Local</b>", font=dict(size=20, family="Arial Black", color="black")),
                    tickfont=dict(size=20, family="Arial Black", color="black")
                ),
                margin=dict(t=40, b=40, l=100, r=40),
                height=600,
                showlegend=False
            )

            st.plotly_chart(fig_diff_local, use_container_width=True)

            ...

            

        # Comparacao Multichecks
        st.markdown("### 🔹 Comparação Head x Múltiplos Checks")
        st.markdown("""
        <small>
        Essa análise permite comparar um cultivar (Head) com vários outros (Checks) ao mesmo tempo. 
        Ela apresenta o percentual de vitórias, produtividade média e a diferença média de performance 
        em relação aos demais cultivares selecionados.
        </small>
        """, unsafe_allow_html=True)

        head_unico = st.selectbox("Cultivar Head", options=cultivares_unicos, key="multi_head")
        opcoes_checks = [c for c in cultivares_unicos if c != head_unico]
        checks_selecionados = st.multiselect("Cultivares Check", options=opcoes_checks, key="multi_checks")

        if head_unico and checks_selecionados:
            df_multi = df_resultado_h2h[
                (df_resultado_h2h["Head"] == head_unico) &
                (df_resultado_h2h["Check"].isin(checks_selecionados))
            ]

            if not df_multi.empty:
                prod_head_media = df_multi["Head_Mean"].mean().round(1)

                st.markdown(f"#### 🎯 Cultivar Head: **{head_unico}** | Produtividade Média: **{prod_head_media} sc/ha**")

                resumo = df_multi.groupby("Check").agg({
                    "Number_of_Win": "sum",
                    "Number_of_Comparison": "sum",
                    "Check_Mean": "mean"
                }).reset_index()

                resumo.rename(columns={
                    "Check": "Cultivar Check",
                    "Number_of_Win": "Vitórias",
                    "Number_of_Comparison": "Num_Locais",
                    "Check_Mean": "Prod_sc_ha_media"
                }, inplace=True)

                resumo["% Vitórias"] = (resumo["Vitórias"] / resumo["Num_Locais"] * 100).round(1)
                resumo["Prod_sc_ha_media"] = resumo["Prod_sc_ha_media"].round(1)
                resumo["Diferença Média"] = (prod_head_media - resumo["Prod_sc_ha_media"]).round(1)

                resumo = resumo[["Cultivar Check", "% Vitórias", "Num_Locais", "Prod_sc_ha_media", "Diferença Média"]]

                col_tabela, col_grafico = st.columns([1.4, 1.6])
                with col_tabela:
                    st.markdown("### 📊 Tabela Comparativa")
                    gb = GridOptionsBuilder.from_dataframe(resumo)
                    gb.configure_default_column(cellStyle={'fontSize': '14px'})
                    gb.configure_grid_options(headerHeight=30)
                    custom_css = {".ag-header-cell-label": {"font-weight": "bold", "font-size": "15px", "color": "black"}}
                    AgGrid(resumo, gridOptions=gb.build(), height=400, custom_css=custom_css)

                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                        resumo.to_excel(writer, sheet_name="comparacao_multi_check", index=False)

                    st.download_button(
                        label="📅 Baixar Comparacao (Excel)",
                        data=buffer.getvalue(),
                        file_name=f"comparacao_{head_unico}_vs_checks.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                with col_grafico:
                    fig_diff = go.Figure()
                    cores_personalizadas = resumo["Diferença Média"].apply(
                        lambda x: "#01B8AA" if x > 1 else "#FD625E" if x < -1 else "#F2C80F"
                    )

                    fig_diff.add_trace(go.Bar(
                        y=resumo["Cultivar Check"],
                        x=resumo["Diferença Média"],
                        orientation='h',
                        text=resumo["Diferença Média"].round(1),
                        textposition="outside",
                        textfont=dict(size=16, family="Arial Black", color="black"),
                        marker_color=cores_personalizadas
                    ))

                    fig_diff.update_layout(
                        title=dict(text="📊 Diferença Média de Produtividade", font=dict(size=20, family="Arial Black")),
                        xaxis=dict(title=dict(text="Diferença Média (sc/ha)", font=dict(size=16)), tickfont=dict(size=14)),
                        yaxis=dict(title=dict(text="Check"), tickfont=dict(size=14)),
                        margin=dict(t=30, b=40, l=60, r=30),
                        height=400,
                        showlegend=False
                    )

                    st.plotly_chart(fig_diff, use_container_width=True)
            else:
                st.info("❓ Nenhuma comparação disponível com os Checks selecionados.")

            

          

            




