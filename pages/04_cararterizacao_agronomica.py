import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.title("📊 Caracterização Agronômica")
st.markdown("Explore os dados de caracterização agronômica nas faixas avaliadas. Aplique filtros para visualizar os dados conforme necessário.")

# ✅ Verifica se df_av5 está carregado
if "merged_dataframes" in st.session_state:
    df_av5 = st.session_state["merged_dataframes"].get("av5TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")

    if df_av5 is not None and not df_av5.empty:
        df_caract = df_av5.copy()

        # Renomeia colunas principais (pode ajustar conforme nomes reais da base AV5)
        df_caract = df_caract.rename(columns={
            "nomeFazenda": "Fazenda",
            "nomeProdutor": "Produtor",
            "codigoEstado": "Estado",
            "nomeEstado": "UF",
            "nomeCidade": "Cidade",
            "regional": "Microrregiao",
            "tipoTeste": "Teste",
            "indexTratamento": "Index",
            "gm": "GM",
            "nome": "Cultivar",
            "displayName": "DTC"
        })

        df_caract = df_caract[df_caract["Teste"] == "Faixa"]

        df_caract["Produtor"] = df_caract["Produtor"].astype(str).str.upper()
        df_caract["Fazenda"] = df_caract["Fazenda"].astype(str).str.upper()

        # 🛠️ Substituições nas cultivares
        substituicoes = {
            "B�NUS IPRO": "BÔNUS IPRO",
            "DOM�NIO IPRO": "DOMÍNIO IPRO",
            "F�RIA CE": "FÚRIA CE",
            "V�NUS CE": "VÊNUS CE",
            "GH 2383 IPRO": "GH 2483 IPRO"
        }

        if "Cultivar" in df_caract.columns:
            df_caract["Cultivar"] = df_caract["Cultivar"].replace(substituicoes)

        # 🔍 Layout com filtros
        col_filtros, col_tabela = st.columns([1.5, 8.5])

        with col_filtros:
            st.markdown("### 🎧 Filtros")

            filtros = {
                "Microrregiao": "Microrregião",
                "Estado": "Estado",
                "Cidade": "Cidade",
                "Fazenda": "Fazenda",
                "Cultivar": "Cultivar"
            }

            # Filtros com expander
            for coluna, label in filtros.items():
                if coluna in df_caract.columns:
                    with st.expander(label):
                        opcoes = sorted(df_caract[coluna].dropna().unique())
                        selecionados = []
                        for op in opcoes:
                            op_str = str(op)
                            if st.checkbox(op_str, key=f"{coluna}_caract_{op_str}", value=False):
                                selecionados.append(op)
                        if selecionados:
                            df_caract = df_caract[df_caract[coluna].isin(selecionados)]

            # Slider de GM por último (fora do expander)
            if "GM" in df_caract.columns:
                gm_min = int(df_caract["GM"].min())
                gm_max = int(df_caract["GM"].max())

                
                if gm_min < gm_max:
                    gm_range = st.slider(
                        "Selecione o intervalo de GM",
                        min_value=gm_min,
                        max_value=gm_max,
                        value=(gm_min, gm_max),
                        step=1
                    )
                    df_caract = df_caract[df_caract["GM"].between(gm_range[0], gm_range[1])]
                else:
                    st.info(f"Grupo de Maturação disponível: **{gm_min}**")





        

        
        # 📊 Tabela
        with col_tabela:
            colunas_principais = [
                "Produtor", "Fazenda", "UF", "Estado", "Cidade", "Microrregiao",
                "Cultivar", "GM", "Index"
            ]

            # 💡 Dicionário com colunas para cálculo de média
            grupos_media = {
                "RV_media": [f"planta{i}NumeroRamosVegetativos" for i in range(1, 6)],
                "RR_media": [f"planta{i}NumeroRamosReprodutivos" for i in range(1, 6)],
                "NV_TS_medio": [f"planta{i}NumeroVagensTercoSuperior" for i in range(1, 6)],
                "NV_TM_media": [f"planta{i}NumeroVagensTercoMedio" for i in range(1, 6)],
                "NV_TI_media": [f"planta{i}NumeroVagensTercoInferior" for i in range(1, 6)],
                "NV_TS_1G": [f"planta{i}NumGraoVagemTS1" for i in range(1, 6)],
                "NV_TS_2G": [f"planta{i}NumGraoVagemTS2" for i in range(1, 6)],
                "NV_TS_3G": [f"planta{i}NumGraoVagemTS3" for i in range(1, 6)],
                "NV_TS_4G": [f"planta{i}NumGraoVagemTS4" for i in range(1, 6)],
                "NV_TM_1G": [f"planta{i}NumGraoVagemTM1" for i in range(1, 6)],
                "NV_TM_2G": [f"planta{i}NumGraoVagemTM2" for i in range(1, 6)],
                "NV_TM_3G": [f"planta{i}NumGraoVagemTM3" for i in range(1, 6)],
                "NV_TM_4G": [f"planta{i}NumGraoVagemTM4" for i in range(1, 6)],
                "NV_TI_1G": [f"planta{i}NumGraoVagemTI1" for i in range(1, 6)],
                "NV_TI_2G": [f"planta{i}NumGraoVagemTI2" for i in range(1, 6)],
                "NV_TI_3G": [f"planta{i}NumGraoVagemTI3" for i in range(1, 6)],
                "NV_TI_4G": [f"planta{i}NumGraoVagemTI4" for i in range(1, 6)],
            }

            # 🔄 Calcula as médias
            import numpy as np

            # 🔄 Calcula as médias (substitui 0 por np.nan para ignorar nos cálculos)
            for nome_col, colunas in grupos_media.items():
                df_caract[nome_col] = df_caract[colunas].replace(0, np.nan).astype(float).mean(axis=1).round(2)

            # ➕ Colunas somadas (vagens)
            df_caract["NV_media"] = (
                df_caract[["NV_TS_medio", "NV_TM_media", "NV_TI_media"]].replace(0, np.nan).astype(float).sum(axis=1)
            ).round(2)

            df_caract["NV_1G"] = (
                df_caract[["NV_TS_1G", "NV_TM_1G", "NV_TI_1G"]].replace(0, np.nan).astype(float).sum(axis=1)
            ).round(2)
            df_caract["NV_2G"] = (
                df_caract[["NV_TS_2G", "NV_TM_2G", "NV_TI_2G"]].replace(0, np.nan).astype(float).sum(axis=1)
            ).round(2)
            df_caract["NV_3G"] = (
                df_caract[["NV_TS_3G", "NV_TM_3G", "NV_TI_3G"]].replace(0, np.nan).astype(float).sum(axis=1)
            ).round(2)
            df_caract["NV_4G"] = (
                df_caract[["NV_TS_4G", "NV_TM_4G", "NV_TI_4G"]].replace(0, np.nan).astype(float).sum(axis=1)
            ).round(2)

            # ➕ Percentuais (com proteção contra divisão por zero/nulo)
            df_caract["NV_TS_perc"] = df_caract.apply(
                lambda row: round((row["NV_TS_medio"] / row["NV_media"]) * 100, 2) if pd.notnull(row["NV_media"]) and row["NV_media"] > 0 else None,
                axis=1
            )
            df_caract["NV_TM_perc"] = df_caract.apply(
                lambda row: round((row["NV_TM_media"] / row["NV_media"]) * 100, 2) if pd.notnull(row["NV_media"]) and row["NV_media"] > 0 else None,
                axis=1
            )
            df_caract["NV_TI_perc"] = df_caract.apply(
                lambda row: round((row["NV_TI_media"] / row["NV_media"]) * 100, 2) if pd.notnull(row["NV_media"]) and row["NV_media"] > 0 else None,
                axis=1
            )


            # ➕ Percentuais com proteção contra divisão por zero/nulo
            df_caract["NV_TS_perc"] = df_caract.apply(
                lambda row: round((row["NV_TS_medio"] / row["NV_media"]) * 100, 2) if row["NV_media"] and row["NV_media"] > 0 else None,
                axis=1
            )
            df_caract["NV_TM_perc"] = df_caract.apply(
                lambda row: round((row["NV_TM_media"] / row["NV_media"]) * 100, 2) if row["NV_media"] and row["NV_media"] > 0 else None,
                axis=1
            )
            df_caract["NV_TI_perc"] = df_caract.apply(
                lambda row: round((row["NV_TI_media"] / row["NV_media"]) * 100, 2) if row["NV_media"] and row["NV_media"] > 0 else None,
                axis=1
            )


            # ➕ Percentuais
            df_caract["NV_TS_perc"] = ((df_caract["NV_TS_medio"] / df_caract["NV_media"]) * 100).round(2)
            df_caract["NV_TM_perc"] = ((df_caract["NV_TM_media"] / df_caract["NV_media"]) * 100).round(2)
            df_caract["NV_TI_perc"] = ((df_caract["NV_TI_media"] / df_caract["NV_media"]) * 100).round(2)

            # 📋 Tabela
            colunas_visiveis = colunas_principais + [
                "RV_media", "RR_media",
                "NV_TS_medio", "NV_TM_media", "NV_TI_media", "NV_media",
                "NV_TS_1G", "NV_TS_2G", "NV_TS_3G", "NV_TS_4G",
                "NV_TM_1G", "NV_TM_2G", "NV_TM_3G", "NV_TM_4G",
                "NV_TI_1G", "NV_TI_2G", "NV_TI_3G", "NV_TI_4G",
                "NV_1G", "NV_2G", "NV_3G", "NV_4G",
                "NV_TS_perc", "NV_TM_perc", "NV_TI_perc"
            ]

            colunas_visiveis = [col for col in colunas_visiveis if col in df_caract.columns]

            st.markdown("### 📋 Tabela de Caracterização Agronômica")
            #st.dataframe(df_caract[colunas_visiveis], use_container_width=True)

            from st_aggrid import AgGrid, GridOptionsBuilder

            

            df_fmt_caract = df_caract[colunas_visiveis].copy()

            # Cria o builder com nome único
            gb_caract = GridOptionsBuilder.from_dataframe(df_fmt_caract)

            # Formata colunas float com 1 casa decimal
            colunas_float = df_fmt_caract.select_dtypes(include=["float", "float64"]).columns
            for col in colunas_float:
                gb_caract.configure_column(field=col, type=["numericColumn"], valueFormatter="x.toFixed(1)")

            # Fonte e cabeçalho
            gb_caract.configure_default_column(cellStyle={'fontSize': '14px'})
            gb_caract.configure_grid_options(headerHeight=30)

            # Estilo do cabeçalho
            custom_css = {
                ".ag-header-cell-label": {
                    "font-weight": "bold",
                    "font-size": "15px",
                    "color": "black"
                }
            }

            # Exibe com AgGrid
            AgGrid(
                df_fmt_caract,
                gridOptions=gb_caract.build(),
                height=500,
                custom_css=custom_css,
                use_container_width=True
            )


            # ====================== 📊 Resumo por Cultivar – Número de Vagens ======================
            import io
            import numpy as np
            import pandas as pd
            from st_aggrid import AgGrid, GridOptionsBuilder

            st.markdown("### 📊 Resumo de Caracterização por Cultivar (Número de Vagens por Planta)")

            # Substitui 0 por NaN
            colunas_vagens = ["NV_TS_medio", "NV_TM_media", "NV_TI_media"]
            df_caract[colunas_vagens] = df_caract[colunas_vagens].replace(0, np.nan)

            # Agrupa e calcula a média
            df_resumo_vagens = df_caract.groupby("Cultivar").agg(
                GM=("GM", "first"),
                **{col: (col, "mean") for col in colunas_vagens}
            ).reset_index()

            # Soma dos terços = total por planta
            df_resumo_vagens["NV_total"] = (
                df_resumo_vagens["NV_TS_medio"] +
                df_resumo_vagens["NV_TM_media"] +
                df_resumo_vagens["NV_TI_media"]
            ).round(2)

            # Percentuais (%)
            df_resumo_vagens["NV_TS_perc"] = df_resumo_vagens.apply(
                lambda row: round((row["NV_TS_medio"] / row["NV_total"]) * 100, 2)
                if pd.notnull(row["NV_total"]) and row["NV_total"] > 0 else None,
                axis=1
            )
            df_resumo_vagens["NV_TM_perc"] = df_resumo_vagens.apply(
                lambda row: round((row["NV_TM_media"] / row["NV_total"]) * 100, 2)
                if pd.notnull(row["NV_total"]) and row["NV_total"] > 0 else None,
                axis=1
            )
            df_resumo_vagens["NV_TI_perc"] = df_resumo_vagens.apply(
                lambda row: round((row["NV_TI_media"] / row["NV_total"]) * 100, 2)
                if pd.notnull(row["NV_total"]) and row["NV_total"] > 0 else None,
                axis=1
            )

            # Renomeia indicadores
            renomear = {
                "NV_TS_medio": "NV_TS",
                "NV_TM_media": "NV_TM",
                "NV_TI_media": "NV_TI"
            }
            df_resumo_vagens = df_resumo_vagens.rename(columns=renomear)

            # 🔄 Pivot: indicadores como linhas
            df_vagens_long = df_resumo_vagens.melt(
                id_vars=["Cultivar"],
                value_vars=[
                    "NV_TS", "NV_TS_perc",
                    "NV_TM", "NV_TM_perc",
                    "NV_TI", "NV_TI_perc",
                    "NV_total"
                ],
                var_name="Indicador",
                value_name="Valor"
            )

            # Pivot final
            df_vagens_pivot = df_vagens_long.pivot_table(
                index="Indicador",
                columns="Cultivar",
                values="Valor"
            ).reindex([
                "NV_TS", "NV_TS_perc",
                "NV_TM", "NV_TM_perc",
                "NV_TI", "NV_TI_perc",
                "NV_total"
            ]).round(1).reset_index()

            # 🎨 Estilo customizado no AgGrid
            gb = GridOptionsBuilder.from_dataframe(df_vagens_pivot)

            # Estiliza todas as colunas float com 1 casa decimal
            float_cols = df_vagens_pivot.select_dtypes(include=["float", "float64"]).columns
            for col in float_cols:
                gb.configure_column(field=col, type=["numericColumn"], valueFormatter="x.toFixed(1)")

            # Tamanho da fonte e altura do cabeçalho
            gb.configure_default_column(cellStyle={'fontSize': '14px'})
            gb.configure_grid_options(headerHeight=30)

            # CSS extra (percentuais em cinza claro, total em negrito)
            custom_css = {
                ".ag-header-cell-label": {
                    "font-weight": "bold",
                    "font-size": "15px",
                    "color": "black"
                },
                ".ag-row:first-child .ag-cell, .ag-row:nth-child(3) .ag-cell, .ag-row:nth-child(5) .ag-cell": {
                    "background-color": "#f0f0f0"
                },
                ".ag-row:last-child .ag-cell": {
                    "font-weight": "bold"
                }
            }

            # Exibe com AgGrid
            AgGrid(
                df_vagens_pivot,
                gridOptions=gb.build(),
                height=250,
                custom_css=custom_css,
                use_container_width=True
            )


            # 📝 Legenda
            st.markdown("""
            ℹ️ **Legenda**
            - **NV_TS**: Nº médio de vagens no terço superior  
            - **NV_TS_perc**: % de vagens no terço superior  
            - **NV_TM**: Nº médio de vagens no terço médio  
            - **NV_TM_perc**: % de vagens no terço médio  
            - **NV_TI**: Nº médio de vagens no terço inferior  
            - **NV_TI_perc**: % de vagens no terço inferior  
            - **NV_total**: Total médio de vagens por planta
            """)


            # 📥 Exportar Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_vagens_pivot.to_excel(writer, index=False, sheet_name="resumo_vagens_pivot")

            st.download_button(
                label="📥 Baixar Resumo de Vagens (Pivotado)",
                data=output.getvalue(),
                file_name="resumo_vagens_pivotado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # ====================== 📊 Resumo por Cultivar – Número de Grãos por Vagem ======================
            st.markdown("### 📊 Resumo de Caracterização por Cultivar (Número de Grãos por Vagem)")

            # Substitui 0 por NaN
            colunas_graos = [
                "NV_TS_1G", "NV_TS_2G", "NV_TS_3G", "NV_TS_4G",
                "NV_TM_1G", "NV_TM_2G", "NV_TM_3G", "NV_TM_4G",
                "NV_TI_1G", "NV_TI_2G", "NV_TI_3G", "NV_TI_4G"
            ]
            df_caract[colunas_graos] = df_caract[colunas_graos].replace(0, np.nan)

            # Agrupa e calcula média
            df_resumo_graos = df_caract.groupby("Cultivar").agg(
                GM=("GM", "first"),
                **{col: (col, "mean") for col in colunas_graos}
            ).reset_index()

            # Totais por tipo
            df_resumo_graos["NV_1G"] = df_resumo_graos[["NV_TS_1G", "NV_TM_1G", "NV_TI_1G"]].sum(axis=1)
            df_resumo_graos["NV_2G"] = df_resumo_graos[["NV_TS_2G", "NV_TM_2G", "NV_TI_2G"]].sum(axis=1)
            df_resumo_graos["NV_3G"] = df_resumo_graos[["NV_TS_3G", "NV_TM_3G", "NV_TI_3G"]].sum(axis=1)
            df_resumo_graos["NV_4G"] = df_resumo_graos[["NV_TS_4G", "NV_TM_4G", "NV_TI_4G"]].sum(axis=1)

            # Percentuais
            def calcula_percentual(n, d):
                return (n / d.replace(0, pd.NA)) * 100

            for g in ["1G", "2G", "3G", "4G"]:
                for terc in ["TS", "TM", "TI"]:
                    df_resumo_graos[f"NV_{terc}_{g}_perc"] = calcula_percentual(
                        df_resumo_graos[f"NV_{terc}_{g}"], df_resumo_graos[f"NV_{g}"]
                    )

            # 🔄 Arredonda tudo relevante (inclusive %)
            colunas_gerais = colunas_graos + [
                "NV_1G", "NV_2G", "NV_3G", "NV_4G"
            ] + [f"NV_{terc}_{g}_perc" for g in ["1G", "2G", "3G", "4G"] for terc in ["TS", "TM", "TI"]]

            for col in colunas_gerais:
                if col in df_resumo_graos.columns:
                    df_resumo_graos[col] = pd.to_numeric(df_resumo_graos[col], errors="coerce").round(1)

            # Indicadores em ordem
            colunas_indicadores = []
            for g in ["1G", "2G", "3G", "4G"]:
                for terc in ["TS", "TM", "TI"]:
                    colunas_indicadores += [f"NV_{terc}_{g}", f"NV_{terc}_{g}_perc"]
                colunas_indicadores.append(f"NV_{g}")

            # 🚨 Garante que os indicadores realmente existem
            colunas_indicadores = [col for col in colunas_indicadores if col in df_resumo_graos.columns]

            # Pivotagem
            df_long = df_resumo_graos.melt(
                id_vars=["Cultivar"],
                value_vars=colunas_indicadores,
                var_name="Indicador",
                value_name="Valor"
            )
            df_pivot = df_long.pivot_table(
                index="Indicador",
                columns="Cultivar",
                values="Valor"
            ).reindex(colunas_indicadores).reset_index()

            # Verificação extra
            if df_pivot.empty:
                st.warning("⚠️ Nenhum dado disponível para exibir a tabela de grãos por vagem.")
            else:
                # AgGrid com estilo
                gb = GridOptionsBuilder.from_dataframe(df_pivot)

                for col in df_pivot.select_dtypes(include=["float", "float64"]).columns:
                    gb.configure_column(col, type=["numericColumn"], valueFormatter="x.toFixed(1)")

                gb.configure_default_column(cellStyle={'fontSize': '14px'})
                gb.configure_grid_options(headerHeight=30)

                # Estilo CSS para linhas destacadas
                custom_css_graos = {
                    ".ag-header-cell-label": {
                        "font-weight": "bold",
                        "font-size": "15px",
                        "color": "black"
                    },
                    ".ag-row .ag-cell": {
                        "font-size": "14px"
                    },
                    ".ag-row:nth-child(2n) .ag-cell": {
                        "background-color": "#f9f9f9"
                    }
                }

                for idx, indicador in enumerate(df_pivot["Indicador"]):
                    if "_perc" in indicador:
                        custom_css_graos[f".ag-center-cols-container .ag-row[row-index='{idx}'] .ag-cell"] = {
                            "background-color": "#f0f0f0"
                        }
                    elif indicador in ["NV_1G", "NV_2G", "NV_3G", "NV_4G"]:
                        custom_css_graos[f".ag-center-cols-container .ag-row[row-index='{idx}'] .ag-cell"] = {
                            "font-weight": "bold"
                        }

                AgGrid(
                    df_pivot,
                    gridOptions=gb.build(),
                    height=600,
                    custom_css=custom_css_graos,
                    use_container_width=True
                )

                # 📥 Exportar Excel
                output_graos = io.BytesIO()
                with pd.ExcelWriter(output_graos, engine="xlsxwriter") as writer:
                    df_resumo_graos.to_excel(writer, index=False, sheet_name="resumo_graos")

                st.download_button(
                    label="📥 Baixar Resumo (Grãos por Vagem)",
                    data=output_graos.getvalue(),
                    file_name="resumo_cultivar_graos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # 📝 Legenda
                st.markdown("""
                ℹ️ **Legenda**  
                - **NV_XX_1G a NV_XX_4G**: Número médio de grãos por vagem por terço da planta (TS - Superior, TM - Médio, TI - Inferior)  
                - **_perc**: Percentual em relação ao total daquele grupo  
                - **NV_1G a NV_4G**: Total médio de grãos por vagem com 1 a 4 grãos  
                """)

            
            # 📊 Visualizar Gráfico - Percentual de Vagens por Terço da Planta    
            with st.expander("📊 Visualizar Gráfico - Distribuição Percentual de Vagens por Terço"):
                import plotly.express as px

                # Agrupamento e reshape dos dados
                df_vagens_grouped = df_caract.groupby("Cultivar")[["NV_TS_perc", "NV_TM_perc", "NV_TI_perc"]].mean().reset_index()

                df_vagens_long = df_vagens_grouped.melt(
                    id_vars="Cultivar",
                    value_vars=["NV_TS_perc", "NV_TM_perc", "NV_TI_perc"],
                    var_name="Terço",
                    value_name="Percentual"
                )

                # Legenda personalizada
                tercos_legenda = {
                    "NV_TS_perc": "Terço Superior",
                    "NV_TM_perc": "Terço Médio",
                    "NV_TI_perc": "Terço Inferior"
                }
                df_vagens_long["Terço"] = df_vagens_long["Terço"].map(tercos_legenda)

                # 🌈 Cores claras personalizadas
                cores_personalizadas = {
                    "Terço Superior": "#81D4FA",  # Azul claro
                    "Terço Médio": "#4FC3F7",     # Azul médio
                    "Terço Inferior": "#29B6F6"   # Azul escuro
                }

                # 🎯 Gráfico
                fig = px.bar(
                    df_vagens_long,
                    x="Cultivar",
                    y="Percentual",
                    color="Terço",
                    barmode="group",
                    text="Percentual",
                    color_discrete_map=cores_personalizadas
                )

                fig.update_traces(
                    texttemplate='<b>%{text:.1f}%</b>',
                    textposition='outside',
                    textfont=dict(size=20, family="Arial", color="black")
                )

                fig.update_layout(
                    title="<b>Distribuição Percentual de Vagens por Terço</b>",
                    title_font=dict(family="Arial", size=20, color="black"),
                    xaxis=dict(
                        title=dict(text="<b>Cultivar</b>", font=dict(family="Arial", size=20, color="black")),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title=dict(text="<b>Percentual (%)</b>", font=dict(family="Arial", size=20, color="black")),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        range=[0, 100]
                    ),
                    bargap=0.25,
                    height=500,
                    legend_title_text="",
                    legend=dict(font=dict(size=20, family="Arial", color="black"))
                )

                st.plotly_chart(fig, use_container_width=True)
      


            # 📊 Gráfico único: Percentual de Vagens com 4 Grãos por Terço (TS, TM, TI)
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 4 Grãos por Terço da Planta"):
                # Prepara o dataframe no formato longo
                df_4g = df_resumo_graos[["Cultivar", "NV_TS_4G_perc", "NV_TM_4G_perc", "NV_TI_4G_perc"]].copy()

                df_4g_long = df_4g.melt(
                    id_vars="Cultivar",
                    value_vars=["NV_TS_4G_perc", "NV_TM_4G_perc", "NV_TI_4G_perc"],
                    var_name="Terço",
                    value_name="Percentual"
                )

                # Renomeia os terços
                df_4g_long["Terço"] = df_4g_long["Terço"].map({
                    "NV_TS_4G_perc": "Terço Superior",
                    "NV_TM_4G_perc": "Terço Médio",
                    "NV_TI_4G_perc": "Terço Inferior"
                })

                fig = px.bar(
                    df_4g_long,
                    x="Cultivar",
                    y="Percentual",
                    color="Terço",
                    barmode="group",
                    text="Percentual",
                    color_discrete_map={
                        "Terço Superior": "#81D4FA",
                        "Terço Médio": "#4FC3F7",
                        "Terço Inferior": "#29B6F6"
                    },
                    title="<b>Percentual de Vagens com 4 Grãos por Terço da Planta (%)</b>"
                )

                fig.update_traces(
                    texttemplate='<b>%{text:.1f}%</b>',
                    textposition='outside',
                    textfont=dict(size=20, family="Arial", color="black")
                )

                fig.update_layout(
                    title_font=dict(family="Arial", size=20, color="black"),
                    xaxis=dict(
                        title=dict(text="<b>Cultivar</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title=dict(text="<b>Percentual (%)</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        range=[0, 100]
                    ),
                    bargap=0.25,
                    height=500,
                    legend_title_text="",
                    legend=dict(font=dict(size=20, family="Arial", color="black"))
                )

                st.plotly_chart(fig, use_container_width=True)



            # 📊 Gráfico único: Percentual de Vagens com 3 Grãos por Terço (TS, TM, TI)
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 3 Grãos por Terço da Planta"):
                # Prepara o dataframe no formato longo
                df_3g = df_resumo_graos[["Cultivar", "NV_TS_3G_perc", "NV_TM_3G_perc", "NV_TI_3G_perc"]].copy()

                df_3g_long = df_3g.melt(
                    id_vars="Cultivar",
                    value_vars=["NV_TS_3G_perc", "NV_TM_3G_perc", "NV_TI_3G_perc"],
                    var_name="Terço",
                    value_name="Percentual"
                )

                # Renomeia os terços
                df_3g_long["Terço"] = df_3g_long["Terço"].map({
                    "NV_TS_3G_perc": "Terço Superior",
                    "NV_TM_3G_perc": "Terço Médio",
                    "NV_TI_3G_perc": "Terço Inferior"
                })

                # Cria o gráfico
                fig = px.bar(
                    df_3g_long,
                    x="Cultivar",
                    y="Percentual",
                    color="Terço",
                    barmode="group",
                    text="Percentual",
                    color_discrete_map={
                        "Terço Superior": "#81D4FA",
                        "Terço Médio": "#4FC3F7",
                        "Terço Inferior": "#29B6F6"
                    },
                    title="<b>Percentual de Vagens com 3 Grãos por Terço da Planta (%)</b>"
                )

                fig.update_traces(
                    texttemplate='<b>%{text:.1f}%</b>',
                    textposition='outside',
                    textfont=dict(size=20, family="Arial", color="black")
                )

                fig.update_layout(
                    title_font=dict(family="Arial", size=20, color="black"),
                    xaxis=dict(
                        title=dict(text="<b>Cultivar</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title=dict(text="<b>Percentual (%)</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        range=[0, 100]
                    ),
                    bargap=0.25,
                    height=500,
                    legend_title_text="",
                    legend=dict(font=dict(size=20, family="Arial", color="black"))
                )

                st.plotly_chart(fig, use_container_width=True)

           

            # 📊 Gráfico único: Percentual de Vagens com 2 Grãos por Terço (TS, TM, TI)
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 2 Grãos por Terço da Planta"):
                # Prepara o DataFrame no formato longo
                df_2g = df_resumo_graos[["Cultivar", "NV_TS_2G_perc", "NV_TM_2G_perc", "NV_TI_2G_perc"]].copy()

                df_2g_long = df_2g.melt(
                    id_vars="Cultivar",
                    value_vars=["NV_TS_2G_perc", "NV_TM_2G_perc", "NV_TI_2G_perc"],
                    var_name="Terço",
                    value_name="Percentual"
                )

                df_2g_long["Terço"] = df_2g_long["Terço"].map({
                    "NV_TS_2G_perc": "Terço Superior",
                    "NV_TM_2G_perc": "Terço Médio",
                    "NV_TI_2G_perc": "Terço Inferior"
                })

                # Cria o gráfico agrupado
                fig = px.bar(
                    df_2g_long,
                    x="Cultivar",
                    y="Percentual",
                    color="Terço",
                    barmode="group",
                    text="Percentual",
                    color_discrete_map={
                        "Terço Superior": "#81D4FA",
                        "Terço Médio": "#4FC3F7",
                        "Terço Inferior": "#29B6F6"
                    },
                    title="<b>Percentual de Vagens com 2 Grãos por Terço da Planta (%)</b>"
                )

                fig.update_traces(
                    texttemplate='<b>%{text:.1f}%</b>',
                    textposition='outside',
                    textfont=dict(size=20, family="Arial", color="black")
                )

                fig.update_layout(
                    title_font=dict(family="Arial", size=20, color="black"),
                    xaxis=dict(
                        title=dict(text="<b>Cultivar</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title=dict(text="<b>Percentual (%)</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        range=[0, 100]
                    ),
                    bargap=0.25,
                    height=500,
                    legend_title_text="",
                    legend=dict(font=dict(size=20, family="Arial", color="black"))
                )

                st.plotly_chart(fig, use_container_width=True)

            # ============================ 📊 Gráfico único: Vagens com 1 Grão por Terço ============================
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 1 Grão por Terço da Planta"):
                # Prepara o DataFrame no formato longo
                df_1g = df_resumo_graos[["Cultivar", "NV_TS_1G_perc", "NV_TM_1G_perc", "NV_TI_1G_perc"]].copy()

                df_1g_long = df_1g.melt(
                    id_vars="Cultivar",
                    value_vars=["NV_TS_1G_perc", "NV_TM_1G_perc", "NV_TI_1G_perc"],
                    var_name="Terço",
                    value_name="Percentual"
                )

                df_1g_long["Terço"] = df_1g_long["Terço"].map({
                    "NV_TS_1G_perc": "Terço Superior",
                    "NV_TM_1G_perc": "Terço Médio",
                    "NV_TI_1G_perc": "Terço Inferior"
                })

                # Cria o gráfico agrupado
                fig = px.bar(
                    df_1g_long,
                    x="Cultivar",
                    y="Percentual",
                    color="Terço",
                    barmode="group",
                    text="Percentual",
                    color_discrete_map={
                        "Terço Superior": "#81D4FA",  # Azul claro
                        "Terço Médio": "#4FC3F7",     # Verde claro
                        "Terço Inferior": "#29B6F6"   # Azul escuro
                    },
                    title="<b>Percentual de Vagens com 1 Grão por Terço da Planta (%)</b>"
                )

                fig.update_traces(
                    texttemplate='<b>%{text:.1f}%</b>',
                    textposition='outside',
                    textfont=dict(size=20, family="Arial", color="black")
                )

                fig.update_layout(
                    title_font=dict(family="Arial", size=20, color="black"),
                    xaxis=dict(
                        title=dict(text="<b>Cultivar</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title=dict(text="<b>Percentual (%)</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        range=[0, 100]
                    ),
                    bargap=0.25,
                    height=500,
                    legend_title_text="",
                    legend=dict(font=dict(size=20, family="Arial", color="black"))
                )

                st.plotly_chart(fig, use_container_width=True)
      



            # ============================ 📊 Gráfico único: Percentual de Vagens com 1 a 4 Grãos ============================
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 1 a 4 Grãos por Cultivar"):
                df_vagens_graos = df_resumo_graos[["Cultivar", "NV_1G", "NV_2G", "NV_3G", "NV_4G"]].copy()

                df_vagens_graos_long = df_vagens_graos.melt(
                    id_vars="Cultivar",
                    value_vars=["NV_1G", "NV_2G", "NV_3G", "NV_4G"],
                    var_name="Grãos por Vagem",
                    value_name="Percentual"
                )

                df_vagens_graos_long["Grãos por Vagem"] = df_vagens_graos_long["Grãos por Vagem"].map({
                    "NV_1G": "1 Grão",
                    "NV_2G": "2 Grãos",
                    "NV_3G": "3 Grãos",
                    "NV_4G": "4 Grãos"
                })

                fig = px.bar(
                    df_vagens_graos_long,
                    x="Cultivar",
                    y="Percentual",
                    color="Grãos por Vagem",
                    barmode="group",
                    text="Percentual",
                    title="<b>Percentual de Vagens com 1 a 4 Grãos por Cultivar</b>",
                    color_discrete_map={
                        "1 Grão": "#B2EBF2",
                        "2 Grãos": "#81D4FA",
                        "3 Grãos": "#4FC3F7",
                        "4 Grãos": "#29B6F6"
                    }
                )

                fig.update_traces(
                    texttemplate='<b>%{text:.1f}%</b>',
                    textposition='outside',
                    textfont=dict(size=20, family="Arial", color="black")
                )

                fig.update_layout(
                    title_font=dict(family="Arial", size=20, color="black"),
                    xaxis=dict(
                        title=dict(text="<b>Cultivar</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title=dict(text="<b>Percentual (%)</b>", font=dict(size=20, family="Arial", color="black")),
                        tickfont=dict(size=20, family="Arial", color="black"),
                        range=[0, 100]
                    ),
                    bargap=0.25,
                    height=500,
                    legend_title_text="",
                    legend=dict(font=dict(size=20, family="Arial", color="black"))
                )

                st.plotly_chart(fig, use_container_width=True)



            
          

            # 📥 Exportar
            output_graos = io.BytesIO()
            with pd.ExcelWriter(output_graos, engine="xlsxwriter") as writer:
                df_resumo_graos.to_excel(writer, index=False, sheet_name="resumo_grao_vagem")

            st.download_button(
                label="📥 Baixar Resumo (Grãos por Vagem)",
                data=output_graos.getvalue(),
                file_name="resumo_cultivar_grao_vagem.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_graos"
            )           



    else:
        st.warning("⚠️ Dados de AV5 (Caracterização Agronômica) não encontrados ou estão vazios.")
else:
    st.error("❌ Dados não carregados. Volte à página principal e carregue os dados primeiro.")
