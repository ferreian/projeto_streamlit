import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
import numpy as np

st.title("🎲 Ciclo dos Cultivares (AV6)")
st.markdown("Explore o ciclo dos cultivares nas faixas avaliadas. Aplique filtros para visualizar os dados conforme necessário.")

if "merged_dataframes" in st.session_state:
    df_av6 = st.session_state["merged_dataframes"].get("av6TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")

    if df_av6 is not None and not df_av6.empty:
        df_ciclo = df_av6.copy()

        df_ciclo = df_ciclo.rename(columns={
            "nomeFazenda": "Fazenda",
            "nomeProdutor": "Produtor",
            "codigoEstado": "Estado",
            "nomeEstado": "UF",
            "nomeCidade": "Cidade",
            "regional": "Microrregiao",
            "tipoTeste": "Teste",
            "dataPlantio": "Plantio",
            "dataColheita": "Colheita",
            "indexTratamento": "Index",
            "gm": "GM",
            "gmVisual": "GM_obs",
            "dataMaturacaoFisiologica": "MAT",
            "nivelAcamenamento": "AC",
            "aberturaVagens": "ABV",
            "qualidadeFinalPlot": "QF",
            "nome": "Cultivar",
            "cidadeRef": "CidadeRef",
            "fazendaRef": "FazendaRef",
            "displayName": "DTC"
        })


        # 🔢 Corrige GM para inteiro (sem casas decimais)
        if "GM" in df_ciclo.columns:
            df_ciclo["GM"] = pd.to_numeric(df_ciclo["GM"], errors="coerce").round().astype("Int64")



        for col in ["AC", "ABV"]:
            df_ciclo[col] = pd.to_numeric(df_ciclo[col], errors="coerce").fillna(0)
            df_ciclo[col] = df_ciclo[col].apply(lambda x: 9 if x == 0 else x).astype(int)

        for col in ["Plantio", "Colheita", "MAT"]:
            col_aux = col + "_aux"
            if col in df_ciclo.columns:
                df_ciclo[col_aux] = pd.to_numeric(df_ciclo[col], errors="coerce")
                df_ciclo.loc[
                    (df_ciclo[col_aux] < 946684800) | (df_ciclo[col_aux] > 4102444800), col_aux
                ] = pd.NaT
                df_ciclo[col_aux] = pd.to_datetime(df_ciclo[col_aux], unit="s", errors="coerce")

        df_ciclo["Ciclo_dias"] = (df_ciclo["MAT_aux"] - df_ciclo["Plantio_aux"]).dt.days + 5

        for col in ["Plantio_aux", "Colheita_aux", "MAT_aux"]:
            col_original = col.replace("_aux", "")
            df_ciclo[col_original] = df_ciclo[col].dt.strftime("%d/%m/%Y")

        df_ciclo.drop(columns=["Plantio_aux", "Colheita_aux", "MAT_aux"], inplace=True)

        df_ciclo = df_ciclo[df_ciclo["Teste"] == "Faixa"]
        df_ciclo["Produtor"] = df_ciclo["Produtor"].astype(str).str.upper()
        df_ciclo["Fazenda"] = df_ciclo["Fazenda"].astype(str).str.upper()

        


        # 🔍 Layout com filtros
        col_filtros, col_tabela = st.columns([1.5, 8.5])

        with col_filtros:
            st.markdown("### 🎛️ Filtros")

            # 🛠️ Substituições nas cultivares
            substituicoes = {
                "B�NUS IPRO": "BÔNUS IPRO",
                "DOM�NIO IPRO": "DOMÍNIO IPRO",
                "F�RIA CE": "FÚRIA CE",
                "V�NUS CE": "VÊNUS CE",
                "GH 2383 IPRO": "GH 2483 IPRO"
            }

            if "Cultivar" in df_ciclo.columns:
                df_ciclo["Cultivar"] = df_ciclo["Cultivar"].replace(substituicoes)

            filtros = {
                "Microrregiao": "Microrregião",
                "Estado": "Estado",
                "Cidade": "Cidade",
                "Fazenda": "Fazenda",
                "Cultivar": "Cultivar",
                "GM": "GM"
            }

            for coluna, label in filtros.items():
                if coluna in df_ciclo.columns:

                    
                    # 🔘 GM como slider (com checagem)
                    if coluna == "GM":
                        valores_gm = df_ciclo["GM"].dropna().unique()
                        if len(valores_gm) > 0:
                            gm_min = int(df_ciclo["GM"].min())
                            gm_max = int(df_ciclo["GM"].max())
                            
                            if gm_min < gm_max:
                                intervalo_gm = st.slider(
                                    "Selecione intervalo de GM:",
                                    min_value=gm_min,
                                    max_value=gm_max,
                                    value=(gm_min, gm_max),
                                    step=1
                                )
                                df_ciclo = df_ciclo[
                                    df_ciclo["GM"].between(intervalo_gm[0], intervalo_gm[1])
                                ]
                            else:
                                st.info(f"Apenas um valor de GM disponível: **{gm_min}**")


                    # 🔲 Checkbox para os demais
                    else:
                        with st.expander(label):
                            opcoes = sorted(df_ciclo[coluna].dropna().unique())
                            selecionados = []
                            for op in opcoes:
                                op_str = str(op)
                                if st.checkbox(op_str, key=f"{coluna}_doenca_{op_str}", value=False):
                                    selecionados.append(op)
                            if selecionados:
                                df_ciclo = df_ciclo[df_ciclo[coluna].isin(selecionados)]



        with col_tabela:
            # 🔠 Ordena colunas visíveis
            ordem_desejada = [
                "Produtor", "Fazenda", "UF", "Estado", "Cidade", "Microrregiao",
                "Cultivar", "GM","GM_obs", "Index", "Plantio", "Colheita","MAT","Ciclo_dias", "AC", "ABV", "QF"
            ]

            # Pega as colunas extras (excluindo as desnecessárias e já incluídas)
            colunas_extra = [
                col for col in df_ciclo.columns
                if col not in [
                    "uuid_x", "dataSync", "acao", "cultivar", "populacao",
                    "avaliacaoRef", "idBaseRef", "firebase", "uuid_y",
                    "FazendaRef", "tipoAvaliacao", "avaliado", "latitude",
                    "longitude", "altitude", "dataPlantio", "dataColheita",
                    "dtcResponsavelRef", "CidadeRef", "estadoRef",
                    "ChaveFaixa", "DTC", "Teste"
                ] and col not in ordem_desejada
            ]

            colunas_visiveis = ordem_desejada + colunas_extra

            st.markdown("### 📋 Tabela com o ciclo dos cultivares (AV6)")

            from st_aggrid import AgGrid, GridOptionsBuilder

            df_fmt = df_ciclo[colunas_visiveis].copy()
            df_fmt["GM"] = pd.to_numeric(df_fmt["GM"], errors="coerce").round().astype("Int64")

            # Substituições nos nomes das cultivares
            substituicoes = {
                "B�NUS IPRO": "BÔNUS IPRO",
                "DOM�NIO IPRO": "DOMÍNIO IPRO",
                "F�RIA CE": "FÚRIA CE",
                "V�NUS CE": "VÊNUS CE",
                "GH 2383 IPRO": "GH 2483 IPRO"
            }
            df_fmt["Cultivar"] = df_fmt["Cultivar"].replace(substituicoes)

            gb = GridOptionsBuilder.from_dataframe(df_fmt)

            # ✅ Corrige exibição da GM sem decimal
            gb.configure_column("GM", type=["numericColumn"], valueFormatter="x.toFixed(0)")

            # Demais colunas numéricas
            colunas_float = df_fmt.select_dtypes(include=["float", "int"]).columns
            for col in colunas_float:
                if col in ["GM_obs", "Ciclo_dias"]:
                    gb.configure_column(
                        field=col,
                        type=["numericColumn"],
                        valueFormatter="x.toFixed(0)"  # Inteiro
                    )
                elif col != "GM":  # 👈 Evita sobrescrever a GM
                    gb.configure_column(
                        field=col,
                        type=["numericColumn"],
                        valueFormatter="x.toFixed(1)"  # Float com 1 casa
                    )


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
                df_fmt,
                gridOptions=gb.build(),
                height=600,
                custom_css=custom_css
            )
            
            st.markdown("""            
             ℹ️ **Legenda**: **MAT**: Data da maturação fisiológica do cultivar, **Ciclo_dias**: MAT - Plantio (descontado o período médio de germinação de 5 dias),
                **AC**: Nível de acamamento, **ABV**: Nota de abertura de vagens.             
            """)
           

            # 📥 Exportar
            output_av6 = io.BytesIO()
            with pd.ExcelWriter(output_av6, engine="xlsxwriter") as writer:
                df_ciclo[colunas_visiveis].to_excel(writer, index=False, sheet_name="dados_doencas")

            st.download_button(
                label="📥 Baixar Dados de Ciclo (AV6)",
                data=output_av6.getvalue(),
                file_name="faixa_ciclo_av6.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 📊 Resumo por Cultivar com Mínimo e Máximo
            st.markdown("---")
            st.markdown("### 📊 Resumo do Ciclo por Cultivar")

            # 🧮 Agrupa e calcula as estatísticas
            df_resumo = df_ciclo.groupby(["Cultivar", "GM"]).agg({
                "Ciclo_dias": ["mean", "min", "max"],
                "AC": "mean",
                "ABV": "mean"
            }).reset_index()

            # 🔁 Ajusta MultiIndex das colunas
            df_resumo.columns = ["Cultivar", "GM", "Ciclo_dias_media", "Ciclo_dias_min", "Ciclo_dias_max", "AC_media", "ABV_media"]

            # 🎯 Arredonda e converte para inteiro
            col_arredondar = ["Ciclo_dias_media", "Ciclo_dias_min", "Ciclo_dias_max", "AC_media", "ABV_media"]
            df_resumo[col_arredondar] = df_resumo[col_arredondar].round(0).astype("Int64")

            # 🧱 Mostra no AgGrid
            from st_aggrid import GridOptionsBuilder, AgGrid

            gb_resumo = GridOptionsBuilder.from_dataframe(df_resumo)
            gb_resumo.configure_default_column(cellStyle={'fontSize': '14px'})
            gb_resumo.configure_grid_options(headerHeight=30)

            # Estilo do cabeçalho em negrito
            custom_css_resumo = {
                ".ag-header-cell-label": {
                    "font-weight": "bold",
                    "font-size": "15px",
                    "color": "black"
                }
            }

            AgGrid(
                df_resumo,
                gridOptions=gb_resumo.build(),
                height=400,
                custom_css=custom_css_resumo
            )

            # 📥 Exportar resumo com min/max
            output_resumo = io.BytesIO()
            with pd.ExcelWriter(output_resumo, engine="xlsxwriter") as writer:
                df_resumo.to_excel(writer, index=False, sheet_name="resumo_ciclo")

            st.download_button(
                label="📥 Baixar Resumo Ciclo",
                data=output_resumo.getvalue(),
                file_name="resumo_ciclo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


            # 📊 Histograma de Ciclo_dias
            with st.expander("📊 Visualizar Histograma do Ciclo (dias)", expanded=False):
                df_hist = df_ciclo.copy()
                df_hist = df_hist[df_hist["Ciclo_dias"].notna()]
                df_hist = df_hist[df_hist["Ciclo_dias"] > 0]
                df_hist["Ciclo_dias"] = pd.to_numeric(df_hist["Ciclo_dias"], errors="coerce")

                x_data = df_hist["Ciclo_dias"].dropna()
                x_data = x_data[x_data > 0]

                fig_hist = go.Figure()

                fig_hist.add_trace(go.Histogram(
                    x=x_data,
                    nbinsx=50,
                    name="Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y"
                ))

                # Curva de densidade
                if len(x_data) > 1 and x_data.std() > 0:
                    kde = gaussian_kde(x_data)
                    x_vals = np.linspace(x_data.min(), x_data.max(), 500)
                    y_vals = kde(x_vals)

                    fig_hist.add_trace(go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode="lines",
                        name="Densidade",
                        line=dict(color="darkblue", width=2),
                        yaxis="y2"
                    ))
                else:
                    st.warning("⚠️ Dados insuficientes ou sem variação para calcular a curva de densidade.")

                # Linha da média
                media = x_data.mean()
                fig_hist.add_trace(go.Scatter(
                    x=[media, media],
                    y=[0, y_vals.max() if len(x_data) > 1 and x_data.std() > 0 else 1],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # Layout
                font_bold = dict(size=16, family="Arial Bold", color="black")

                fig_hist.update_layout(
                    title=dict(text="Histograma do Ciclo (dias)", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Ciclo (dias)", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        showgrid=True,
                        gridcolor="lightgray",
                    ),
                    yaxis=dict(
                        title=dict(text="Frequência", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        showgrid=True,
                        gridcolor="lightgray"
                    ),
                    yaxis2=dict(
                        title=dict(text="Densidade", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        overlaying="y",
                        side="right",
                        showgrid=False
                    ),
                    plot_bgcolor="white",
                    bargap=0.1,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=16, family="Arial", color="black")
                    )
                )

                st.plotly_chart(fig_hist, use_container_width=True)
            


            ## 📊 Histograma de Abertura de Vagens (ABV)
            with st.expander("📊 Visualizar Histograma de Abertura de Vagens (ABV)", expanded=False):
                df_hist = df_ciclo.copy()
                df_hist = df_hist[df_hist["ABV"].notna()]
                df_hist = df_hist[df_hist["ABV"] > 0]
                df_hist["Ciclo_dias"] = pd.to_numeric(df_hist["ABV"], errors="coerce")

                x_data = df_hist["ABV"].dropna()
                x_data = x_data[x_data > 0]

                fig_hist = go.Figure()

                fig_hist.add_trace(go.Histogram(
                    x=x_data,
                    nbinsx=50,
                    name="Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y"
                ))

                # Curva de densidade
                if len(x_data) > 1 and x_data.std() > 0:
                    kde = gaussian_kde(x_data)
                    x_vals = np.linspace(x_data.min(), x_data.max(), 500)
                    y_vals = kde(x_vals)

                    fig_hist.add_trace(go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode="lines",
                        name="Densidade",
                        line=dict(color="darkblue", width=2),
                        yaxis="y2"
                    ))
                else:
                    st.warning("⚠️ Dados insuficientes ou sem variação para calcular a curva de densidade.")

                # Linha da média
                media = x_data.mean()
                fig_hist.add_trace(go.Scatter(
                    x=[media, media],
                    y=[0, y_vals.max() if len(x_data) > 1 and x_data.std() > 0 else 1],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # Layout
                font_bold = dict(size=16, family="Arial Bold", color="black")

                fig_hist.update_layout(
                    title=dict(text="Histograma de Abertura de Vagens (ABV)", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Abertura de Vagens (ABV)", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        showgrid=True,
                        gridcolor="lightgray",
                    ),
                    yaxis=dict(
                        title=dict(text="Frequência", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        showgrid=True,
                        gridcolor="lightgray"
                    ),
                    yaxis2=dict(
                        title=dict(text="Densidade", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        overlaying="y",
                        side="right",
                        showgrid=False
                    ),
                    plot_bgcolor="white",
                    bargap=0.1,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=16, family="Arial", color="black")
                    )
                )

                st.plotly_chart(fig_hist, use_container_width=True)

            # 📦 Boxplot de Ciclo_dias
            media_ciclo = df_ciclo["Ciclo_dias"].dropna().mean()

            with st.expander("📦 Visualizar Box Plot de Ciclo em Dias", expanded=False):
                fig_box_ciclo = go.Figure()

                fig_box_ciclo.add_trace(go.Box(
                    x=df_ciclo["Ciclo_dias"],
                    name="Ciclo (dias)",
                    boxpoints="outliers",
                    fillcolor="lightblue",
                    marker_color="lightblue",
                    line=dict(color="black", width=1),
                    boxmean=True
                ))

                # Estilo dos textos
                font_bold = dict(size=20, family="Arial Bold", color="black")

                fig_box_ciclo.update_layout(
                    title=dict(
                        text="Box Plot do Ciclo em Dias",
                        font=font_bold
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Ciclo em Dias",
                            font=font_bold
                        ),
                        tickfont=font_bold,
                        showgrid=True,
                        gridcolor="lightgray"
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Observações",
                            font=font_bold
                        ),
                        tickfont=font_bold,
                        showgrid=True,
                        gridcolor="lightgray"
                    ),
                    legend=dict(
                        font=font_bold,
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    plot_bgcolor="white",
                    showlegend=True
                )

                st.plotly_chart(fig_box_ciclo, use_container_width=True)

            # 📦 Boxplot de Abertura de Vagens (ABV)
            
            media_ciclo = df_ciclo["ABV"].dropna().mean()

            with st.expander("📦 Visualizar Box Plot de Abertura de Vagens", expanded=False):
                fig_box_ciclo = go.Figure()

                fig_box_ciclo.add_trace(go.Box(
                    x=df_ciclo["ABV"],
                    name="Abertura de Vagens",
                    boxpoints="outliers",
                    fillcolor="lightblue",
                    marker_color="lightblue",
                    line=dict(color="black", width=1),
                    boxmean=True
                ))

                # Estilo dos textos
                font_bold = dict(size=20, family="Arial Bold", color="black")

                fig_box_ciclo.update_layout(
                    title=dict(
                        text="Box Plot de Abertura de Vagens (ABV)",
                        font=font_bold
                    ),
                    xaxis=dict(
                        title=dict(
                            text="Abertura de Vagens",
                            font=font_bold
                        ),
                        tickfont=font_bold,
                        showgrid=True,
                        gridcolor="lightgray"
                    ),
                    yaxis=dict(
                        title=dict(
                            text="Observações",
                            font=font_bold
                        ),
                        tickfont=font_bold,
                        showgrid=True,
                        gridcolor="lightgray"
                    ),
                    legend=dict(
                        font=font_bold,
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    plot_bgcolor="white",
                    showlegend=True
                )

                st.plotly_chart(fig_box_ciclo, use_container_width=True)




           