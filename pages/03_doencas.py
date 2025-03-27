import streamlit as st
import pandas as pd
import io

st.title("🦠 Avaliação de Doenças (AV2)")
st.markdown("Explore as notas de doenças em faixas avaliadas. Aplique filtros para visualizar os dados conforme necessário.")

# ✅ Verifica se df_av2 está carregado
if "merged_dataframes" in st.session_state:
    df_av2 = st.session_state["merged_dataframes"].get("av2TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")

    if df_av2 is not None and not df_av2.empty:
        df_doencas = df_av2.copy()

        # 🚧 Tratamento de valores 0 -> 9
        TRATAR_ZERO_COMO_9 = True
        colunas_doencas = [
            "nota1NivelPhytophthora",
            "nota2NivelAnomalia",
            "nota3NivelOidio",
            "nota4NivelManchaParda",
            "nota5NivelManchaAlvo",
            "nota6NivelManchaOlhoRa",
            "nota7NivelCercospora",
            "nota8NivelAntracnose",
            "nota8NivelDfc"
        ]
        if TRATAR_ZERO_COMO_9:
            for col in colunas_doencas:
                if col in df_doencas.columns:
                    df_doencas[col] = df_doencas[col].replace(0, 9)

        # Renomeia colunas
        df_doencas = df_doencas.rename(columns={
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
            "nota1NivelPhytophthora": "PHY",
            "nota2NivelAnomalia": "ANO",
            "nota3NivelOidio": "OID",
            "nota4NivelManchaParda": "MPA",
            "nota5NivelManchaAlvo": "MAL",
            "nota6NivelManchaOlhoRa": "MOR",
            "nota7NivelCercospora": "CER",
            "nota8NivelAntracnose": "ANT",
            "nota8NivelDfc": "DFC",
            "cidadeRef": "CidadeRef",
            "fazendaRef": "FazendaRef",
            "displayName": "DTC"
        })

        df_doencas = df_doencas[df_doencas["Teste"] == "Faixa"]

        # Normaliza texto
        df_doencas["Produtor"] = df_doencas["Produtor"].astype(str).str.upper()
        df_doencas["Fazenda"] = df_doencas["Fazenda"].astype(str).str.upper()

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

            if "Cultivar" in df_doencas.columns:
                df_doencas["Cultivar"] = df_doencas["Cultivar"].replace(substituicoes)

            filtros = {
                "Microrregiao": "Microrregião",
                "Estado": "Estado",
                "Cidade": "Cidade",
                "Fazenda": "Fazenda",
                "Cultivar": "Cultivar",
                "GM": "GM"
            }

            for coluna, label in filtros.items():
                if coluna in df_doencas.columns:

                    # 🔘 GM como slider
                    if coluna == "GM":
                        valores_gm = df_doencas["GM"].dropna().unique()
                        if len(valores_gm) > 0:
                            gm_min = int(df_doencas["GM"].min())
                            gm_max = int(df_doencas["GM"].max())
                            intervalo_gm = st.slider(
                                "Selecione intervalo de GM:",
                                min_value=gm_min,
                                max_value=gm_max,
                                value=(gm_min, gm_max),
                                step=1
                            )
                            df_doencas = df_doencas[
                                df_doencas["GM"].between(intervalo_gm[0], intervalo_gm[1])
                            ]

                    # 🔲 Checkbox para os demais
                    else:
                        with st.expander(label):
                            opcoes = sorted(df_doencas[coluna].dropna().unique())
                            selecionados = []
                            for op in opcoes:
                                op_str = str(op)
                                if st.checkbox(op_str, key=f"{coluna}_doenca_{op_str}", value=False):
                                    selecionados.append(op)
                            if selecionados:
                                df_doencas = df_doencas[df_doencas[coluna].isin(selecionados)]



        with col_tabela:
            colunas_visiveis = [
                "Produtor", "Fazenda", "UF", "Estado", "Cidade", "Microrregiao",
                "Cultivar", "GM", "Index"
            ] + [col for col in df_doencas.columns if col not in [
                "uuid_x", "dataSync", "acao", "cultivar", "populacao",
                "avaliacaoRef", "idBaseRef", "firebase", "uuid_y",
                "FazendaRef", "tipoAvaliacao", "avaliado", "latitude",
                "longitude", "altitude", "dataPlantio", "dataColheita",
                "dtcResponsavelRef", "CidadeRef", "estadoRef",
                "ChaveFaixa", "DTC", "Teste"
            ] and col not in [
                "Produtor", "Fazenda", "UF", "Estado", "Cidade", "Microrregiao",
                "Cultivar", "GM", "Index"
            ]]

            st.markdown("### 📋 Tabela de Doenças (AV2)")

            from st_aggrid import AgGrid, GridOptionsBuilder

            # Copia o DataFrame que vai ser exibido
            df_fmt = df_doencas[colunas_visiveis].copy()

            # 🔠 Substituição nos nomes das cultivares
            substituicoes = {
                "B�NUS IPRO": "BÔNUS IPRO",
                "DOM�NIO IPRO": "DOMÍNIO IPRO",
                "F�RIA CE": "FÚRIA CE",
                "V�NUS CE": "VÊNUS CE",
                "GH 2383 IPRO": "GH 2483 IPRO"
            }
            df_fmt["Cultivar"] = df_fmt["Cultivar"].replace(substituicoes)

            # Cria o builder do grid
            gb = GridOptionsBuilder.from_dataframe(df_fmt)

            # Aplica formatação visual para colunas float (1 casa decimal)
            colunas_float = df_fmt.select_dtypes(include=["float"]).columns
            for col in colunas_float:
                gb.configure_column(
                    field=col,
                    type=["numericColumn"],
                    valueFormatter="x.toFixed(1)"
                )

            # Tamanho da fonte das células
            gb.configure_default_column(cellStyle={'fontSize': '14px'})

            # Ajusta altura do cabeçalho
            gb.configure_grid_options(headerHeight=30)

            # Estilo do cabeçalho (negrito, fonte preta, tamanho 15px)
            custom_css = {
                ".ag-header-cell-label": {
                    "font-weight": "bold",
                    "font-size": "15px",
                    "color": "black"
                }
            }

            # Renderiza o grid
            AgGrid(
                df_fmt,
                gridOptions=gb.build(),
                height=600,
                custom_css=custom_css
            )







            # ℹ️ Legenda das siglas
            st.markdown(
                "**ℹ️ Legenda:** "
                "**PHY** - Phytophthora; "
                "**ANO** - Anomalia; "
                "**OID** - Oídio; "
                "**MPA** - Mancha Parda; "
                "**MAL** - Mancha Alvo; "
                "**MOR** - Mancha Olho de Rã; "
                "**CER** - Cercospora; "
                "**ANT** - Antracnose; "
                "**DFC** - Doenças Final de Ciclo"
            )     
                        

            # 📥 Exportar
            output_av2 = io.BytesIO()
            with pd.ExcelWriter(output_av2, engine="xlsxwriter") as writer:
                df_doencas[colunas_visiveis].to_excel(writer, index=False, sheet_name="dados_doencas")

            st.download_button(
                label="📥 Baixar Dados de Doenças (AV2)",
                data=output_av2.getvalue(),
                file_name="faixa_doencas_av2.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            col_esquerda, col_direita = st.columns([0.85, 0.15])

            # 👉 Coluna de seleção com checkboxes (do lado direito)
            col_esquerda, col_direita = st.columns([0.9, 0.1])

            with col_direita:
                st.markdown("### ")
                st.caption("🎯 **Selecione as doenças para visualizar**:")

                doencas_codigos = ["PHY", "ANO", "OID", "MPA", "MAL", "MOR", "CER", "ANT", "DFC"]
                codigos_selecionados = []

                for cod in doencas_codigos:
                    if st.checkbox(cod, value=False, key=f"doenca_{cod}"):
                        codigos_selecionados.append(cod)


            with col_esquerda:
                if not df_doencas.empty:
                    colunas_doencas = ["PHY", "ANO", "OID", "MPA", "MAL", "MOR", "CER", "ANT", "DFC"]
                    colunas_presentes = [col for col in colunas_doencas if col in df_doencas.columns]

                    # 📊 Estatísticas principais
                    resumo = df_doencas.groupby("Cultivar").agg(
                        GM=("GM", "first"),
                        **{f"{col}_mean": (col, "mean") for col in colunas_presentes},
                        **{f"{col}_min": (col, "min") for col in colunas_presentes},
                        **{f"{col}_max": (col, "max") for col in colunas_presentes},
                    ).round(1).reset_index()

                    df_resumo_doencas = resumo.copy()


                    # ➕ Incidência %
                    for col in colunas_presentes:
                        total = df_doencas.groupby("Cultivar")[col].count()
                        abaixo_6 = df_doencas[df_doencas[col] < 6].groupby("Cultivar")[col].count()
                        incidencia = ((abaixo_6 / total) * 100).round(1).reindex(total.index).fillna(0)
                        df_resumo_doencas[f"{col}_inc_per"] = df_resumo_doencas["Cultivar"].map(incidencia)

                    # 🔢 Ordena colunas
                    ordem_colunas = [
                        "Cultivar",
                        "GM",
                        "PHY_mean", "PHY_min", "PHY_max", "PHY_inc_per",
                        "ANO_mean", "ANO_min", "ANO_max", "ANO_inc_per",
                        "OID_mean", "OID_min", "OID_max", "OID_inc_per",
                        "MPA_mean", "MPA_min", "MPA_max", "MPA_inc_per",
                        "MAL_mean", "MAL_min", "MAL_max", "MAL_inc_per",
                        "MOR_mean", "MOR_min", "MOR_max", "MOR_inc_per",
                        "CER_mean", "CER_min", "CER_max", "CER_inc_per",
                        "ANT_mean", "ANT_min", "ANT_max", "ANT_inc_per",
                        "DFC_mean", "DFC_min", "DFC_max", "DFC_inc_per"
                    ]

                    ordem_final = [col for col in ordem_colunas if col in df_resumo_doencas.columns]

                    # 🎯 Filtra conforme seleção
                    if codigos_selecionados:
                        colunas_filtradas = ["Cultivar"]
                        for cod in codigos_selecionados:
                            colunas_filtradas += [col for col in ordem_final if col.startswith(cod)]
                        df_mostrar = df_resumo_doencas[colunas_filtradas]
                    else:
                        df_mostrar = df_resumo_doencas[ordem_final]

                    # 🔠 Substituições nos nomes das cultivares
                    substituicoes = {
                        "B�NUS IPRO": "BÔNUS IPRO",
                        "DOM�NIO IPRO": "DOMÍNIO IPRO",
                        "F�RIA CE": "FÚRIA CE",
                        "V�NUS CE": "VÊNUS CE",
                        "GH 2383 IPRO": "GH 2483 IPRO"
                    }
                    df_mostrar["Cultivar"] = df_mostrar["Cultivar"].replace(substituicoes)

                    st.markdown("### 📊 Resumo por Cultivar (Média, Mínimo, Máximo e Incidência %)")

                    # ⬇️ Continua com o AgGrid normalmente
                    from st_aggrid import AgGrid, GridOptionsBuilder

                    df_fmt = df_mostrar.copy()
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

                    # 👇 Botão de exportação
                    import io

                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                        df_mostrar.to_excel(writer, sheet_name="Resumo Doenças", index=False)
                        writer.close()
                        st.download_button(
                            label="📥 Baixar Resumo Doenças",
                            data=buffer,
                            file_name="resumo_doencas.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )


                   


#=================================================================================================================================




    else:
        st.warning("⚠️ Dados de AV2 (Doenças) não encontrados ou estão vazios.")
else:
    st.error("❌ Dados não carregados. Volte à página principal e carregue os dados primeiro.")
