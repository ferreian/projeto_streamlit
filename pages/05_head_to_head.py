import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go

from st_aggrid import AgGrid, GridOptionsBuilder

st.title("🌱 Avaliação AV7 - Tratamentos de Soja")
st.markdown("Explore os dados da avaliação AV7. Utilize os filtros para refinar a visualização dos dados.")

if "merged_dataframes" in st.session_state:
    df_av7 = st.session_state["merged_dataframes"].get("av7TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")

    if df_av7 is not None and not df_av7.empty:
        st.success("✅ Dados carregados com sucesso!")

        df_final_av7 = df_av7[~df_av7["displayName"].isin(["raullanconi", "stine"])].copy()

        # Cálculos adicionais
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

        colunas_selecionadas = [
            "nomeFazenda", "nomeProdutor", "regional", "nomeCidade", "codigoEstado", "nomeEstado",
            "dataPlantio", "dataColheita", "tipoTeste", "populacao", "indexTratamento", "nome", "gm",
            "areaParcela", "numeroPlantasMedio10m", "Pop_Final", "umidadeParcela", "producaoCorrigida",
            "producaoCorrigidaSc", "PMG_corrigido", "displayName", "cidadeRef", "fazendaRef", "ChaveFaixa"
        ]

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
            "indexTratamento": "Index",
            "areaParcela": "Area Parcela",
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
        df_final_av7 = df_final_av7[colunas_selecionadas].rename(columns=colunas_renomeadas)

        # Normaliza nomes das colunas para facilitar filtros
        df_final_av7.columns = df_final_av7.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

        # Normaliza texto de colunas
        df_final_av7["Produtor"] = df_final_av7["Produtor"].astype(str).str.upper()
        df_final_av7["Fazenda"] = df_final_av7["Fazenda"].astype(str).str.upper()

        df_final_av7["Cultivar"] = df_final_av7["Cultivar"].replace({
            "B�NUS IPRO": "BÔNUS IPRO",
            "DOM�NIO IPRO": "DOMÍNIO IPRO",
            "F�RIA CE": "FÚRIA CE",
            "V�NUS CE": "VÊNUS CE",
            "GH 2383 IPRO": "GH 2483 IPRO"
        })

        st.session_state["df_final_av7"] = df_final_av7

        # Filtros visuais
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
                if coluna in df_final_av7.columns:
                    if coluna == "GM":
                        valores_gm = df_final_av7["GM"].dropna().unique()
                        if len(valores_gm) > 0:
                            gm_min = int(df_final_av7["GM"].min())
                            gm_max = int(df_final_av7["GM"].max())
                            intervalo_gm = st.slider(
                                "Selecione intervalo de GM:",
                                min_value=gm_min,
                                max_value=gm_max,
                                value=(gm_min, gm_max),
                                step=1
                            )
                            df_final_av7 = df_final_av7[df_final_av7["GM"].between(intervalo_gm[0], intervalo_gm[1])]
                    else:
                        with st.expander(label):
                            opcoes = sorted(df_final_av7[coluna].dropna().unique())
                            selecionados = []
                            for op in opcoes:
                                op_str = str(op)
                                if st.checkbox(op_str, key=f"{coluna}_{op_str}", value=False):
                                    selecionados.append(op)
                            if selecionados:
                                df_final_av7 = df_final_av7[df_final_av7[coluna].isin(selecionados)]

        with col_tabela:
            st.markdown("### 📋 Tabela de Dados - AV7")
            colunas_visiveis = [
                "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index", "populacao", "GM",
                "Area Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
                "prod_kg_ha", "prod_sc_ha", "PMG"
            ]

            # Garante que só usa colunas que realmente existem
            colunas_visiveis = [col for col in colunas_visiveis if col in df_final_av7.columns]
            df_fmt = df_final_av7[colunas_visiveis].copy()
            

            # AgGrid
            gb = GridOptionsBuilder.from_dataframe(df_fmt)
            colunas_float = df_fmt.select_dtypes(include=["float"]).columns
            for col in colunas_float:
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
                df_fmt,
                gridOptions=gb.build(),
                height=600,
                custom_css=custom_css
            )

            # Botão de exportação 
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_fmt.to_excel(writer, sheet_name="dados_av7", index=False)
            st.download_button(
                label="📥 Baixar Dados AV7",
                data=buffer.getvalue(),
                file_name="dados_av7.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 🤜🏻🤛🏻 Análise Head to Head
            st.markdown("---")
            st.markdown("### ⚔️ Análise Head to Head entre Cultivares")

            if st.button("🔁 Rodar Análise Head to Head"):
                df_final_av7["Local"] = df_final_av7["Fazenda"] + "_" + df_final_av7["Cidade"]
                df_h2h = df_final_av7[["Local", "Cultivar", "prod_sc_ha"]].dropna()

                resultados_h2h = []

                for local, grupo in df_h2h.groupby("Local"):
                    cultivares = grupo["Cultivar"].unique()

                    for head in cultivares:
                        prod_head = grupo[grupo["Cultivar"] == head]["prod_sc_ha"].values
                        if len(prod_head) == 0:
                            continue

                        for check in cultivares:
                            if head == check:
                                continue

                            prod_check = grupo[grupo["Cultivar"] == check]["prod_sc_ha"].values
                            if len(prod_check) == 0:
                                continue

                            diff = prod_head[0] - prod_check[0]
                            win = int(diff > 0)

                            resultados_h2h.append({
                                "Head": head,
                                "Check": check,
                                "Head_Mean": round(prod_head[0], 1),
                                "Check_Mean": round(prod_check[0], 1),
                                "Difference": round(diff, 1),
                                "Number_of_Win": win,
                                "Percentage_of_Win": 100.0 if win else 0.0,
                                "Number_of_Comparison": 1,
                                "Local": local
                            })

                st.session_state["df_resultado_h2h"] = pd.DataFrame(resultados_h2h)
                st.success("✅ Análise concluída!")

            # 👉 Mostra o resultado se já tiver sido calculado
            if "df_resultado_h2h" in st.session_state:
                df_resultado_h2h = st.session_state["df_resultado_h2h"]
                st.dataframe(df_resultado_h2h, use_container_width=True)

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df_resultado_h2h.to_excel(writer, sheet_name="head_to_head", index=False)

                st.download_button(
                    label="📥 Baixar Resultado Head to Head",
                    data=buffer.getvalue(),
                    file_name="resultado_head_to_head.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # 🎯 Seletor de comparação Head to Head
                st.markdown("## 🎯 Selecione os cultivares para comparação Head to Head")

                cultivares_unicos = sorted(df_resultado_h2h["Head"].unique())

                col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

                with col1:
                    head_select = st.selectbox("Selecionar Cultivar Head", options=cultivares_unicos, key="head_select")

                with col2:
                    st.markdown("<h1 style='text-align: center;'>X</h1>", unsafe_allow_html=True)

                with col3:
                    check_select = st.selectbox("Selecionar Cultivar Check", options=cultivares_unicos, key="check_select")
                
                

                # 🎯 Métricas, Cartões e Gráficos
                if head_select and check_select and head_select != check_select:
                    df_selecionado = df_resultado_h2h[
                        (df_resultado_h2h["Head"] == head_select) &
                        (df_resultado_h2h["Check"] == check_select)
                    ]

                    num_locais = df_selecionado["Local"].nunique()
                    vitorias = df_selecionado[df_selecionado["Difference"] > 0].shape[0]
                    derrotas = df_selecionado[df_selecionado["Difference"] < 0].shape[0]

                    max_diff = df_selecionado["Difference"].max() if not df_selecionado.empty else 0
                    min_diff = df_selecionado["Difference"].min() if not df_selecionado.empty else 0
                    media_diff_vitorias = df_selecionado[df_selecionado["Difference"] > 0]["Difference"].mean() or 0
                    media_diff_derrotas = df_selecionado[df_selecionado["Difference"] < 0]["Difference"].mean() or 0

                    # 🔳 Cartões estilizados
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.markdown(f"""
                            <div style="background-color:#f2f2f2; padding:15px; border-radius:10px; text-align:center;">
                                <h5 style="font-weight:bold;">📍 Número de Locais</h5>
                                <div style="font-size: 20px; color:#f2f2f2;">Max: --</div>
                                <h2 style="margin: 10px 0; color:#333; font-size: 4em;">{num_locais}</h2>
                                <div style="font-size: 20px; color:#f2f2f2;">Média: --</div>
                            </div>
                        """, unsafe_allow_html=True)

                    with col5:
                        st.markdown(f"""
                            <div style="background-color:#d4edda; padding:15px; border-radius:10px; text-align:center;">
                                <h5 style="font-weight:bold;">✅ Vitórias</h5>
                                <div style="font-size: 20px; color:#155724;">Max: {max_diff:.1f} sc/ha</div>
                                <h2 style="margin: 10px 0; color:#155724; font-size: 4em;">{vitorias}</h2>
                                <div style="font-size: 20px; color:#155724;">Média: {media_diff_vitorias:.1f} sc/ha</div>
                            </div>
                        """, unsafe_allow_html=True)


                    with col6:
                        st.markdown(f"""
                            <div style="background-color:#f8d7da; padding:15px; border-radius:10px; text-align:center;">
                                <h5 style="font-weight:bold;">❌ Derrotas</h5>
                                <div style="font-size: 20px; color:#721c24;">Min: {min_diff:.1f} sc/ha</div>
                                <h2 style="margin: 10px 0; color:#721c24; font-size: 4em;">{derrotas}</h2>
                                <div style="font-size: 20px; color:#721c24;">Média: {media_diff_derrotas:.1f} sc/ha</div>
                            </div>
                        """, unsafe_allow_html=True)


                    # 📊 Gráfico em Pizza
                    col7, col8, col9 = st.columns([1, 2, 1])
                    with col8:
                        with st.container():
                            st.markdown("""
                                <div style="background-color: #f9f9f9; padding: 10px; border-radius: 12px; 
                                            box-shadow: 0px 2px 5px rgba(0,0,0,0.1); text-align: center;">
                                    <h4 style="margin-bottom: 0.5rem;">Resultado Geral do Head</h4>
                            """, unsafe_allow_html=True)

                            fig = go.Figure(
                                data=[go.Pie(
                                    labels=["Vitórias", "Derrotas"],
                                    values=[vitorias, derrotas],
                                    marker=dict(colors=["green", "red"]),
                                    hole=0.6,
                                    textinfo='label+percent',
                                    textposition='outside',
                                    textfont=dict(size=20, color="black", family="Arial Black"),
                                )]
                            )

                            fig.update_layout(
                                margin=dict(t=10, b=10, l=10, r=10),
                                height=270,
                                showlegend=False
                            )

                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                    # 📊 Gráfico de Barras - Diferença por Local
                    df_sorted = df_selecionado.sort_values(by="Difference")
                    cores = df_sorted["Difference"].apply(
                        lambda x: f"rgba(0, 128, 0, {min(1, abs(x)/10)})" if x > 0 else f"rgba(220, 20, 60, {min(1, abs(x)/10)})"
                    ).tolist()

                    fig_bar = go.Figure()
                    fig_bar.add_trace(go.Bar(
                        x=df_sorted["Local"],
                        y=df_sorted["Difference"],
                        marker_color=cores,
                        text=df_sorted["Difference"].round(1),
                        textposition="outside",
                        textfont=dict(size=20, color="black", family="Arial Black")
                    ))

                    fig_bar.update_layout(
                        title=dict(text="Diferença por Local", font=dict(size=20, color="black", family="Arial Black")),
                        xaxis=dict(
                            title=dict(text="Local", font=dict(size=20, color="black", family="Arial Black")),
                            tickfont=dict(size=20, color="black", family="Arial Black")
                        ),
                        yaxis=dict(
                            title=dict(text="Diferença (sc/ha)", font=dict(size=20, color="black", family="Arial Black")),
                            tickfont=dict(size=20, color="black", family="Arial Black")
                        ),
                        height=800,
                        margin=dict(t=50, b=80),
                        showlegend=False,
                        bargap=0.25
                    )

                    st.plotly_chart(fig_bar, use_container_width=True)           

            
    else:
        st.warning("⚠️ Dados de AV7 não encontrados ou estão vazios.")
else:
    st.error("❌ Dados não carregados. Volte à página principal e carregue os dados primeiro.")
