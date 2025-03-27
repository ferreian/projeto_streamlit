import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.title("🌱 Caracterização Agronômica (AV5)")
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

        # 🔍 Layout com filtros
        col_filtros, col_tabela = st.columns([1.5, 8.5])

        with col_filtros:
            st.markdown("### 🎛️ Filtros")

            filtros = {
                "Microrregiao": "Microrregião",
                "Estado": "Estado",
                "Cidade": "Cidade",
                "Fazenda": "Fazenda",
                "Cultivar": "Cultivar",
                "GM": "GM"
            }

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
        
        # 📊 Tabela
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

            st.markdown("### 📋 Tabela de Caracterização Agronômica (AV5)")
            st.dataframe(df_caract[colunas_visiveis], use_container_width=True)

            # 📥 Exportar
            output_av5 = io.BytesIO()
            with pd.ExcelWriter(output_av5, engine="xlsxwriter") as writer:
                df_caract[colunas_visiveis].to_excel(writer, index=False, sheet_name="caracterizacao_av5")

            st.download_button(
                label="📥 Baixar Caracterização (AV5)",
                data=output_av5.getvalue(),
                file_name="caracterizacao_agronomica_av5.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


            
            # ====================== 📊 Resumo por Cultivar – Número de Vagens ======================
            st.markdown("### 📊 Resumo de Caracterização por Cultivar (Número de Vagens)")

            colunas_vagens = [
                "NV_TS_medio", "NV_TM_media", "NV_TI_media", "NV_media"
            ]

            # 🎯 Agrupa por cultivar e calcula média
            df_resumo_vagens = df_caract.groupby("Cultivar").agg(
                GM=("GM", "first"),
                **{col: (col, "mean") for col in colunas_vagens}
            ).reset_index()

            # ➕ Calcula percentuais apenas se NV_media > 0
            df_resumo_vagens["NV_TS_perc"] = df_resumo_vagens.apply(
                lambda row: round((row["NV_TS_medio"] / row["NV_media"]) * 100, 2) if row["NV_media"] > 0 else None,
                axis=1
            )
            df_resumo_vagens["NV_TM_perc"] = df_resumo_vagens.apply(
                lambda row: round((row["NV_TM_media"] / row["NV_media"]) * 100, 2) if row["NV_media"] > 0 else None,
                axis=1
            )
            df_resumo_vagens["NV_TI_perc"] = df_resumo_vagens.apply(
                lambda row: round((row["NV_TI_media"] / row["NV_media"]) * 100, 2) if row["NV_media"] > 0 else None,
                axis=1
            )

            # 🔄 Reorganiza colunas
            colunas_visiveis_vagens = [
                "Cultivar", "GM",
                "NV_TS_medio", "NV_TM_media", "NV_TI_media", "NV_media",
                "NV_TS_perc", "NV_TM_perc", "NV_TI_perc"
            ]

            df_resumo_vagens = df_resumo_vagens[colunas_visiveis_vagens]

            # 🧾 Mostra tabela
            st.dataframe(df_resumo_vagens, use_container_width=True)


            # 📥 Exportar
            output_vagens = io.BytesIO()
            with pd.ExcelWriter(output_vagens, engine="xlsxwriter") as writer:
                df_resumo_vagens.to_excel(writer, index=False, sheet_name="resumo_vagens")

            st.download_button(
                label="📥 Baixar Resumo (Número de Vagens)",
                data=output_vagens.getvalue(),
                file_name="resumo_cultivar_vagens.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

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
                    "Terço Superior": "#6EC1E4",  # azul claro
                    "Terço Médio": "#A5D6A7",     # verde claro
                    "Terço Inferior": "#F48FB1"   # rosa claro
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
                    textfont=dict(size=16, family="Arial", color="black")
                )

                fig.update_layout(
                    title="Distribuição Percentual de Vagens por Terço",
                    title_font=dict(family="Arial", size=20, color="black"),
                    xaxis=dict(
                        title=dict(text="Cultivar", font=dict(family="Arial", size=16, color="black")),
                        tickfont=dict(family="Arial", size=16, color="black"),
                        tickangle=-45
                    ),
                    yaxis=dict(
                        visible=False,
                        range=[0, 100]
                    ),
                    bargap=0.25,
                    height=500,
                    legend_title_text=""
                )

                st.plotly_chart(fig, use_container_width=True)













            # 📊 Gráfico de barras - Caracterização de Produtividade no Terço Superior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens no Terço Superior"):
                fig = px.bar(
                    df_resumo_vagens,
                    x="Cultivar",
                    y="NV_TS_perc",
                    text="NV_TS_perc",
                    labels={"NV_TS_perc": "% Vagens - TS"},
                    title="Percentual de Vagens no Terço Superior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # 📊 Gráfico de barras - Caracterização de Produtividade no Terço Médio
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens no Terço Médio"):
                fig = px.bar(
                    df_resumo_vagens,
                    x="Cultivar",
                    y="NV_TM_perc",
                    text="NV_TM_perc",
                    labels={"NV_TM_perc": "% Vagens - TM"},
                    title="Percentual de Vagens no Terço Médio (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade no Terço Inferior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens no Terço Inferior"):
                fig = px.bar(
                    df_resumo_vagens,
                    x="Cultivar",
                    y="NV_TI_perc",
                    text="NV_TI_perc",
                    labels={"NV_TI_perc": "% Vagens - TI"},
                    title="Percentual de Vagens no Terço Inferior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            
            # ====================== 📊 Resumo por Cultivar – Número de Grãos por Vagem ======================
            st.markdown("### 📊 Resumo de Caracterização por Cultivar (Número de Grão por Vagem)")

            colunas_graos = [
                "NV_TS_1G", "NV_TS_2G", "NV_TS_3G", "NV_TS_4G",
                "NV_TM_1G", "NV_TM_2G", "NV_TM_3G", "NV_TM_4G",
                "NV_TI_1G", "NV_TI_2G", "NV_TI_3G", "NV_TI_4G",
                "NV_1G", "NV_2G", "NV_3G", "NV_4G"
            ]

            df_resumo_graos = df_caract.groupby("Cultivar").agg(
                GM=("GM", "first"),
                **{col: (col, "mean") for col in colunas_graos}
            ).round(2).reset_index()

            # ➕ Cálculo das porcentagens (ignorando divisões por zero ou NaN)
            def calcula_percentual(numerador, denominador):
                return (numerador / denominador.replace(0, pd.NA)).round(2)

            df_resumo_graos["NV_TS_1G_perc"] = calcula_percentual(df_resumo_graos["NV_TS_1G"], df_resumo_graos["NV_1G"])
            df_resumo_graos["NV_TM_1G_perc"] = calcula_percentual(df_resumo_graos["NV_TM_1G"], df_resumo_graos["NV_1G"])
            df_resumo_graos["NV_TI_1G_perc"] = calcula_percentual(df_resumo_graos["NV_TI_1G"], df_resumo_graos["NV_1G"])

            df_resumo_graos["NV_TS_2G_perc"] = calcula_percentual(df_resumo_graos["NV_TS_2G"], df_resumo_graos["NV_2G"])
            df_resumo_graos["NV_TM_2G_perc"] = calcula_percentual(df_resumo_graos["NV_TM_2G"], df_resumo_graos["NV_2G"])
            df_resumo_graos["NV_TI_2G_perc"] = calcula_percentual(df_resumo_graos["NV_TI_2G"], df_resumo_graos["NV_2G"])

            df_resumo_graos["NV_TS_3G_perc"] = calcula_percentual(df_resumo_graos["NV_TS_3G"], df_resumo_graos["NV_3G"])
            df_resumo_graos["NV_TM_3G_perc"] = calcula_percentual(df_resumo_graos["NV_TM_3G"], df_resumo_graos["NV_3G"])
            df_resumo_graos["NV_TI_3G_perc"] = calcula_percentual(df_resumo_graos["NV_TI_3G"], df_resumo_graos["NV_3G"])

            df_resumo_graos["NV_TS_4G_perc"] = calcula_percentual(df_resumo_graos["NV_TS_4G"], df_resumo_graos["NV_4G"])
            df_resumo_graos["NV_TM_4G_perc"] = calcula_percentual(df_resumo_graos["NV_TM_4G"], df_resumo_graos["NV_4G"])
            df_resumo_graos["NV_TI_4G_perc"] = calcula_percentual(df_resumo_graos["NV_TI_4G"], df_resumo_graos["NV_4G"])


            # 🧾 Mostra tabela
            # ✅ Define colunas visíveis (incluindo calculadas)

            colunas_visiveis_graos = [
                "Cultivar", "GM",
                "NV_TS_1G", "NV_TS_1G_perc",
                "NV_TM_1G","NV_TM_1G_perc",
                "NV_TI_1G","NV_TI_1G_perc",
                "NV_1G",
                 
                "NV_TS_2G", "NV_TS_2G_perc",
                "NV_TM_2G", "NV_TM_2G_perc",
                "NV_TI_2G","NV_TI_2G_perc",
                "NV_2G",
                  

                "NV_TS_3G","NV_TS_3G_perc",
                "NV_TM_3G","NV_TM_3G_perc",
                "NV_TI_3G","NV_TI_3G_perc",
                "NV_3G",
                 

                "NV_TS_4G","NV_TS_4G_perc",
                "NV_TM_4G","NV_TM_4G_perc",
                "NV_TI_4G","NV_TI_4G_perc",
                "NV_4G",
            ]

            # 🔒 Garante que só aparecem colunas que existem
            colunas_visiveis_graos = [col for col in colunas_visiveis_graos if col in df_resumo_graos.columns]

            # 🧾 Mostra tabela
            st.dataframe(df_resumo_graos[colunas_visiveis_graos], use_container_width=True)


            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 4 Grãos no Terço Superior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 4 Grãos no Terço Superior"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TS_4G_perc",
                    text="NV_TS_4G_perc",
                    labels={"NV_TS_4G_perc": "% Vagens 4 Grãos - TS"},
                    title="Percentual de Vagens com 4 Grãos no Terço Superior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
           

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 3 Grãos no Terço Superior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 3 Grãos no Terço Superior"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TS_3G_perc",
                    text="NV_TS_3G_perc",
                    labels={"NV_TS_3G_perc": "% Vagens 3 Grãos - TS"},
                    title="Percentual de Vagens com 3 Grãos no Terço Superior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 2 Grãos no Terço Superior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 2 Grãos no Terço Superior"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TS_2G_perc",
                    text="NV_TS_2G_perc",
                    labels={"NV_TS_2G_perc": "% Vagens 2 Grãos - TS"},
                    title="Percentual de Vagens com 2 Grãos no Terço Superior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 1 Grãos no Terço Superior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 1 Grão no Terço Superior"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TS_1G_perc",
                    text="NV_TS_1G_perc",
                    labels={"NV_TS_1G_perc": "% Vagens 1 Grão - TS"},
                    title="Percentual de Vagens com 1 Grão no Terço Superior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
                      

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 4 Grãos no Terço Medio
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 4 Grãos no Terço Médio"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TM_4G_perc",
                    text="NV_TM_4G_perc",
                    labels={"NV_TM_4G_perc": "% Vagens 4 Grãos - TM"},
                    title="Percentual de Vagens com 4 Grãos no Terço Médio (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 3 Grãos no Terço Médio
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 3 Grãos no Terço Médio"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TM_3G_perc",
                    text="NV_TM_3G_perc",
                    labels={"NV_TM_3G_perc": "% Vagens 3 Grãos - TS"},
                    title="Percentual de Vagens com 3 Grãos no Terço Superior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 2 Grãos no Terço Medio
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 2 Grãos no Terço Médio"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TM_2G_perc",
                    text="NV_TM_2G_perc",
                    labels={"NV_TM_2G_perc": "% Vagens 2 Grãos - TM"},
                    title="Percentual de Vagens com 2 Grãos no Terço Médio (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 1 Grãos no Terço Medio
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 1 Grão no Terço Médio"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TM_1G_perc",
                    text="NV_TM_1G_perc",
                    labels={"NV_TM_1G_perc": "% Vagens 1 Grão - TM"},
                    title="Percentual de Vagens com 1 Grão no Terço Médio (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 4 Grãos no Terço Inferior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 4 Grãos no Terço Inferior"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TI_4G_perc",
                    text="NV_TI_4G_perc",
                    labels={"NV_TI_4G_perc": "% Vagens 4 Grãos - TI"},
                    title="Percentual de Vagens com 4 Grãos no Terço Inferior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 3 Grãos no Terço Inferior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 3 Grãos no Terço Inferior"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TI_3G_perc",
                    text="NV_TI_3G_perc",
                    labels={"NV_TI_3G_perc": "% Vagens 3 Grãos - TI"},
                    title="Percentual de Vagens com 3 Grãos no Terço Inferior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 2 Grãos no Terço Inferior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 2 Grãos no Terço Inferior"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TI_2G_perc",
                    text="NV_TI_2G_perc",
                    labels={"NV_TI_2G_perc": "% Vagens 2 Grãos - TI"},
                    title="Percentual de Vagens com 2 Grãos no Terço Inferior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 1 Grão no Terço Inferior
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 1 Grão no Terço Inferior"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_TI_1G_perc",
                    text="NV_TI_1G_perc",
                    labels={"NV_TI_1G_perc": "% Vagens 1 Grão - TI"},
                    title="Percentual de Vagens com 1 Grão no Terço Inferior (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 4 Grãos
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 4 Grãos"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_4G",
                    text="NV_4G",
                    labels={"NV_4G": "% Vagens 4 Grãos"},
                    title="Percentual de Vagens com 4 Grãos (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 3 Grãos
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 3 Grãos"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_3G",
                    text="NV_3G",
                    labels={"NV_3G": "% Vagens 3 Grãos"},
                    title="Percentual de Vagens com 3 Grãos (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 2 Grãos
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 2 Grãos"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_2G",
                    text="NV_2G",
                    labels={"NV_2G": "% Vagens 2 Grãos"},
                    title="Percentual de Vagens com 2 Grãos (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # 📊 Gráfico de barras - Caracterização de Produtividade Número de Vagens com 1 Grão
            with st.expander("📊 Visualizar Gráfico - Percentual de Vagens com 1 Grão"):
                fig = px.bar(
                    df_resumo_graos,
                    x="Cultivar",
                    y="NV_1G",
                    text="NV_1G",
                    labels={"NV_1G": "% Vagens 1 Grãos"},
                    title="Percentual de Vagens com 1 Grãos (%)",
                    color_discrete_sequence=["lightblue"]
                )

                fig.update_traces(
                    texttemplate='%{text:.1f}%',
                    textposition='outside',
                    textfont=dict(
                        size=14,
                        family="Arial",
                        color="black"
                    )
                )

                fig.update_layout(
                    title_font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Cultivar",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        )
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Percentual (%)",
                            font=dict(
                                family="Arial",
                                size=16,
                                color="black"
                            )
                        ),
                        tickfont=dict(
                            size=13,
                            family="Arial",
                            color="black"
                        ),
                        range=[0, 100]
                    ),
                    uniformtext_minsize=8,
                    uniformtext_mode='hide',
                    bargap=0.3,
                    height=450
                )

                fig.update_xaxes(tickangle=-45)
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


            # 📊 Gráfico Combinado - Distribuição de Vagens por Terço e por Nº de Grãos")"
            with st.expander("📊 Gráfico Combinado - Distribuição de Vagens por Terço e por Nº de Grãos"):
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots

                cultivar_labels = df_resumo_vagens["Cultivar"]

                fig = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=("Número Médio de Vagens por Terço", "Distribuição de Vagens por Nº de Grãos"),
                    shared_yaxes=True
                )

                # Parte 1 - Vagens por terço
                fig.add_trace(go.Bar(
                    x=df_resumo_vagens["NV_TS_medio"],
                    y=cultivar_labels,
                    name="Terço Superior",
                    orientation='h',
                    marker_color="#6EC1E4",
                ), row=1, col=1)

                fig.add_trace(go.Bar(
                    x=df_resumo_vagens["NV_TM_media"],
                    y=cultivar_labels,
                    name="Terço Médio",
                    orientation='h',
                    marker_color="#A5D6A7",
                ), row=1, col=1)

                fig.add_trace(go.Bar(
                    x=df_resumo_vagens["NV_TI_media"],
                    y=cultivar_labels,
                    name="Terço Inferior",
                    orientation='h',
                    marker_color="#F48FB1",
                ), row=1, col=1)

                # Parte 2 - Vagens por nº de grãos
                fig.add_trace(go.Bar(
                    x=df_resumo_graos["NV_4G"],
                    y=cultivar_labels,
                    name="4 Grãos",
                    orientation='h',
                    marker_color="#1976D2"
                ), row=1, col=2)

                fig.add_trace(go.Bar(
                    x=df_resumo_graos["NV_3G"],
                    y=cultivar_labels,
                    name="3 Grãos",
                    orientation='h',
                    marker_color="#4CAF50"
                ), row=1, col=2)

                fig.add_trace(go.Bar(
                    x=df_resumo_graos["NV_2G"],
                    y=cultivar_labels,
                    name="2 Grãos",
                    orientation='h',
                    marker_color="#FFB6C1"
                ), row=1, col=2)

                fig.add_trace(go.Bar(
                    x=df_resumo_graos["NV_1G"],
                    y=cultivar_labels,
                    name="1 Grão",
                    orientation='h',
                    marker_color="#E1BEE7"
                ), row=1, col=2)

                fig.update_layout(
                    height=600,
                    title="📊 Distribuição de Vagens por Parte da Planta e Nº de Grãos",
                    barmode='stack',
                    showlegend=True,
                    xaxis_title="Média de Vagens",
                    font=dict(size=14, family="Arial"),
                )

                st.plotly_chart(fig, use_container_width=True)


        








#=====+++++++++




    else:
        st.warning("⚠️ Dados de AV5 (Caracterização Agronômica) não encontrados ou estão vazios.")
else:
    st.error("❌ Dados não carregados. Volte à página principal e carregue os dados primeiro.")
