import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
import numpy as np


st.title("🎲 Floração dos Cultivares (AV3)")
st.markdown("Explore o florescimento dos cultivaes nas faixas avaliadas. Aplique filtros para visualizar os dados conforme necessário.")

# ✅ Verifica se df_av3 está carregado
if "merged_dataframes" in st.session_state:
    df_av3 = st.session_state["merged_dataframes"].get("av3TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")

    if df_av3 is not None and not df_av3.empty:
        df_florescimento = df_av3.copy()       

        # Renomeia colunas
        df_florescimento = df_florescimento.rename(columns={
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
            "dataInicioFloracao": "InicioFloracao",
            "dataFimFloracao": "FimFloracao",
            "corFlor": "CorFlor",
            "habitoCrescimento": "HC",          
            "nome": "Cultivar",            
            "cidadeRef": "CidadeRef",
            "fazendaRef": "FazendaRef",
            "displayName": "DTC"
        })

        # 🧮 Cria colunas auxiliares convertendo timestamps em segundos para datetime real
        for col in ["Plantio", "Colheita", "InicioFloracao", "FimFloracao"]:
            col_aux = col + "_aux"
            if col in df_florescimento.columns:
                df_florescimento[col_aux] = pd.to_numeric(df_florescimento[col], errors="coerce")

                # 🔒 Limita para intervalos plausíveis de datas (anos 2000 a 2100)
                df_florescimento.loc[
                    (df_florescimento[col_aux] < 946684800) |  # 01/01/2000
                    (df_florescimento[col_aux] > 4102444800),  # 01/01/2100
                    col_aux
                ] = pd.NaT

                df_florescimento[col_aux] = pd.to_datetime(df_florescimento[col_aux], unit="s", errors="coerce")


        # 🧮 Cálculo do DFAP: Colheita - InícioFloração (se ambos existirem)
        def calcular_dfap(row):
            inicio = row.get("InicioFloracao_aux")
            colheita = row.get("Colheita_aux")

            if pd.notnull(inicio) and pd.notnull(colheita):
                return (colheita - inicio).days
            else:
                return None

        df_florescimento["DFAP"] = df_florescimento.apply(calcular_dfap, axis=1)

        # 🧮 Cálculo do DAC: Colheita - Plantio
        df_florescimento["DAC"] = (
            df_florescimento["Colheita_aux"] - df_florescimento["Plantio_aux"]
        ).dt.days


        # 📆 Converte colunas originais para exibição no formato brasileiro
        for col in ["Plantio_aux", "Colheita_aux", "InicioFloracao_aux", "FimFloracao_aux"]:
            col_original = col.replace("_aux", "")
            df_florescimento[col_original] = df_florescimento[col].dt.strftime("%d/%m/%Y")

        # 🧹 Remove colunas auxiliares
        df_florescimento.drop(columns=["Plantio_aux", "Colheita_aux", "InicioFloracao_aux", "FimFloracao_aux"], inplace=True)
       

        

        # Normaliza texto
        df_florescimento["Produtor"] = df_florescimento["Produtor"].astype(str).str.upper()
        df_florescimento["Fazenda"] = df_florescimento["Fazenda"].astype(str).str.upper()

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

            if "Cultivar" in df_florescimento.columns:
                df_florescimento["Cultivar"] = df_florescimento["Cultivar"].replace(substituicoes)

            filtros = {
                "Microrregiao": "Microrregião",
                "Estado": "Estado",
                "Cidade": "Cidade",
                "Fazenda": "Fazenda",
                "Cultivar": "Cultivar",
                "GM": "GM"
            }

            for coluna, label in filtros.items():
                if coluna in df_florescimento.columns:

                    # 🔘 GM como slider (com checagem)
                    if coluna == "GM":
                        valores_gm = df_florescimento["GM"].dropna().unique()
                        if len(valores_gm) > 0:
                            gm_min = int(df_florescimento["GM"].min())
                            gm_max = int(df_florescimento["GM"].max())

                            if gm_min < gm_max:
                                intervalo_gm = st.slider(
                                    "Selecione intervalo de GM:",
                                    min_value=gm_min,
                                    max_value=gm_max,
                                    value=(gm_min, gm_max),
                                    step=1
                                )
                                df_florescimento = df_florescimento[
                                    df_florescimento["GM"].between(intervalo_gm[0], intervalo_gm[1])
                                ]
                            else:
                                st.info(f"Apenas um valor de GM disponível: **{gm_min}**")

                    # 🔲 Checkbox para os demais
                    else:
                        with st.expander(label):
                            opcoes = sorted(df_florescimento[coluna].dropna().unique())
                            selecionados = []
                            for op in opcoes:
                                op_str = str(op)
                                if st.checkbox(op_str, key=f"{coluna}_doenca_{op_str}", value=False):
                                    selecionados.append(op)
                            if selecionados:
                                df_florescimento = df_florescimento[df_florescimento[coluna].isin(selecionados)]

        with col_tabela:
            # 🔠 Ordena colunas visíveis
            ordem_desejada = [
                "Produtor", "Fazenda", "UF", "Estado", "Cidade", "Microrregiao",
                "Cultivar", "GM", "HC", "CorFlor", "Index", "Plantio", "Colheita",
                "InicioFloracao", "FimFloracao", "DFAP", "DAC"
            ]

            colunas_extra = [
                col for col in df_florescimento.columns
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

            st.markdown("### 📋 Tabela com Informações sobre o florescimento dos cultivares (AV3)")

            from st_aggrid import AgGrid, GridOptionsBuilder

            df_fmt = df_florescimento[colunas_visiveis].copy()

            substituicoes = {
                "B�NUS IPRO": "BÔNUS IPRO",
                "DOM�NIO IPRO": "DOMÍNIO IPRO",
                "F�RIA CE": "FÚRIA CE",
                "V�NUS CE": "VÊNUS CE",
                "GH 2383 IPRO": "GH 2483 IPRO"
            }
            df_fmt["Cultivar"] = df_fmt["Cultivar"].replace(substituicoes)

            gb = GridOptionsBuilder.from_dataframe(df_fmt)

            colunas_float = df_fmt.select_dtypes(include=["float", "int"]).columns
            for col in colunas_float:
                if col in ["GM_obs", "Ciclo_dias"]:
                    gb.configure_column(
                        field=col,
                        type=["numericColumn"],
                        valueFormatter="x.toFixed(0)"
                    )
                else:
                    gb.configure_column(
                        field=col,
                        type=["numericColumn"],
                        valueFormatter="x.toFixed(0)"
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
             ℹ️ **Legenda**: **CorFlor**: Cor predominante da flor observada, **HC**: Hábito de crescimento (e.g., determinado, indeterminado),
             **DFAP**: Dias de floração após plantio, **DAC**: Dias até colheita
            """)

            output_av6 = io.BytesIO()
            with pd.ExcelWriter(output_av6, engine="xlsxwriter") as writer:
                df_florescimento[colunas_visiveis].to_excel(writer, index=False, sheet_name="dados_doencas")

            st.download_button(
                label="📥 Baixar Dados de Florescimento (AV3)",
                data=output_av6.getvalue(),
                file_name="faixa_florescimento_av3.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
