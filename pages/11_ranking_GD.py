import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Geração de Demanda", layout="wide")

st.title("📊 Geração de Demanda")
st.markdown("Carregue a base e filtre os dados conforme necessário.")

# 📂 Upload do arquivo Excel
uploaded_file = st.file_uploader("📥 Faça upload da base Excel", type=["xlsx"])

# Inicializa controle de filtros
if "aplicar_filtros" not in st.session_state:
    st.session_state.aplicar_filtros = False
if "resetar" not in st.session_state:
    st.session_state.resetar = False

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    st.success("✅ Base carregada com sucesso!")

    # 🧼 Renomeia colunas
    df = df.rename(columns={
        "produtor": "Produtor",
        "cidade": "Cidade",
        "estado": "Estado",
        "estado_sigla": "UF",
        "fazenda": "Fazenda",
        "rec": "Rec",
        "macro": "Macro",
        "cultivar": "Cultivar",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "plantio": "Plantio",
        "colheita": "Colheita",
        "pop_final_pls": "População",
        "prod_kg_ha": "Prod (kg/ha)",
        "produtividade": "Prod (sc/ha)",
        "gm": "GM"
    })
    #
    # 🗓️ Converte datas para string formatada
    for col in ["Plantio", "Colheita"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y")

    col_filtros, col_tabela = st.columns([1.5, 8.5])

    with col_filtros:
        st.markdown("### 🎛️ Filtros")

        filtros_checkbox = {
            "Macro": "Macro",
            "Rec": "Rec",
            "Estado": "Estado",
            "Cidade": "Cidade",
            "Produtor": "Produtor",
            "Cultivar": "Cultivar"
        }

        filtros_selecionados = {}

        for coluna, label in filtros_checkbox.items():
            if coluna in df.columns:
                with st.expander(f"Filtrar por {label}"):
                    opcoes = sorted(df[coluna].dropna().unique())
                    selecionados = []
                    for op in opcoes:
                        key = f"{coluna}_{op}"
                        if st.session_state.resetar:
                            st.session_state[key] = False
                        if st.checkbox(str(op), key=key):
                            selecionados.append(op)
                    if selecionados:
                        filtros_selecionados[coluna] = selecionados

        # 🎚️ Filtro de GM como slider
        if "GM" in df.columns:
            valores_gm = df["GM"].dropna().unique()
            if len(valores_gm) > 0:
                gm_min, gm_max = int(df["GM"].min()), int(df["GM"].max())
                if gm_min < gm_max:
                    if st.session_state.resetar:
                        st.session_state["gm_range"] = (gm_min, gm_max)
                    intervalo_gm = st.slider(
                        "Selecionar faixa de GM:",
                        min_value=gm_min,
                        max_value=gm_max,
                        value=st.session_state.get("gm_range", (gm_min, gm_max)),
                        step=1,
                        key="gm_range"
                    )
                    filtros_selecionados["GM"] = list(range(intervalo_gm[0], intervalo_gm[1]+1))
                else:
                    st.info(f"Apenas um valor de GM disponível: **{gm_min}**")

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Aplicar Filtros"):
                st.session_state.aplicar_filtros = True
                st.session_state.resetar = False

        with col2:
            if st.button("🔄 Resetar Filtros"):
                st.session_state.aplicar_filtros = True
                st.session_state.resetar = True

    with col_tabela:
        st.markdown("### 📄 Dados Filtrados")

        df_filtrado = df.copy()

        # Aplica os filtros
        if st.session_state.aplicar_filtros:
            for coluna, selecionados in filtros_selecionados.items():
                df_filtrado = df_filtrado[df_filtrado[coluna].isin(selecionados)]

        colunas_visiveis = [
            "Produtor", "Fazenda", "Cidade", "Estado", "UF", "Macro", "Rec",
            "Cultivar", "GM", "Plantio", "Colheita", "População", "Prod (kg/ha)", "Prod (sc/ha)",
            "Latitude", "Longitude"
        ]
        colunas_visiveis = [col for col in colunas_visiveis if col in df_filtrado.columns]

        df_fmt = df_filtrado[colunas_visiveis].copy()
        df_fmt = df_fmt.sort_values(by="Prod (sc/ha)", ascending=False)

        st.dataframe(df_fmt.reset_index(drop=True), use_container_width=True)

        # 💾 Exportar Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_fmt.to_excel(writer, index=False, sheet_name='DemandaFiltrada')

        st.download_button(
            label="📥 Baixar Dados Filtrados",
            data=output.getvalue(),
            file_name="demanda_filtrada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 🔄 Produção por Local
        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

        st.markdown("### 📊 Produtividade por Local")

        try:
            # Gera a pivot
            df_pivot = pd.pivot_table(
                df_fmt,
                index=["Produtor", "Fazenda"],
                columns="Cultivar",
                values="Prod (sc/ha)",
                aggfunc="mean"
            ).reset_index()

            # Cultivares ordenados
            colunas_cultivares = sorted([col for col in df_pivot.columns if col not in ["Produtor", "Fazenda"]])

            # Estatísticas por linha
            df_pivot["Prod Mín (sc/ha)"] = df_pivot[colunas_cultivares].min(axis=1)
            df_pivot["Prod Máx (sc/ha)"] = df_pivot[colunas_cultivares].max(axis=1)
            df_pivot["Prod Média (sc/ha)"] = df_pivot[colunas_cultivares].mean(axis=1)

            # Reorganiza colunas
            colunas_final = ["Produtor", "Fazenda", "Prod Mín (sc/ha)", "Prod Máx (sc/ha)", "Prod Média (sc/ha)"] + colunas_cultivares
            df_pivot = df_pivot[colunas_final]

            from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

            # 🧠 Estilo condicional para colunas dos cultivares
            cor_cultivar = JsCode("""
            function(params) {
                if (params.value === null || params.value === undefined) return '';
                const valor = parseFloat(params.value);
                let cor = '';
                if (valor < 40) cor = '#ffcccc';
                else if (valor < 55) cor = '#fff2cc';
                else if (valor < 65) cor = '#d9ead3';
                else cor = '#b6d7a8';
                return {'backgroundColor': cor, 'color': 'black'};
            }
            """)

            # ⚙️ Builder
            gb = GridOptionsBuilder.from_dataframe(df_pivot)

            gb.configure_default_column(
                cellStyle={'fontSize': '14px', 'color': 'black'},
                resizable=True,
                sortable=True,
                filter=True
            )

            # Aplica estilo às colunas das cultivares
            for col in colunas_cultivares:
                gb.configure_column(col, cellStyle=cor_cultivar, type=["numericColumn"], valueFormatter="x.toFixed(1)")

            # Fixa as primeiras colunas
            gb.configure_column("Produtor", pinned="left")
            gb.configure_column("Fazenda", pinned="left")

            # 💅 CSS para cabeçalho negrito e preto
            custom_css = {
                ".ag-header-cell-label": {
                    "font-weight": "bold",
                    "color": "black"
                }
            }

            # 🚀 Renderiza AgGrid
            AgGrid(
                df_pivot,
                gridOptions=gb.build(),
                enable_enterprise_modules=True,
                height=500,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,
                autoSizeColumns=True,
                custom_css=custom_css
            )




        except Exception as e:
            st.warning(f"❌ Erro ao gerar tabela pivotada com AgGrid: {e}")




else:
    st.info("⚠️ Faça upload de um arquivo `.xlsx` para começar.")
