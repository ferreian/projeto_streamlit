import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder
import io

st.title("📊 Performance dos materiais")
st.markdown(
    "Nesta página, você pode visualizar a performance dos materiais avaliados em diferentes localidades, "
    "comparando seus resultados com a média geral, a média específica do local e a média das melhores testemunhas."
)

if "merged_dataframes" in st.session_state:
    df_av7 = st.session_state["merged_dataframes"].get("av7TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")

    if df_av7 is not None and not df_av7.empty:
        st.success("✅ Dados carregados com sucesso!")

        df_final_av7 = df_av7[~df_av7["displayName"].isin(["raullanconi", "stine"])].copy()

        if "numeroLinhas" in df_final_av7.columns and "comprimentoLinha" in df_final_av7.columns:
            df_final_av7["areaParcela"] = df_final_av7["numeroLinhas"] * df_final_av7["comprimentoLinha"] * 0.5

        col_plantas = ["numeroPlantas10Metros1a", "numeroPlantas10Metros2a", "numeroPlantas10Metros3a", "numeroPlantas10Metros4a"]
        if all(col in df_final_av7.columns for col in col_plantas):
            df_final_av7["numeroPlantasMedio10m"] = df_final_av7[col_plantas].replace(0, pd.NA).mean(axis=1, skipna=True)
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

        if all(col in df_final_av7.columns for col in ["ChaveFaixa", "populacao"]):
            df_final_av7["ChaveDensidade"] = df_final_av7["ChaveFaixa"].astype(str) + "_" + df_final_av7["populacao"].astype(str)

        df_final_av7 = df_final_av7[df_final_av7["tipoTeste"] == "Densidade"]

        colunas_renomeadas = {
            "nomeFazenda": "Fazenda", "nomeProdutor": "Produtor", "regional": "Microrregiao",
            "nomeCidade": "Cidade", "codigoEstado": "Estado", "nomeEstado": "UF",
            "dataPlantio": "Plantio", "dataColheita": "Colheita", "tipoTeste": "Teste",
            "nome": "Cultivar", "gm": "GM", "populacao": "População", "indexTratamento": "Index",
            "areaParcela": "Área Parcela", "numeroPlantasMedio10m": "plts_10m", "Pop_Final": "Pop_Final",
            "umidadeParcela": "Umidade (%)", "producaoCorrigida": "prod_kg_ha", "producaoCorrigidaSc": "prod_sc_ha",
            "PMG_corrigido": "PMG", "displayName": "DTC", "cidadeRef": "CidadeRef",
            "fazendaRef": "FazendaRef", "ChaveFaixa": "ChaveFaixa"
        }

        df_final_av7 = df_final_av7.rename(columns=colunas_renomeadas)

        for col in ["Plantio", "Colheita"]:
            if col in df_final_av7.columns:
                df_final_av7[col] = pd.to_datetime(df_final_av7[col], errors="coerce", origin="unix", unit="s").dt.strftime("%d/%m/%Y")

        if "Index" in df_final_av7.columns and "População" in df_final_av7.columns:
            df_final_av7["Index_População"] = df_final_av7["Index"].astype(str) + "_" + df_final_av7["População"].astype(str)

        df_final_av7["Grupo"] = df_final_av7["Index"].astype(str).str[-2:] + "_" + df_final_av7["População"].astype(str)

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

        with col_tabela:
            st.markdown("### 📋 Tabela Informações de Produção")

            colunas_visiveis = [
                "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "População", "Index", "Index_População", "GM",
                "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
                "prod_kg_ha", "prod_sc_ha", "PMG", "ChaveDensidade", "Grupo"
            ]

            colunas_presentes = [col for col in colunas_visiveis if col in df_final_av7.columns]
            df_visualizacao = df_final_av7[colunas_presentes]

            gb = GridOptionsBuilder.from_dataframe(df_visualizacao)
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
                df_visualizacao,
                gridOptions=gb.build(),
                height=500,
                custom_css=custom_css
            )

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_visualizacao.to_excel(writer, index=False, sheet_name="faixa_densidade")

            st.download_button(
                label="🗕️ Baixar Densidade",
                data=output.getvalue(),
                file_name="densidade.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Novo dataframe agrupado
            st.markdown("### 🪜 Média por Grupo de Repetições")

            df_media_grupo = df_final_av7.groupby("Grupo").agg({
                "Cultivar": "first",
                "População": "first",
                "Pop_Final": "mean",
                "prod_kg_ha": "mean",
                "prod_sc_ha": "mean",
                "PMG": "mean"
            }).reset_index()


            # Arredonda e formata
            df_media_grupo["Pop_Final"] = df_media_grupo["Pop_Final"].round(0).astype(int)
            df_media_grupo["prod_kg_ha"] = df_media_grupo["prod_kg_ha"].round(1)
            df_media_grupo["prod_sc_ha"] = df_media_grupo["prod_sc_ha"].round(1)
            df_media_grupo["PMG"] = df_media_grupo["PMG"].round(1)

            # Mostra no AgGrid
            gb_grupo = GridOptionsBuilder.from_dataframe(df_media_grupo)
            gb_grupo.configure_default_column(cellStyle={'fontSize': '14px'})

            AgGrid(
                df_media_grupo,
                gridOptions=gb_grupo.build(),
                height=350,
                custom_css=custom_css
            )

            # Botão para exportar o dataframe de média por grupo
            output_grupo = io.BytesIO()
            with pd.ExcelWriter(output_grupo, engine='xlsxwriter') as writer:
                df_media_grupo.to_excel(writer, index=False, sheet_name="media_grupos")

            st.download_button(
                label="🗕️ Baixar Média por Grupo",
                data=output_grupo.getvalue(),
                file_name="media_por_grupo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            import pandas as pd
            import plotly.express as px
            import numpy as np

            # Histograma 📊 população final
            with st.expander("📊 Visualizar Histograma de População Final", expanded=False):
                st.markdown("Visualize a distribuição de `População Final` por faixa de população.")

                populacao_order = [200, 250, 300, 350, 400]

                # Cores personalizadas
                cores_populacao = {
                    200: "#1f77b4",  # azul
                    250: "#2ca02c",  # verde
                    300: "#ff7f0e",  # laranja
                    350: "#9467bd",  # roxo
                    400: "#8c564b"   # marrom escuro
                }

                # Filtra zeros e nulos
                df_filtrado = df_final_av7.copy()
                df_filtrado["Pop_Final"] = pd.to_numeric(df_filtrado["Pop_Final"], errors="coerce")
                df_filtrado = df_filtrado[df_filtrado["Pop_Final"].notna()]
                df_filtrado = df_filtrado[df_filtrado["Pop_Final"] > 0]

                fig = px.histogram(
                    df_filtrado,
                    x="Pop_Final",
                    color="População",
                    facet_col="População",
                    nbins=50,
                    title="Histograma da População por 'Pop_Final'",
                    labels={"Pop_Final": "População Final"},
                    category_orders={"População": populacao_order},
                    color_discrete_map=cores_populacao
                )

                # Layout geral
                fig.update_layout(
                    showlegend=False,
                    height=600,
                    bargap=0.3,
                    template="plotly_white",
                    title=dict(
                        text="Histograma da População por 'Pop_Final'",
                        font=dict(size=18, family="Arial Black", color="black")
                    )
                )

                # Títulos das facetas em negrito
                for annotation in fig.layout.annotations:
                    annotation.font = dict(family="Arial Black", size=14, color="black")

                # Eixos + linha de média + anotação
                for i, populacao in enumerate(populacao_order):
                    eixo_x = f"xaxis{i + 1 if i > 0 else ''}"
                    eixo_y = f"yaxis{i + 1 if i > 0 else ''}"

                    fig.update_layout({
                        eixo_x: dict(
                            range=[100000, 450000],
                            tickformat="~s",
                            title=dict(
                                text="População Final",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickfont=dict(family="Arial", size=12, color="black")
                        ),
                        eixo_y: dict(
                            range=[0, 10],  # Ajuste conforme necessário
                            title=dict(
                                text="Frequência",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickfont=dict(family="Arial", size=12, color="black")
                        )
                    })

                    # Dados por população (limpos)
                    dados_pop = df_filtrado[df_filtrado["População"] == populacao]["Pop_Final"]

                    if len(dados_pop) == 0:
                        continue

                    media = dados_pop.mean()
                    xref = eixo_x.replace("axis", "")
                    yref = eixo_y.replace("axis", "")

                    # Linha da média
                    fig.add_shape(
                        type="line",
                        x0=media,
                        x1=media,
                        y0=0,
                        y1=0.88,
                        xref=xref,
                        yref="paper",
                        line=dict(color="red", width=2, dash="dash")
                    )

                    # Anotação da média
                    fig.add_annotation(
                        x=media,
                        y=1.05,
                        xref=xref,
                        yref="paper",
                        text=f"Média: {int(media/1000)}K",
                        showarrow=False,
                        yanchor="bottom",
                        font=dict(family="Arial Black", size=12, color="red"),
                        align="center"
                    )

                # Exibe o gráfico
                st.plotly_chart(fig, use_container_width=True)




            import pandas as pd
            import plotly.express as px
            import numpy as np

            # Histograma 📊 produção corrigida
            with st.expander("📊 Visualizar Histograma de Produção (sc/ha)", expanded=False):
                st.markdown("Distribuição da produção por faixa de população, considerando apenas valores válidos (≠ 0 e não nulos).")

                populacao_order = [200, 250, 300, 350, 400]

                cores_populacao = {
                    200: "#1f77b4",
                    250: "#2ca02c",
                    300: "#ff7f0e",
                    350: "#9467bd",
                    400: "#8c564b"
                }

                # Filtrando zeros e nulos
                df_filtrado = df_final_av7.copy()
                df_filtrado["prod_sc_ha"] = pd.to_numeric(df_filtrado["prod_sc_ha"], errors="coerce")
                df_filtrado = df_filtrado[df_filtrado["prod_sc_ha"].notna()]
                df_filtrado = df_filtrado[df_filtrado["prod_sc_ha"] > 0]

                fig = px.histogram(
                    df_filtrado,
                    x="prod_sc_ha",
                    color="População",
                    facet_col="População",
                    nbins=50,
                    title="Histograma da Produção por 'sc/ha'",
                    labels={"prod_sc_ha": "Produção (sc/ha)"},
                    category_orders={"População": populacao_order},
                    color_discrete_map=cores_populacao
                )

                fig.update_layout(
                    showlegend=False,
                    height=600,
                    bargap=0.3,
                    template="plotly_white",
                    title=dict(
                        text="Histograma da Produção por 'sc/ha'",
                        font=dict(size=18, family="Arial Black", color="black")
                    )
                )

                for annotation in fig.layout.annotations:
                    annotation.font = dict(family="Arial Black", size=14, color="black")

                for i, populacao in enumerate(populacao_order):
                    eixo_x = f"xaxis{i + 1 if i > 0 else ''}"
                    eixo_y = f"yaxis{i + 1 if i > 0 else ''}"

                    fig.update_layout({
                        eixo_x: dict(
                            range=[0, 120],
                            title=dict(
                                text="Produção (sc/ha)",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickfont=dict(family="Arial", size=12, color="black")
                        ),
                        eixo_y: dict(
                            range=[0, 20],
                            title=dict(
                                text="Frequência",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickfont=dict(family="Arial", size=12, color="black")
                        )
                    })

                    # Filtra os dados válidos por população
                    dados_pop = df_filtrado[df_filtrado["População"] == populacao]["prod_sc_ha"]

                    if len(dados_pop) == 0:
                        continue

                    media = dados_pop.mean()
                    xref = eixo_x.replace("axis", "")

                    fig.add_shape(
                        type="line",
                        x0=media,
                        x1=media,
                        y0=0,
                        y1=1,
                        xref=xref,
                        yref="paper",
                        line=dict(color="red", width=2, dash="dash")
                    )

                    fig.add_annotation(
                        x=media,
                        y=1.05,
                        xref=xref,
                        yref="paper",
                        text=f"Média: {media:.1f} sc/ha",
                        showarrow=False,
                        yanchor="bottom",
                        font=dict(family="Arial Black", size=12, color="red"),
                        align="center"
                    )

                st.plotly_chart(fig, use_container_width=True)



            import pandas as pd
            import plotly.express as px
            import numpy as np

            # Histograma 📊 PMG
            with st.expander("📊 Visualizar Histograma de PMG (Peso de Mil Grãos)", expanded=False):
                st.markdown("Distribuição do PMG (Peso de Mil Grãos) por faixa de população, considerando apenas valores válidos.")

                populacao_order = [200, 250, 300, 350, 400]

                cores_populacao = {
                    200: "#1f77b4",
                    250: "#2ca02c",
                    300: "#ff7f0e",
                    350: "#9467bd",
                    400: "#8c564b"
                }

                # Filtrando zeros e nulos
                df_filtrado = df_final_av7.copy()
                df_filtrado["PMG"] = pd.to_numeric(df_filtrado["PMG"], errors="coerce")
                df_filtrado = df_filtrado[df_filtrado["PMG"].notna()]
                df_filtrado = df_filtrado[df_filtrado["PMG"] > 0]

                fig = px.histogram(
                    df_filtrado,
                    x="PMG",
                    color="População",
                    facet_col="População",
                    nbins=10,
                    title="Histograma do Peso de Mil Grãos (PMG)",
                    labels={"PMG": "PMG (g)"},
                    category_orders={"População": populacao_order},
                    color_discrete_map=cores_populacao
                )

                fig.update_layout(
                    showlegend=False,
                    height=600,
                    bargap=0.3,
                    template="plotly_white",
                    title=dict(
                        text="Histograma do Peso de Mil Grãos (PMG)",
                        font=dict(size=18, family="Arial Black", color="black")
                    )
                )

                for annotation in fig.layout.annotations:
                    annotation.font = dict(family="Arial Black", size=14, color="black")

                for i, populacao in enumerate(populacao_order):
                    eixo_x = f"xaxis{i + 1 if i > 0 else ''}"
                    eixo_y = f"yaxis{i + 1 if i > 0 else ''}"

                    fig.update_layout({
                        eixo_x: dict(
                            title=dict(
                                text="PMG (g)",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickfont=dict(family="Arial", size=12, color="black")
                        ),
                        eixo_y: dict(
                            range=[0, 8],  # ajuste se quiser fixar o eixo Y
                            title=dict(
                                text="Frequência",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickfont=dict(family="Arial", size=12, color="black")
                        )
                    })

                    # Média por população
                    dados_pop = df_filtrado[df_filtrado["População"] == populacao]["PMG"]

                    if len(dados_pop) == 0:
                        continue

                    media = dados_pop.mean()
                    xref = eixo_x.replace("axis", "")

                    # Linha da média
                    fig.add_shape(
                        type="line",
                        x0=media,
                        x1=media,
                        y0=0,
                        y1=1,
                        xref=xref,
                        yref="paper",
                        line=dict(color="red", width=2, dash="dash")
                    )

                    # Anotação da média
                    fig.add_annotation(
                        x=media,
                        y=1.05,
                        xref=xref,
                        yref="paper",
                        text=f"Média: {media:.1f} g",
                        showarrow=False,
                        yanchor="bottom",
                        font=dict(family="Arial Black", size=12, color="red"),
                        align="center"
                    )

                st.plotly_chart(fig, use_container_width=True)



            import numpy as np
            import pandas as pd
            import plotly.express as px

            # Boxplot 📦 População Final
            with st.expander("📦 Visualizar Boxplot de População Final", expanded=False):
                st.markdown("Boxplot da População Final por faixa de população. As médias e medianas ignoram valores zero e nulos.")

                populacao_order = [200, 250, 300, 350, 400]

                cores_populacao = {
                    200: "#1f77b4",
                    250: "#2ca02c",
                    300: "#ff7f0e",
                    350: "#9467bd",
                    400: "#8c564b"
                }

                # Filtra PMG não nulo e maior que zero
                df_filtrado = df_final_av7.copy()
                df_filtrado["Pop_Final"] = pd.to_numeric(df_filtrado["Pop_Final"], errors="coerce")
                df_filtrado = df_filtrado[df_filtrado["Pop_Final"].notna()]
                df_filtrado = df_filtrado[df_filtrado["Pop_Final"] > 0]

                fig = px.box(
                    df_filtrado,
                    y="Pop_Final",
                    color="População",
                    facet_col="População",
                    category_orders={"População": populacao_order},
                    color_discrete_map=cores_populacao,
                    points="outliers",
                    labels={"Pop_Final": "População Final"}
                )

                # Layout geral
                fig.update_layout(
                    showlegend=False,
                    height=600,
                    template="plotly_white"
                )

                # Títulos das facetas com média e mediana
                for annotation in fig.layout.annotations:
                    try:
                        pop_value = int(annotation.text.split("=")[-1])
                        dados = df_filtrado[df_filtrado["População"] == pop_value]["Pop_Final"]

                        if len(dados) > 0:
                            media = dados.mean()
                            mediana = dados.median()
                            annotation.text = (
                                f"População: {pop_value}<br>"
                                f"<span style='font-size:12px;color:#333;'>🔺 Mediana: {int(mediana/1000)}K</span><br>"
                                f"<span style='font-size:12px;color:red;'>🔻 Média: {int(media/1000)}K</span>"
                            )
                    except:
                        pass

                    annotation.font = dict(family="Arial Black", size=14, color="black")

                # Ajuste visual dos eixos
                for i, populacao in enumerate(populacao_order):
                    eixo_y = f"yaxis{i + 1 if i > 0 else ''}"

                    fig.update_layout({
                        eixo_y: dict(
                            range=[100000, 450000],
                            title=dict(
                                text="População Final",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickformat="~s",
                            tickfont=dict(family="Arial", size=12, color="black")
                        )
                    })

                # Exibe o gráfico
                st.plotly_chart(fig, use_container_width=True)

        
            
            import numpy as np
            import pandas as pd
            import plotly.express as px

            # Boxplot 📦 Produção (sc/ha)
            with st.expander("📦 Visualizar Boxplot de Produção (sc/ha)", expanded=False):
                st.markdown("Boxplot da Produção (sc/ha) por faixa de população, com média e mediana exibidas em cada faceta.")

                populacao_order = [200, 250, 300, 350, 400]

                cores_populacao = {
                    200: "#1f77b4",
                    250: "#2ca02c",
                    300: "#ff7f0e",
                    350: "#9467bd",
                    400: "#8c564b"
                }

                # Filtra produção válida
                df_filtrado = df_final_av7.copy()
                df_filtrado["prod_sc_ha"] = pd.to_numeric(df_filtrado["prod_sc_ha"], errors="coerce")
                df_filtrado = df_filtrado[df_filtrado["prod_sc_ha"].notna()]
                df_filtrado = df_filtrado[df_filtrado["prod_sc_ha"] > 0]

                fig = px.box(
                    df_filtrado,
                    y="prod_sc_ha",
                    color="População",
                    facet_col="População",
                    category_orders={"População": populacao_order},
                    color_discrete_map=cores_populacao,
                    points="outliers",
                    labels={"prod_sc_ha": "Produção (sc/ha)"}
                )

                fig.update_layout(
                    showlegend=False,
                    height=600,
                    template="plotly_white"
                )

                # Injeta média e mediana nos títulos das facetas
                for annotation in fig.layout.annotations:
                    try:
                        pop_value = int(annotation.text.split("=")[-1])
                        dados = df_filtrado[df_filtrado["População"] == pop_value]["prod_sc_ha"]

                        if len(dados) > 0:
                            media = dados.mean()
                            mediana = dados.median()
                            annotation.text = (
                                f"População: {pop_value}<br>"
                                f"<span style='font-size:12px;color:#333;'>🔺 Mediana: {mediana:.1f} sc/ha</span><br>"
                                f"<span style='font-size:12px;color:red;'>🔻 Média: {media:.1f} sc/ha</span>"
                            )
                    except:
                        pass

                    annotation.font = dict(family="Arial Black", size=14, color="black")

                # Eixos formatados
                for i, populacao in enumerate(populacao_order):
                    eixo_y = f"yaxis{i + 1 if i > 0 else ''}"

                    fig.update_layout({
                        eixo_y: dict(
                            range=[0, 120],
                            title=dict(
                                text="Produção (sc/ha)",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickfont=dict(family="Arial", size=12, color="black")
                        )
                    })

                # Exibe o gráfico
                st.plotly_chart(fig, use_container_width=True)



            # Boxplot 📦 PMG (Peso de Mil Grãos)
            with st.expander("📦 Visualizar Boxplot de PMG por Faixa de População", expanded=False):
                st.markdown("Boxplot do Peso de Mil Grãos (PMG) por faixa de população, com média e mediana exibidas.")

                populacao_order = [200, 250, 300, 350, 400]

                cores_populacao = {
                    200: "#1f77b4",
                    250: "#2ca02c",
                    300: "#ff7f0e",
                    350: "#9467bd",
                    400: "#8c564b"
                }

                # Filtra PMG válido
                df_filtrado = df_final_av7.copy()
                df_filtrado["PMG"] = pd.to_numeric(df_filtrado["PMG"], errors="coerce")
                df_filtrado = df_filtrado[df_filtrado["PMG"].notna()]
                df_filtrado = df_filtrado[df_filtrado["PMG"] > 0]

                fig = px.box(
                    df_filtrado,
                    y="PMG",
                    color="População",
                    facet_col="População",
                    category_orders={"População": populacao_order},
                    color_discrete_map=cores_populacao,
                    points="outliers",
                    labels={"PMG": "PMG (g)"}
                )

                fig.update_layout(
                    showlegend=False,
                    height=600,
                    template="plotly_white",
                )

                # Injeta mediana e média nos títulos das facetas
                for annotation in fig.layout.annotations:
                    try:
                        pop_value = int(annotation.text.split("=")[-1])
                        dados = df_filtrado[df_filtrado["População"] == pop_value]["PMG"]

                        if len(dados) > 0:
                            media = dados.mean()
                            mediana = dados.median()
                            annotation.text = (
                                f"População: {pop_value}<br>"
                                f"<span style='font-size:12px;color:#333;'>🔺 Mediana: {mediana:.1f} g</span><br>"
                                f"<span style='font-size:12px;color:red;'>🔻 Média: {media:.1f} g</span>"
                            )
                    except:
                        pass

                    annotation.font = dict(family="Arial Black", size=14, color="black")

                # Ajusta os eixos
                for i, populacao in enumerate(populacao_order):
                    eixo_y = f"yaxis{i + 1 if i > 0 else ''}"
                    fig.update_layout({
                        eixo_y: dict(
                            range=[0, 350],  # ajuste conforme necessário
                            title=dict(
                                text="PMG (g)",
                                font=dict(family="Arial Black", size=14, color="black")
                            ),
                            tickfont=dict(family="Arial", size=12, color="black")
                        )
                    })

                st.plotly_chart(fig, use_container_width=True)



































        




