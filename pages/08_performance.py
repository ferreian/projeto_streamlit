import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder
import io

st.title("📊 Performance dos materiais")
st.markdown(
    "Nesta página, você pode visualizar a performance dos materiais avaliados em diferentes localidades, comparando seus resultados com a média geral,"\
    " a média específica do local e a média das melhores testemunhas."
)

if "merged_dataframes" in st.session_state:
    df_av7 = st.session_state["merged_dataframes"].get("av7TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")

    if df_av7 is not None and not df_av7.empty:
        st.success("✅ Dados carregados com sucesso!")

        df_final_av7 = df_av7[~df_av7["displayName"].isin(["raullanconi", "stine"])].copy()

        if "numeroLinhas" in df_final_av7.columns and "comprimentoLinha" in df_final_av7.columns:
            df_final_av7["areaParcela"] = df_final_av7["numeroLinhas"] * df_final_av7["comprimentoLinha"] * 0.5

        colunas_plantas = ["numeroPlantas10Metros1a", "numeroPlantas10Metros2a", "numeroPlantas10Metros3a", "numeroPlantas10Metros4a"]
        if all(col in df_final_av7.columns for col in colunas_plantas):
            df_final_av7["numeroPlantasMedio10m"] = df_final_av7[colunas_plantas].replace(0, pd.NA).mean(axis=1, skipna=True)
            df_final_av7["Pop_Final"] = (20000 * df_final_av7["numeroPlantasMedio10m"]) / 10

        if "numeroPlantasMedio10m" in df_final_av7.columns:
            df_final_av7["popMediaFinal"] = (10000 / 0.5) * (df_final_av7["numeroPlantasMedio10m"] / 10)

        if all(col in df_final_av7.columns for col in ["pesoParcela", "umidadeParcela", "areaParcela"]):
            df_final_av7["producaoCorrigida"] = (
                (df_final_av7["pesoParcela"] * (100 - df_final_av7["umidadeParcela"]) / 87) * (10000 / df_final_av7["areaParcela"])
            ).astype(float).round(1)

        if "producaoCorrigida" in df_final_av7.columns:
            df_final_av7["producaoCorrigidaSc"] = (df_final_av7["producaoCorrigida"] / 60).astype(float).round(1)

        if all(col in df_final_av7.columns for col in ["pesoMilGraos", "umidadeAmostraPesoMilGraos"]):
            df_final_av7["PMG_corrigido"] = (
                df_final_av7["pesoMilGraos"] * ((100 - df_final_av7["umidadeAmostraPesoMilGraos"]) / 87)
            ).astype(float).round(1)

        if all(col in df_final_av7.columns for col in ["fazendaRef", "indexTratamento"]):
            df_final_av7["ChaveFaixa"] = df_final_av7["fazendaRef"].astype(str) + "_" + df_final_av7["indexTratamento"].astype(str)

        for col in ["dataPlantio", "dataColheita"]:
            if col in df_final_av7.columns:
                df_final_av7[col] = pd.to_datetime(df_final_av7[col], origin="unix", unit="s").dt.strftime("%d/%m/%Y")

        # ================= Cálculo de Métricas ===========================
        df_metricas = df_final_av7.copy()

        # Limpeza da coluna de produtividade
        df_metricas["producaoCorrigidaSc"] = pd.to_numeric(df_metricas["producaoCorrigidaSc"], errors="coerce")
        df_metricas["producaoCorrigidaSc"] = df_metricas["producaoCorrigidaSc"].replace([0, np.inf, -np.inf], np.nan)

        # 🎯 Média Geral
        media_geral = df_metricas["producaoCorrigidaSc"].dropna().mean()

        # 🎯 Média por Local (fazendaRef)
        medias_por_local = df_metricas.groupby("fazendaRef")["producaoCorrigidaSc"].mean().reset_index()
        medias_por_local.rename(columns={"producaoCorrigidaSc": "Média Local (sc/ha)"}, inplace=True)

        # 🔢 Input para número de Top Cultivares
        top_n = st.number_input("Selecione o número de cultivares para média TOP:", min_value=1, max_value=20, value=5, step=1)

        # 🎯 Média Top X por Local
        top_medias = (
            df_metricas
            .sort_values(by=["fazendaRef", "producaoCorrigidaSc"], ascending=[True, False])
            .groupby("fazendaRef")
            .head(top_n)
            .groupby("fazendaRef")["producaoCorrigidaSc"]
            .mean()
            .reset_index()
            .rename(columns={"producaoCorrigidaSc": "Média Top (sc/ha)"})
        )

        # Merge das métricas no DataFrame principal
        df_final_av7 = df_final_av7.merge(medias_por_local, on="fazendaRef", how="left")
        df_final_av7 = df_final_av7.merge(top_medias, on="fazendaRef", how="left")
        df_final_av7["Média Geral (sc/ha)"] = round(media_geral, 1)

        # Arredondamento das novas colunas
        df_final_av7["Média Local (sc/ha)"] = df_final_av7["Média Local (sc/ha)"].round(1)
        df_final_av7["Média Top (sc/ha)"] = df_final_av7["Média Top (sc/ha)"].round(1)




        # ============= Renomeia colunas depois de adicionar as métricas =============
        colunas_renomeadas = {
            "nomeFazenda": "Fazenda",
            "nomeProdutor": "Produtor",
            "regional": "Microrregiao",
            "nomeCidade": "Cidade",
            "codigoEstado": "Estado",
            "nomeEstado": "UF",
            "dataPlantio": "Plantio",
            "dataColheita": "Colheita",
            "tipoTeste": "Teste",
            "nome": "Cultivar",
            "gm": "GM",
            "populacao": "População",	
            "indexTratamento": "Index",
            "areaParcela": "Área Parcela",
            "numeroPlantasMedio10m": "plts_10m",
            "Pop_Final": "Pop_Final",
            "umidadeParcela": "Umidade (%)",
            "producaoCorrigida": "prod_kg_ha",
            "producaoCorrigidaSc": "prod_sc_ha",
            "PMG_corrigido": "PMG",
            "displayName": "DTC",
            "cidadeRef": "CidadeRef",
            "fazendaRef": "FazendaRef",
            "ChaveFaixa": "ChaveFaixa"
        }

        df_final_av7 = df_final_av7.rename(columns=colunas_renomeadas)

        # ✅ Agora as colunas renomeadas + métricas aparecem corretamente
        colunas_finais = list(colunas_renomeadas.values()) + ["Média Local (sc/ha)", "Média Top (sc/ha)", "Média Geral (sc/ha)"]

        df_final_av7 = df_final_av7[[col for col in colunas_finais if col in df_final_av7.columns]]


        # ================= Ajustes e limpeza final =======================
        if "df_final_av7_original" not in st.session_state:
            st.session_state["df_final_av7_original"] = df_final_av7.copy()

        if "Produtor" in df_final_av7.columns:
            df_final_av7["Produtor"] = df_final_av7["Produtor"].astype(str).str.upper()
        if "Fazenda" in df_final_av7.columns:
            df_final_av7["Fazenda"] = df_final_av7["Fazenda"].astype(str).str.upper()

        if "Cultivar" in df_final_av7.columns:
            df_final_av7["Cultivar"] = df_final_av7["Cultivar"].replace({
                "B�NUS IPRO": "BÔNUS IPRO",
                "DOM�NIO IPRO": "DOMÍNIO IPRO",
                "F�RIA CE": "FÚRIA CE",
                "V�NUS CE": "VÊNUS CE",
                "GH 2383 IPRO": "GH 2483 IPRO",
            })

        st.session_state["df_final_av7"] = df_final_av7

        # Colunas visíveis na tabela
        colunas_visiveis = [
            "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index", "populacao", "GM",
            "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
            "prod_kg_ha", "prod_sc_ha", "PMG",
            "Média Local (sc/ha)", "Média Geral (sc/ha)"
        ]


        col_filtros, col_tabela = st.columns([1.5, 8.5])
        
        # 🔁 Correção dos nomes da coluna Cultivar (antes dos filtros)
        if "Cultivar" in df_final_av7.columns:
            df_final_av7["Cultivar"] = df_final_av7["Cultivar"].replace({
                "B�NUS IPRO": "BÔNUS IPRO",
                "DOM�NIO IPRO": "DOMÍNIO IPRO",
                "F�RIA CE": "FÚRIA CE",
                "V�NUS CE": "VÊNUS CE",
                "GH 2383 IPRO": "GH 2483 IPRO"
            })

        # 🔍 Filtra somente onde o tipo de teste é "Faixa"
        df_final_av7 = df_final_av7[df_final_av7["Teste"] == "Faixa"]


        with col_filtros:
            st.markdown("### 🎧 Filtros")

            filtros = {
                "Microrregiao": "Microrregião",
                "Estado": "Estado",
                "Cidade": "Cidade",
                "Fazenda": "Fazenda",
                "Cultivar": "Cultivar",
                # "Teste": "Teste",  <-- removido
            }

            for coluna, label in filtros.items():
                if coluna in df_final_av7.columns:
                    with st.expander(label):
                        opcoes = sorted(df_final_av7[coluna].dropna().unique())
                        selecionados = [
                            op for op in opcoes if st.checkbox(op, key=f"{coluna}_{op}", value=False)
                        ]
                        if selecionados:
                            df_final_av7 = df_final_av7[df_final_av7[coluna].isin(selecionados)]

            if "GM" in df_final_av7.columns:
                gm_min = int(df_final_av7["GM"].min())
                gm_max = int(df_final_av7["GM"].max())
                if gm_min < gm_max:
                    gm_range = st.slider("Intervalo de GM", gm_min, gm_max, (gm_min, gm_max), step=1)
                    df_final_av7 = df_final_av7[df_final_av7["GM"].between(gm_range[0], gm_range[1])]
                else:
                    st.info(f"Apenas um valor de GM disponível: {gm_min}")       
            

            
        #
        with col_tabela:
            st.markdown("### 📋 Tabela Informações de Produção")

            # 🔹 TABELA NORMAL
            
            colunas_visiveis = [
                "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index", "populacao", "GM",
                "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
                "prod_kg_ha", "prod_sc_ha", "PMG",
                "Média Local (sc/ha)", "Média Top (sc/ha)", "Média Geral (sc/ha)"
            ]

            df_visualizacao = df_final_av7[[col for col in colunas_visiveis if col in df_final_av7.columns]]

            gb = GridOptionsBuilder.from_dataframe(df_visualizacao)
            for col in df_visualizacao.select_dtypes(include=["float"]).columns:
                gb.configure_column(field=col, type=["numericColumn"], valueFormatter="x.toFixed(1)")
            gb.configure_default_column(cellStyle={'fontSize': '14px'})
            gb.configure_grid_options(headerHeight=30)

            AgGrid(
                df_visualizacao,
                gridOptions=gb.build(),
                height=500,
                custom_css={
                    ".ag-header-cell-label": {
                        "font-weight": "bold",
                        "font-size": "15px",
                        "color": "black"
                    }
                }
            )

            # Exportação da Tabela Detalhada
            output_normal = io.BytesIO()
            with pd.ExcelWriter(output_normal, engine='xlsxwriter') as writer:
                df_visualizacao.to_excel(writer, index=False, sheet_name="faixa_detalhada")
            st.download_button(
                label="📥 Baixar Tabela Detalhada",
                data=output_normal.getvalue(),
                file_name="tabela_detalhada.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 🔹 TABELA PIVOTADA
            st.markdown("#### 📋 Tabela Performance dos Materiais")

            colunas_pivot = [
                "Cidade", "Cultivar", "Index", "GM",
                "prod_sc_ha", "Média Geral (sc/ha)", "Média Local (sc/ha)", "Média Top (sc/ha)"
            ]
            df_pivot = df_final_av7[colunas_pivot].copy()

            # 🔁 Derrete as métricas (sem Umidade)
            df_melted = pd.melt(
                df_pivot,
                id_vars=["Cultivar", "Index", "GM", "Cidade"],
                value_vars=["prod_sc_ha", "Média Geral (sc/ha)", "Média Local (sc/ha)", "Média Top (sc/ha)"],
                var_name="Métrica",
                value_name="Valor"
            )

            # 📊 Pivot com Métrica nas linhas e Cidades nas colunas
            df_pivotado = df_melted.pivot_table(
                index=["Cultivar", "Index", "GM", "Métrica"],
                columns="Cidade",
                values="Valor",
                aggfunc="mean"
            ).reset_index()

            # ✅ Estilo para destacar linha "prod_sc_ha"
            df_pivotado["EstiloLinha"] = df_pivotado["Métrica"].apply(
                lambda x: "destacar" if x == "prod_sc_ha" else "normal"
            )

            from st_aggrid import JsCode
            row_style = JsCode("""
            function(params) {
                if (params.data.EstiloLinha === 'destacar') {
                    return {
                        'fontWeight': 'bold',
                        'backgroundColor': '#f0f0f0'
                    }
                }
                return {};
            }
            """)

            gb = GridOptionsBuilder.from_dataframe(df_pivotado.drop(columns=["EstiloLinha"]))
            for col in df_pivotado.select_dtypes(include=["float"]).columns:
                gb.configure_column(col, type=["numericColumn"], valueFormatter="x.toFixed(1)")
            gb.configure_default_column(cellStyle={'fontSize': '14px'})
            gb.configure_grid_options(headerHeight=30)

            AgGrid(
                df_pivotado,
                gridOptions=gb.build(),
                height=500,
                custom_css={
                    ".ag-header-cell-label": {
                        "font-weight": "bold",
                        "font-size": "15px",
                        "color": "black"
                    }
                },
                getRowStyle=row_style,
                allow_unsafe_jscode=True
            )

            # Exportação da Tabela Pivotada
            output_pivot = io.BytesIO()
            with pd.ExcelWriter(output_pivot, engine='xlsxwriter') as writer:
                df_pivotado.drop(columns=["EstiloLinha"]).to_excel(writer, index=False, sheet_name="faixa_pivotada")

            st.download_button(
                label="📥 Baixar Tabela Pivotada",
                data=output_pivot.getvalue(),
                file_name="tabela_pivotada.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )








            






            





