import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go

from st_aggrid import AgGrid, GridOptionsBuilder

st.title("⚔️ Análise Head to Head")
st.markdown("Explore os dados da Ánalise Head to Head. Utilize os filtros para refinar a visualização dos dados.")

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

        # Corrige nomes corrompidos de cultivares
        substituicoes_cultivares = {
            "B�NUS IPRO": "BÔNUS IPRO",
            "DOM�NIO IPRO": "DOMÍNIO IPRO",
            "F�RIA CE": "FÚRIA CE",
            "V�NUS CE": "VÊNUS CE",
            "GH 2383 IPRO": "GH 2483 IPRO"
        }

        if "Cultivar" in df_final_av7.columns:
            df_final_av7["Cultivar"] = df_final_av7["Cultivar"].replace(substituicoes_cultivares)


        # Remove duplicadas para evitar repetição em análises futuras
        df_final_av7.drop_duplicates(inplace=True)

        st.session_state["df_final_av7"] = df_final_av7     


        # Filtros visuais
        col_filtros, col_tabela = st.columns([1.5, 8.5])

        with col_filtros:
            st.markdown("### 🎧 Filtros")
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
            st.markdown("### 📋 Tabela de Dados Utilizada na análise (AV7)")
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
            # 🤜🏻🤛🏻 Análise Head to Head
            st.markdown("---")
            st.markdown("### ⚔️ Análise Head to Head entre Cultivares")
            st.markdown("""
            <small>
            A Análise Head to Head compara o desempenho de dois cultivares em cada local de avaliação. 
            Ela mostra o número de vitórias, derrotas e empates (diferenças entre -1 e 1 sc/ha), 
            ajudando a entender qual cultivar teve melhor performance em diferentes condições.
            </small>
            """, unsafe_allow_html=True)

            # Botão para rodar análise
            if st.button("🔁 Rodar Análise Head to Head"):
                df_final_av7["Local"] = df_final_av7["Fazenda"] + "_" + df_final_av7["Cidade"]
                df_h2h = df_final_av7[["Local", "Cultivar", "prod_sc_ha", "Pop_Final", "Umidade (%)"]].dropna()

                resultados_h2h = []

                for local, grupo in df_h2h.groupby("Local"):
                    cultivares = grupo["Cultivar"].unique()

                    for head in cultivares:
                        head_row = grupo[grupo["Cultivar"] == head]
                        if head_row.empty:
                            continue

                        prod_head = head_row["prod_sc_ha"].values[0]
                        pop_head = head_row["Pop_Final"].values[0]
                        umid_head = head_row["Umidade (%)"].values[0]

                        for check in cultivares:
                            if head == check:
                                continue

                            check_row = grupo[grupo["Cultivar"] == check]
                            if check_row.empty:
                                continue

                            prod_check = check_row["prod_sc_ha"].values[0]
                            pop_check = check_row["Pop_Final"].values[0]
                            umid_check = check_row["Umidade (%)"].values[0]

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

                # 🔍 Lista de colunas visíveis (ajustável)
                colunas_visiveis = [
                    "Local", "Head", "Pop_Final_Head", "Umidade_Head", "Head_Mean",
                    "Check", "Pop_Final_Check", "Umidade_Check", "Check_Mean"                    
                ]
                #"Difference", "Number_of_Win", "Is_Draw", "Percentage_of_Win", "Number_of_Comparison"

                st.session_state["df_resultado_h2h"] = df_resultado_h2h
                st.session_state["colunas_visiveis_h2h"] = colunas_visiveis
                st.success("✅ Análise concluída!")

            
            # Exibição interativa da Tabela Head-to-Head
            if "df_resultado_h2h" in st.session_state:
                df_resultado_h2h = st.session_state["df_resultado_h2h"]
                colunas_visiveis = st.session_state.get("colunas_visiveis_h2h", df_resultado_h2h.columns.tolist())

                #

                import numpy as np

                # 🔽 Seletor para Head e Check
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

                    # Função JavaScript para colorir conforme o valor (escala de cor)
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
                            'fontSize': '16px'  // 👈 Aqui aumenta o tamanho
                        }
                    }
                    """)


                    # Configura AgGrid com estilo condicional JS
                    gb = GridOptionsBuilder.from_dataframe(df_h2h_fmt)

                    # 👉 Formatação padrão
                    gb.configure_column("Pop_Final_Head", type=["numericColumn"], valueFormatter="x.toFixed(0)")
                    gb.configure_column("Pop_Final_Check", type=["numericColumn"], valueFormatter="x.toFixed(0)")
                    gb.configure_column("Umidade_Head", type=["numericColumn"], valueFormatter="x.toFixed(1)")
                    gb.configure_column("Umidade_Check", type=["numericColumn"], valueFormatter="x.toFixed(1)")

                    # Colunas com cor gradiente
                    gb.configure_column("Head_Mean", type=["numericColumn"], valueFormatter="x.toFixed(1)", cellStyle=cell_style_js)
                    gb.configure_column("Check_Mean", type=["numericColumn"], valueFormatter="x.toFixed(1)", cellStyle=cell_style_js)

                    # Demais floats
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
                        height=600,
                        custom_css=custom_css,
                        allow_unsafe_jscode=True  # Habilita uso de JsCode
                    )

                else:
                    st.warning("⚠️ Nenhum dado disponível para essa combinação.")






                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df_resultado_h2h.to_excel(writer, sheet_name="head_to_head", index=False)

                st.download_button(
                    label="📅 Baixar Resultado Head to Head",
                    data=buffer.getvalue(),
                    file_name="resultado_head_to_head.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # ⬇️ Botão para baixar o df_filtrado
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df_filtrado.to_excel(writer, sheet_name="head_to_head_filtrado", index=False)

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

                   
                    # ⏹️ Cards de Resultados
                    col4, col5, col6, col7 = st.columns(4)

                    # 📍 Locais
                    with col4:
                        st.markdown(f"""
                            <div style="background-color:#f2f2f2; padding:15px; border-radius:10px; text-align:center;">
                                <h5 style="font-weight:bold; color:#333;">📍 Número de Locais</h5>
                                <div style="font-size: 20px; font-weight:bold; color:#f2f2f2;">&nbsp;</div>
                                <h2 style="margin: 10px 0; color:#333; font-weight:bold; font-size: 4em;">{num_locais}</h2>
                                <div style="font-size: 20px; font-weight:bold; color:#f2f2f2;">&nbsp;</div>
                            </div>
                        """, unsafe_allow_html=True)

                    # ✅ Vitórias
                    with col5:
                        st.markdown(f"""
                            <div style="background-color:#01B8AA80; padding:15px; border-radius:10px; text-align:center;">
                                <h5 style="font-weight:bold; color:#004d47;">✅ Vitórias</h5>
                                <div style="font-size: 20px; font-weight:bold; color:#004d47;">Max: {max_diff:.1f} sc/ha</div>
                                <h2 style="margin: 10px 0; color:#004d47; font-weight:bold; font-size: 4em;">{vitorias}</h2>
                                <div style="font-size: 20px; font-weight:bold; color:#004d47;">Média: {media_diff_vitorias:.1f} sc/ha</div>
                            </div>
                        """, unsafe_allow_html=True)

                    # ➖ Empates
                    with col6:
                        st.markdown(f"""
                            <div style="background-color:#F2C80F80; padding:15px; border-radius:10px; text-align:center;">
                                <h5 style="font-weight:bold; color:#8a7600;">➖ Empates</h5>
                                <div style="font-size: 20px; font-weight:bold; color:#8a7600;">Entre -1 e 1 sc/ha</div>
                                <h2 style="margin: 10px 0; color:#8a7600; font-weight:bold; font-size: 4em;">{empates}</h2>
                                <div style="font-size: 20px; font-weight:bold; color:#F2C80F80;">&nbsp;</div>
                            </div>
                        """, unsafe_allow_html=True)

                    # ❌ Derrotas
                    with col7:
                        st.markdown(f"""
                            <div style="background-color:#FD625E80; padding:15px; border-radius:10px; text-align:center;">
                                <h5 style="font-weight:bold; color:#7c1f1c;">❌ Derrotas</h5>
                                <div style="font-size: 20px; font-weight:bold; color:#7c1f1c;">Min: {min_diff:.1f} sc/ha</div>
                                <h2 style="margin: 10px 0; color:#7c1f1c; font-weight:bold; font-size: 4em;">{derrotas}</h2>
                                <div style="font-size: 20px; font-weight:bold; color:#7c1f1c;">Média: {media_diff_derrotas:.1f} sc/ha</div>
                            </div>
                        """, unsafe_allow_html=True)



                    st.markdown("")
                    
                    # 📊 Gráfico de Pizza
                    col7, col8, col9 = st.columns([1, 2, 1])
                    with col8:
                        st.markdown("""
                            <div style="background-color: #f9f9f9; padding: 10px; border-radius: 12px; 
                                        box-shadow: 0px 2px 5px rgba(0,0,0,0.1); text-align: center;">
                                <h4 style="margin-bottom: 0.5rem;">Resultado Geral do Head</h4>
                        """, unsafe_allow_html=True)

                        fig = go.Figure(data=[go.Pie(
                            labels=["Vitórias", "Empates", "Derrotas"],
                            values=[vitorias, empates, derrotas],
                            marker=dict(colors=["#01B8AA", "#F2C80F", "#FD625E"]),
                            hole=0.6,
                            textinfo='label+percent',
                            textposition='outside',
                            textfont=dict(size=20, color="black", family="Arial Black"),
                        )])

                        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=270, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)


                    
                    # 📊 Gráfico de Diferença por Local (Head vs Check) - Ordenado e Horizontal  
                    st.markdown(f"### <b>📊 Diferença de Produtividade por Local - {head_select} X {check_select}</b>", unsafe_allow_html=True)
                    st.markdown("")                    
                    st.markdown("### 📌 Dica: para melhor visualização dos rótulos, filtre para um número menor de locais.")


                    df_selecionado_sorted = df_selecionado.sort_values("Difference")

                    import plotly.graph_objects as go

                    fig_diff_local = go.Figure()

                    cores_local = df_selecionado["Difference"].apply(
                        lambda x: "#01B8AA" if x > 1 else "#FD625E" if x < -1 else "#F2C80F"
                    )

                    fig_diff_local.add_trace(go.Bar(
                        y=df_selecionado["Local"],
                        x=df_selecionado["Difference"],
                        orientation='h',
                        text=df_selecionado["Difference"].round(1),
                        textposition="outside",
                        textfont=dict(size=20, family="Arial Black", color="black"),  # Força negrito e tamanho 20
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
                        # 👉 Produtividade média do Head
                        prod_head_media = df_multi["Head_Mean"].mean().round(1)

                        # 🧷 Título atualizado com produtividade
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
                        resumo["Diferença Média"] = (resumo["% Vitórias"] - 50).round(1)

                        resumo = resumo[["Cultivar Check", "% Vitórias", "Num_Locais", "Prod_sc_ha_media", "Diferença Média"]]

                        col_tabela, col_grafico = st.columns([1.3, 1.7])
                        with col_tabela:
                            st.markdown("### 📊 Tabela Comparativa")
                            gb = GridOptionsBuilder.from_dataframe(resumo)
                            gb.configure_default_column(cellStyle={'fontSize': '14px'})
                            gb.configure_grid_options(headerHeight=30)
                            custom_css = {".ag-header-cell-label": {"font-weight": "bold", "font-size": "15px", "color": "black"}}
                            AgGrid(resumo, gridOptions=gb.build(), height=400, custom_css=custom_css)

                            buffer = io.BytesIO()
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










                




            
    else:
        st.warning("⚠️ Dados de AV7 não encontrados ou estão vazios.")
else:
    st.error("❌ Dados não carregados. Volte à página principal e carregue os dados primeiro.")
