import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
import io

st.title("📊 Resultados de Produção")
st.markdown(
    "Breve descriçao - Nesta página, você pode visualizar os resultados de produção de soja, incluindo a faixa de densidade e os resultados de cada faixa."
)

if "merged_dataframes" in st.session_state:
    df_av7 = st.session_state["merged_dataframes"].get("av7TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")
    df_av6 = st.session_state["merged_dataframes"].get("av6TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")
    df_av2 = st.session_state["merged_dataframes"].get("av2TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")

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

        df_final_av7 = df_final_av7[colunas_selecionadas].rename(columns=colunas_renomeadas)

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
        

        colunas_visiveis = [
            "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index","populacao", "GM",
            "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
            "prod_kg_ha", "prod_sc_ha", "PMG"
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

        with col_filtros:
            st.markdown("### 🎧 Filtros")




            filtros = {
                "Microrregiao": "Microrregião",
                "Estado": "Estado",
                "Cidade": "Cidade",
                "Fazenda": "Fazenda",
                "Cultivar": "Cultivar",
                "Teste": "Teste",               
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
            
            

            

        with col_tabela:
            aba1, aba2= st.tabs(["📊 Faixa + Densidade", "📋 Resultados Faixa"])

            with aba1:
                colunas_visiveis = [
                    "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index","populacao","GM",
                    "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
                    "prod_kg_ha", "prod_sc_ha", "PMG"
                ]

                df_visualizacao = df_final_av7[[col for col in colunas_visiveis if col in df_final_av7.columns]]
                st.dataframe(df_visualizacao, height=500)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final_av7.to_excel(writer, index=False, sheet_name="faixa_densidade")

                st.download_button(
                    label="📅 Baixar Faixa + Densidade",
                    data=output.getvalue(),
                    file_name="faixa_densidade.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with aba2:
                df_faixa_completo = df_final_av7[df_final_av7["Teste"] == "Faixa"].copy()

                # 👉 Converte 'Plantio' e 'Colheita' para datetime
                df_faixa_completo["Plantio"] = pd.to_datetime(df_faixa_completo["Plantio"], format="%d/%m/%Y", errors="coerce")
                df_faixa_completo["Colheita"] = pd.to_datetime(df_faixa_completo["Colheita"], format="%d/%m/%Y", errors="coerce")

                # 👉 Calcula MAT (dias entre Colheita e Plantio)
                df_faixa_completo["MAT"] = (df_faixa_completo["Colheita"] - df_faixa_completo["Plantio"]).dt.days

                # 👉 Formata as datas para exibição estilo BR (sem horário)
                df_faixa_completo["Plantio"] = df_faixa_completo["Plantio"].dt.strftime("%d/%m/%Y")
                df_faixa_completo["Colheita"] = df_faixa_completo["Colheita"].dt.strftime("%d/%m/%Y")



                if df_av6 is not None and not df_av6.empty:
                    df_av6 = df_av6.copy()
                    df_av6["ChaveFaixa"] = df_av6["fazendaRef"].astype(str) + "_" + df_av6["indexTratamento"].astype(str)
                    df_av6 = df_av6.rename(columns={
                        "nivelAcamenamento": "AC",
                        "gmVisual": "GM_obs"
                    })

                    df_faixa_completo = df_faixa_completo.merge(
                        df_av6[["ChaveFaixa", "AC", "GM_obs"]],
                        on="ChaveFaixa",
                        how="left"
                    )

                df_av4 = st.session_state["merged_dataframes"].get("av4TratamentoSoja_Avaliacao_Fazenda_Users_Cidade_Estado")
                if df_av4 is not None and not df_av4.empty:
                    df_av4 = df_av4.copy()
                    df_av4["ChaveFaixa"] = df_av4["fazendaRef"].astype(str) + "_" + df_av4["indexTratamento"].astype(str)

                    colunas_av4 = {
                        "planta1Engalhamento": "1_ENG",
                        "planta2Engalhamento": "2_ENG",
                        "planta3Engalhamento": "3_ENG",
                        "planta4Engalhamento": "4_ENG",
                        "planta5Engalhamento": "5_ENG",
                        "planta1AlturaInsercaoPrimVagem": "1_AIV",
                        "planta2AlturaInsercaoPrimVagem": "2_AIV",
                        "planta3AlturaInsercaoPrimVagem": "3_AIV",
                        "planta4AlturaInsercaoPrimVagem": "4_AIV",
                        "planta5AlturaInsercaoPrimVagem": "5_AIV",
                        "planta1AlturaPlanta": "1_ALT",
                        "planta2AlturaPlanta": "2_ALT",
                        "planta3AlturaPlanta": "3_ALT",
                        "planta4AlturaPlanta": "4_ALT",
                        "planta5AlturaPlanta": "5_ALT"
                    }

                    df_faixa_completo = df_faixa_completo.merge(
                        df_av4[["ChaveFaixa"] + list(colunas_av4.keys())].rename(columns=colunas_av4),
                        on="ChaveFaixa",
                        how="left"
                    )

                eng_cols = ["1_ENG", "2_ENG", "3_ENG", "4_ENG", "5_ENG"]
                for col in eng_cols:
                    if col in df_faixa_completo.columns:
                        df_faixa_completo[col] = df_faixa_completo[col].replace(0, pd.NA)
                df_faixa_completo["ENG"] = df_faixa_completo[eng_cols].mean(axis=1, skipna=True).round(1)

                alt_cols = ["1_ALT", "2_ALT", "3_ALT", "4_ALT", "5_ALT"]
                for col in alt_cols:
                    if col in df_faixa_completo.columns:
                        df_faixa_completo[col] = df_faixa_completo[col].replace(0, pd.NA)
                df_faixa_completo["ALT"] = df_faixa_completo[alt_cols].mean(axis=1, skipna=True).round(1)

                aiv_cols = ["1_AIV", "2_AIV", "3_AIV", "4_AIV", "5_AIV"]
                for col in aiv_cols:
                    if col in df_faixa_completo.columns:
                        df_faixa_completo[col] = df_faixa_completo[col].replace(0, pd.NA)
                df_faixa_completo["AIV"] = df_faixa_completo[aiv_cols].mean(axis=1, skipna=True).round(1)

                colunas_visiveis_faixa = [
                    "Produtor", "Cultivar", "UF", "Plantio", "Colheita","MAT", "Index","populacao","GM","GM_obs",
                    "Pop_Final", "Umidade (%)", "prod_kg_ha", "prod_sc_ha", "PMG",
                    "ENG","AC","AIV", "ALT"
                ]

                df_visualizacao_faixa = df_faixa_completo[[col for col in colunas_visiveis_faixa if col in df_faixa_completo.columns]]
                #st.dataframe(df_visualizacao_faixa, height=600)


                from st_aggrid import AgGrid, GridOptionsBuilder

                # Define o DataFrame (sem mexer na estrutura original)
                df_fmt = df_visualizacao_faixa.copy()

                # 🔧 Garante que as colunas ENG, AIV, ALT e AC estejam em float
                for col in ["ENG", "AIV", "ALT", "AC"]:
                    if col in df_fmt.columns:
                        df_fmt[col] = pd.to_numeric(df_fmt[col], errors="coerce")

                # Cria o builder
                gb = GridOptionsBuilder.from_dataframe(df_fmt)

                # Aplica formatação visual: número com 1 casa decimal
                colunas_float = df_fmt.select_dtypes(include=["float"]).columns

                for col in colunas_float:
                    gb.configure_column(
                        field=col,
                        type=["numericColumn"],
                        valueFormatter="x.toFixed(1)"
                    )

                # Tamanho da fonte e cabeçalho
                gb.configure_default_column(cellStyle={'fontSize': '14px'})
                gb.configure_grid_options(headerHeight=30)

                # Cabeçalho em negrito e fonte preta
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
                
                colunas_estatisticas = ["Pop_Final", "prod_kg_ha", "prod_sc_ha","AC","PMG", "ENG", "AIV", "ALT"]
                colunas_validas = [col for col in colunas_estatisticas if col in df_faixa_completo.columns]

                df_faixa_completo[colunas_validas] = df_faixa_completo[colunas_validas].replace([np.inf, -np.inf], np.nan)

                # 👉 Para ENG, substitui 0 por 1 (antes de tratar os demais)
                if "ENG" in df_faixa_completo.columns:
                    df_faixa_completo["ENG"] = df_faixa_completo["ENG"].replace(0, 1)
                
                # Substitui zeros por NaN apenas nas colunas que vamos analisar
                df_faixa_completo[colunas_validas] = df_faixa_completo[colunas_validas].replace(0, np.nan)
                
                # 👉 Trata a coluna AC: se for nulo ou zero, vira 9
                if "AC" in df_faixa_completo.columns:
                    df_faixa_completo["AC"] = df_faixa_completo["AC"].fillna(9)
                    df_faixa_completo["AC"] = df_faixa_completo["AC"].replace(0, 9)

                ## ✅ Aqui salva no session_state
                st.session_state["df_faixa_completo"] = df_faixa_completo

                # calcula as estatisticas sem considerar os zeros
                stats_dict = {col: df_faixa_completo[col].describe() for col in colunas_validas}
                df_stats = pd.DataFrame(stats_dict).round(2).reset_index().rename(columns={"index": "Medida"})

                # Adiciona linha de Coeficiente de Variação (%)
                cv_series = {}
                for col in colunas_validas:
                    media = df_faixa_completo[col].mean(skipna=True)
                    desvio = df_faixa_completo[col].std(skipna=True)
                    cv = (desvio / media * 100) if media else np.nan
                    cv_series[col] = round(cv, 2)

                # Cria DataFrame da linha de CV e concatena
                cv_df = pd.DataFrame([cv_series], index=["CV (%)"]).reset_index().rename(columns={"index": "Medida"})
                df_stats = pd.concat([df_stats, cv_df], ignore_index=True)

                from statsmodels.stats.anova import anova_lm
                from statsmodels.formula.api import ols
                from scipy.stats import t

                if {"prod_kg_ha", "Cultivar", "FazendaRef"}.issubset(df_faixa_completo.columns):
                    df_anova = df_faixa_completo[["prod_kg_ha", "Cultivar", "FazendaRef"]].dropna()

                    if not df_anova.empty and df_anova["FazendaRef"].nunique() > 1:
                        try:
                            model = ols('prod_kg_ha ~ C(Cultivar) + C(FazendaRef)', data=df_anova).fit()
                            anova_table = anova_lm(model, typ=2)

                            mse = anova_table.loc["Residual", "sum_sq"] / anova_table.loc["Residual", "df"]
                            n_rep = df_anova["FazendaRef"].nunique()
                            df_resid = anova_table.loc["Residual", "df"]
                            t_val = t.ppf(1 - 0.025, df_resid)

                            lsd = round(t_val * (2 * mse / n_rep) ** 0.5, 2)
                            lsd_sc = round(lsd / 60, 2)

                            # ✅ Prepara linha com todas colunas existentes
                            nova_linha = {col: "" for col in df_stats.columns}
                            nova_linha["Medida"] = "LSD"
                            if "prod_kg_ha" in df_stats.columns:
                                nova_linha["prod_kg_ha"] = lsd
                            if "prod_sc_ha" in df_stats.columns:
                                nova_linha["prod_sc_ha"] = lsd_sc

                            # ✅ Cria DataFrame e concatena
                            lsd_df = pd.DataFrame([nova_linha])
                            df_stats = pd.concat([df_stats, lsd_df], ignore_index=True)

                        except Exception as e:
                            st.warning(f"⚠️ Erro ao calcular LSD: {e}")


                        except Exception as e:
                            st.warning(f"⚠️ Erro ao calcular LSD: {e}")

                # 👉 Traduz os nomes das medidas para Português
                mapa_medidas = {
                    "count": "Total de Observações",
                    "mean": "Média",
                    "std": "Desvio Padrão",
                    "min": "Mínimo",
                    "25%": "1º Quartil - 25%",
                    "50%": "Mediana",
                    "75%": "3º Quartil - 75%",
                    "max": "Máximo",
                    "CV (%)": "Coef. Variação (%)",
                    "Locais": "Nº de Locais"
                }
                df_stats["Medida"] = df_stats["Medida"].replace(mapa_medidas)

                # Adiciona linha com quantidade de locais únicos (CidadeRef)
                num_locais = df_faixa_completo["FazendaRef"].nunique() if "FazendaRef" in df_faixa_completo.columns else np.nan
                locais_dict = {col: np.nan for col in colunas_validas}
                locais_dict[colunas_validas[0]] = num_locais  # coloca o valor só na primeira coluna como referência

                locais_df = pd.DataFrame([locais_dict], index=["Locais"]).reset_index().rename(columns={"index": "Medida"})
                df_stats = pd.concat([df_stats, locais_df], ignore_index=True)

                                
                output_faixa = io.BytesIO()
                with pd.ExcelWriter(output_faixa, engine='xlsxwriter') as writer:
                    
                    #colunas_exportar = [
                    #    "Fazenda", "Produtor", "Microrregiao", "Cidade", "Estado", "UF", "Plantio", "Colheita", "Teste",
                    #    "populacao", "Index", "Cultivar", "GM", "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
                    #    "prod_kg_ha", "prod_sc_ha", "PMG", "DTC", "CidadeRef", "FazendaRef", "ChaveFaixa", "MAT", "AC", "GM_obs",
                    #    "1_ENG", "2_ENG", "3_ENG", "4_ENG", "5_ENG",
                    #    "1_AIV", "2_AIV", "3_AIV", "4_AIV", "5_AIV",
                    #    "1_ALT", "2_ALT", "3_ALT", "4_ALT", "5_ALT",
                    #    "ENG", "ALT", "AIV"
                    #]
                    
                    
                    
                    colunas_exportar = [
                        "Fazenda", "Produtor", "Microrregiao", "Cidade", "Estado", "UF", "Plantio", "Colheita","MAT","Teste",
                        "populacao", "Index", "Cultivar", "GM","GM_obs", "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
                        "prod_kg_ha", "prod_sc_ha", "PMG", "DTC","AC", 
                        "1_ENG", "2_ENG", "3_ENG", "4_ENG", "5_ENG","ENG",
                        "1_AIV", "2_AIV", "3_AIV", "4_AIV", "5_AIV","ALT",
                        "1_ALT", "2_ALT", "3_ALT", "4_ALT", "5_ALT","AIV"
                          
                    ]

                    # 🔍 Filtra apenas colunas que realmente existem no df
                    colunas_para_exportar = [col for col in colunas_exportar if col in df_faixa_completo.columns]

                    # 💾 Exporta apenas as colunas desejadas
                    df_faixa_completo[colunas_para_exportar].to_excel(writer, index=False, sheet_name="resultado_faixa")

                # Botão de download
                st.download_button(
                    label="📅 Baixar Resultado Faixa",
                    data=output_faixa.getvalue(),
                    file_name="resultado_faixa.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


                # 📌 Resumo da produção sc/ha por Cultivar -
                df_conjunta_cultivar = (
                    df_faixa_completo[df_faixa_completo["prod_sc_ha"].notna()]
                    .groupby("Cultivar")
                    .agg(
                        Produtor=("Produtor", "first"),
                        Microregiao=("Microrregiao", "first"),
                        Cidade=("Cidade", "first"),
                        Estado=("UF", "first"),
                        MAT=("MAT", "mean"),
                        Minimo=("prod_sc_ha", "min"),
                        Maximo=("prod_sc_ha", "max"),
                        Umidade=("Umidade (%)", "mean"),                        
                        Prod_sc_ha=("prod_sc_ha", "mean"),
                        Prod_kg_ha=("prod_kg_ha", "mean"),
                        Pop_Final=("Pop_Final", "mean"),
                        AIV=("AIV", "mean"),
                        ALT=("ALT", "mean"),
                        AC=("AC", "mean"),
                        Desvio=("prod_sc_ha", "std"),
                    )
                    .reset_index()
                    .round(1)
                )

                # Limite de classificação
                col_input, _ = st.columns([1.5, 8.5])
                with col_input:
                    limite_classificacao = st.number_input(
                        "Defina o valor mínimo para ser Favorável (sc/ha):",
                        value=50.0,
                        step=1.0,
                        format="%.1f"
                    )

                try:
                    limite_classificacao = float(limite_classificacao)
                except ValueError:
                    st.warning("⚠️ Digite um número válido.")
                    limite_classificacao = 50

                # Cálculo do CV e classificação
                df_conjunta_cultivar["CV (%)"] = (df_conjunta_cultivar["Desvio"] / df_conjunta_cultivar["Prod_sc_ha"] * 100)
                df_conjunta_cultivar = df_conjunta_cultivar.drop(columns=["Desvio"])
                df_conjunta_cultivar["Classificação"] = df_conjunta_cultivar["Prod_sc_ha"].apply(
                    lambda x: "Favorável" if x >= limite_classificacao else "Desfavorável"
                )
                df_conjunta_cultivar = df_conjunta_cultivar.round(1)

                # Título da seção
                st.markdown("#### 📈 Conjunta Produção (sc/ha) e outros componentes de produção por Cultivar")

                # Filtro por classificação
                with st.expander("🎯 Filtrar por Classificação"):
                    mostrar_favoraveis = st.checkbox("Mostrar Favoráveis", value=True)
                    mostrar_desfavoraveis = st.checkbox("Mostrar Desfavoráveis", value=True)

                    opcoes = []
                    if mostrar_favoraveis:
                        opcoes.append("Favorável")
                    if mostrar_desfavoraveis:
                        opcoes.append("Desfavorável")

                    df_conjunta_cultivar = df_conjunta_cultivar[df_conjunta_cultivar["Classificação"].isin(opcoes)]

                # Ordenação por produção média
                df_conjunta_cultivar = df_conjunta_cultivar.sort_values(by=["Prod_sc_ha"], ascending=False)

                # Colunas visíveis
                colunas_visiveis = [
                    "Cultivar","Pop_Final","Umidade","MAT","Prod_kg_ha","Prod_sc_ha","AC","AIV", "ALT",
                ]

                # Exibe a tabela
                #st.dataframe(df_conjunta_cultivar[colunas_visiveis], use_container_width=True)

                # formatando tabela
                
                # 🧼 Corrige os nomes da Cultivar
                if "Cultivar" in df_conjunta_cultivar.columns:
                    df_conjunta_cultivar["Cultivar"] = df_conjunta_cultivar["Cultivar"].replace({
                        "B�NUS IPRO": "BÔNUS IPRO",
                        "DOM�NIO IPRO": "DOMÍNIO IPRO",
                        "F�RIA CE": "FÚRIA CE",
                        "V�NUS CE": "VÊNUS CE",
                        "GH 2383 IPRO": "GH 2483 IPRO"
                    })               

                # 🔢 Arredonda os valores para 1 casa decimal
                df_fmt = df_conjunta_cultivar[colunas_visiveis].copy()
                colunas_float = df_fmt.select_dtypes(include=["float", "float64"]).columns
                df_fmt[colunas_float] = df_fmt[colunas_float].round(1)

                # 🧱 Constrói o grid
                gb = GridOptionsBuilder.from_dataframe(df_fmt)

                # 🔧 Formata colunas numéricas com .toFixed(1)
                for col in colunas_float:
                    gb.configure_column(
                        field=col,
                        type=["numericColumn"],
                        valueFormatter="x.toFixed(1)"
                    )

                # 💅 Fonte, cabeçalho e tamanho
                gb.configure_default_column(cellStyle={'fontSize': '14px'})
                gb.configure_grid_options(headerHeight=30)

                # 🎨 CSS para deixar o cabeçalho mais forte
                custom_css = {
                    ".ag-header-cell-label": {
                        "font-weight": "bold",
                        "font-size": "15px",
                        "color": "black"
                    }
                }

                # 🚀 Exibe tabela bonita
                AgGrid(
                    df_fmt,
                    gridOptions=gb.build(),
                    height=500,
                    custom_css=custom_css,
                    use_container_width=True
                )




                # Botão para baixar
                output_resumo = io.BytesIO()
                with pd.ExcelWriter(output_resumo, engine="xlsxwriter") as writer:
                    df_conjunta_cultivar.to_excel(writer, index=False, sheet_name="resumo_fazendas")

                st.download_button(
                    label="📥 Baixar Resumo de Conjunta",
                    data=output_resumo.getvalue(),
                    file_name="resumo_conjunta_cultivar.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # 📌 Tabela com estatísticas descritivas
                st.markdown("#### 📈 Estatísticas descritivas (por variável)")

                # 🔢 Define colunas visíveis

                #colunas_visiveis = [
                #    "Medida", "Pop_Final", "prod_kg_ha", "prod_sc_ha", "AC",
                #   "PMG", "ENG", "AIV", "ALT"
                #]        
                
                colunas_visiveis = [
                    "Medida", "Pop_Final", "prod_kg_ha", "prod_sc_ha", 
                    "AC","AIV", "ALT"]
                
                df_fmt = df_stats[[col for col in colunas_visiveis if col in df_stats.columns]].copy()

                # 🔢 Arredonda os valores
                colunas_float = df_fmt.select_dtypes(include=["float", "float64"]).columns
                df_fmt[colunas_float] = df_fmt[colunas_float].round(1)

                # 🧱 Constrói o grid
                gb = GridOptionsBuilder.from_dataframe(df_fmt)

                # 🔧 Formata valores numéricos
                for col in colunas_float:
                    gb.configure_column(
                        field=col,
                        type=["numericColumn"],
                        valueFormatter="x.toFixed(1)"
                    )

                # 💅 Estilo
                gb.configure_default_column(cellStyle={'fontSize': '14px'})
                gb.configure_grid_options(headerHeight=30)

                # 🎨 Cabeçalho em destaque
                custom_css = {
                    ".ag-header-cell-label": {
                        "font-weight": "bold",
                        "font-size": "15px",
                        "color": "black"
                    }
                }

                # 🚀 Exibe tabela final
                AgGrid(
                    df_fmt,
                    gridOptions=gb.build(),
                    height=500,
                    custom_css=custom_css,
                    use_container_width=True
                )

               # Botão para exportar estatísticas descritivas em Excel
                output_stats = io.BytesIO()
                with pd.ExcelWriter(output_stats, engine="xlsxwriter") as writer:
                    df_stats.to_excel(writer, index=False, sheet_name="estatisticas_descritivas")

                st.download_button(
                    label="📅 Baixar Estatísticas Descritivas",
                    data=output_stats.getvalue(),
                    file_name="estatisticas_descritivas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

               
                output_faixa = io.BytesIO()
                with pd.ExcelWriter(output_faixa, engine='xlsxwriter') as writer:
                    df_faixa_completo.to_excel(writer, index=False, sheet_name="resultado_faixa")


                # 📌Histograma de População Final (kg/ha)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["Pop_Final"].notna()]
                df_hist = df_hist[df_hist["Pop_Final"] > 0]  # Apenas positivos
                df_hist["Pop_Final"] = pd.to_numeric(df_hist["Pop_Final"], errors="coerce")

                # Dados para o eixo x
                x_data = df_hist["Pop_Final"].dropna()
                x_data = x_data[x_data > 0]

                # Cria o histograma
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

                # Adiciona curva de densidade
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
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # Estilo dos textos
                font_bold = dict(size=16, family="Arial Bold", color="black")

                # Layout final com legenda estilizada
                fig_hist.update_layout(
                    title=dict(text="Histograma de População Final", font=font_bold),
                    xaxis=dict(
                        title=dict(text="População Final", font=font_bold),
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

                # Mostra o gráfico
                with st.expander("📊 Visualizar Histograma de População Final", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)

               
                # 📌Histograma de Produção (kg/ha)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["prod_kg_ha"].notna()]
                df_hist = df_hist[df_hist["prod_kg_ha"] > 0]  # Apenas positivos
                df_hist["prod_kg_ha"] = pd.to_numeric(df_hist["prod_kg_ha"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["prod_kg_ha"].dropna()
                x_data = x_data[x_data > 0]

                # Cria o histograma
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

                # Adiciona curva de densidade
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
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # Estilo dos textos
                font_bold = dict(size=16, family="Arial Bold", color="black")

                # Layout final com legenda estilizada
                fig_hist.update_layout(
                    title=dict(text="Histograma de Produção (kg/ha)", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Produção (kg/ha)", font=font_bold),
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

                # Mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Produção (sc/ha)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)
      

                # 📌 Histograma de Produção (sc/ha)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["prod_sc_ha"].notna()]
                df_hist = df_hist[df_hist["prod_sc_ha"] > 0]  # Apenas positivos
                df_hist["prod_sc_ha"] = pd.to_numeric(df_hist["prod_sc_ha"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["prod_sc_ha"].dropna()
                x_data = x_data[x_data > 0]

                # Cria o histograma
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

                # Adiciona curva de densidade (KDE)
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
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # Layout com dois eixos e legenda em negrito
                font_bold = dict(size=16, family="Arial Bold", color="black")

                fig_hist.update_layout(
                    title=dict(text="Histograma de Produção (sc/ha)", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Produção (sc/ha)", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        showgrid=True,
                        gridcolor="lightgray"
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
                        font=dict(size=16, family="Arial Bold", color="black")
                    ),
                )

                # Mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Produção (sc/ha)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)


                # 📌 Histograma de Acamamento (AC)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["AC"].notna()]
                df_hist = df_hist[df_hist["AC"] > 0]
                df_hist["AC"] = pd.to_numeric(df_hist["AC"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["AC"].dropna()
                x_data = x_data[x_data > 0]

                # Cria o histograma
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

                # Adiciona curva de densidade (KDE)
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
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # Layout
                font_bold = dict(size=16, family="Arial Bold", color="black")

                fig_hist.update_layout(
                    title=dict(text="Histograma de Acamamento", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Nota Acamamento (AC)", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        showgrid=True,
                        gridcolor="lightgray"
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
                        font=dict(size=16, family="Arial Bold", color="black")
                    ),
                )

                # Mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Nota de Acamamento (AC)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)

                # 📌 Histograma de Peso de Mil Grãos 
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["PMG"].notna()]
                df_hist = df_hist[df_hist["PMG"] > 0]
                df_hist["PMG"] = pd.to_numeric(df_hist["PMG"], errors="coerce")

                # Dados para o eixo x
                x_data = df_hist["PMG"].dropna()
                x_data = x_data[x_data > 0]

                # Cria o histograma
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

                # Adiciona curva de densidade (KDE)
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
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # Layout
                font_bold = dict(size=16, family="Arial Bold", color="black")

                fig_hist.update_layout(
                    title=dict(text="Peso de Mil Grão (PMG)", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Peso de Mil Grãos (PMG)", font=font_bold),
                        tickfont=dict(family="Arial", size=20, color="black"),
                        showgrid=True,
                        gridcolor="lightgray"
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
                        font=dict(size=16, family="Arial Bold", color="black")
                    ),
                )

                # Mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Peso de Mil Grãos (PMG)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)

   

                # 📌 Histograma de Engalhamento (ENG)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["ENG"].notna()]
                df_hist = df_hist[df_hist["ENG"] > 0]
                df_hist["ENG"] = pd.to_numeric(df_hist["ENG"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["ENG"].dropna()
                x_data = x_data[x_data > 0]

                # Cria o histograma
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

                # Adiciona curva de densidade
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

                    # Linha da média
                    media = x_data.mean()
                    fig_hist.add_trace(go.Scatter(
                        x=[media, media],
                        y=[0, y_vals.max()],
                        mode="lines",
                        name=f"Média: {media:.1f}",
                        line=dict(color="red", width=2, dash="dash"),
                        yaxis="y2"
                    ))
                else:
                    st.warning("⚠️ Dados insuficientes ou sem variação para calcular a curva de densidade.")

                # Layout
                font_bold = dict(size=16, family="Arial Bold", color="black")

                fig_hist.update_layout(
                    title=dict(text="Histograma de Nota de Engalhamento", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Engalhamento (ENG)", font=font_bold),
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
                    legend=dict(
                        font=dict(size=16, family="Arial Bold", color="black"),
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    plot_bgcolor="white",
                    bargap=0.1,
                )

                # Mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Engalhamento (ENG)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)

                 
                # 📌 Histograma de Altura de Inserção da Primeira Vagem (AIV)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["AIV"].notna()]
                df_hist = df_hist[df_hist["AIV"] > 0]
                df_hist["AIV"] = pd.to_numeric(df_hist["AIV"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["AIV"].dropna()
                x_data = x_data[x_data > 0]

                # Cria o histograma
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

                # Adiciona curva de densidade
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

                    # Linha da média
                    media = x_data.mean()
                    fig_hist.add_trace(go.Scatter(
                        x=[media, media],
                        y=[0, y_vals.max()],
                        mode="lines",
                        name=f"Média: {media:.1f}",
                        line=dict(color="red", width=2, dash="dash"),
                        yaxis="y2"
                    ))
                else:
                    st.warning("⚠️ Dados insuficientes ou sem variação para calcular a curva de densidade.")

                # Layout com dois eixos
                font_bold = dict(size=16, family="Arial Bold", color="black")

                fig_hist.update_layout(
                    title=dict(text="Histograma de Altura de Inserção da Primeira Vagem", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Altura de Inserção da Primeira Vagem (AIV)", font=font_bold),
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
                        font=dict(size=16, family="Arial Bold", color="black"),
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                )

                # Mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Altura de Inserção da Primeira Vagem (AIV)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)

                
                # 📌 Histograma de Altura da Planta (ALT)                
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["ALT"].notna()]
                df_hist = df_hist[df_hist["ALT"] > 0]
                df_hist["ALT"] = pd.to_numeric(df_hist["ALT"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["ALT"].dropna()
                x_data = x_data[x_data > 0]

                # Cria o histograma
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

                # Adiciona curva de densidade
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

                    # Linha da média
                    media = x_data.mean()
                    fig_hist.add_trace(go.Scatter(
                        x=[media, media],
                        y=[0, y_vals.max()],
                        mode="lines",
                        name=f"Média: {media:.1f}",
                        line=dict(color="red", width=2, dash="dash"),
                        yaxis="y2"
                    ))
                else:
                    st.warning("⚠️ Dados insuficientes ou sem variação para calcular a curva de densidade.")

                # Layout com dois eixos
                font_bold = dict(size=16, family="Arial Bold", color="black")

                fig_hist.update_layout(
                    title=dict(text="Histograma de Altura de Planta (ALT)", font=font_bold),
                    xaxis=dict(
                        title=dict(text="Altura de Planta (ALT)", font=font_bold),
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
                        font=dict(size=16, family="Arial Bold", color="black"),
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                )

                # Mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Altura de Planta (ALT)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)

                # 📦Boxplot de População Final
                media = df_faixa_completo["Pop_Final"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de População Final", expanded=False):
                    fig_box = go.Figure()

                    fig_box.add_trace(go.Box(
                        x=df_faixa_completo["Pop_Final"],
                        name="População Final",
                        boxpoints="outliers",
                        fillcolor="lightblue",
                        marker_color="lightblue",
                        line=dict(color="black", width=1),
                        boxmean=True
                    ))

                    # Estilo dos textos
                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig_box.update_layout(
                        title=dict(
                            text="Box Plot de População Final",
                            font=font_bold
                        ),
                        xaxis=dict(
                            title=dict(
                                text="População Final",
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

                    st.plotly_chart(fig_box, use_container_width=True)



                # 📦 Boxplot de Produção (kg/ha)
                media = df_faixa_completo["prod_kg_ha"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Produção (kg/ha)", expanded=False):
                    fig_box = go.Figure()

                    fig_box.add_trace(go.Box(
                        x=df_faixa_completo["prod_kg_ha"],
                        name="Produção (kg/ha)",
                        boxpoints="outliers",
                        fillcolor="lightblue",
                        marker_color="lightblue",
                        line=dict(color="black", width=1),
                        boxmean=True
                    ))

                    # Fonte personalizada
                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig_box.update_layout(
                        title=dict(
                            text="Box Plot de Produção (kg/ha)",
                            font=font_bold
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Produção (kg/ha)",
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

                    st.plotly_chart(fig_box, use_container_width=True)


                # 📦 Boxplot de Produção (sc/ha)

                media = df_faixa_completo["prod_sc_ha"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Produção (sc/ha)", expanded=False):
                    fig_box = go.Figure()

                    fig_box.add_trace(go.Box(
                        x=df_faixa_completo["prod_sc_ha"],
                        name="Produção (sc/ha)",
                        boxpoints="outliers",
                        fillcolor="lightblue",
                        marker_color="lightblue",
                        line=dict(color="black", width=1),
                        boxmean=True
                    ))

                    # Estilo dos títulos e rótulos 
                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig_box.update_layout(
                        title=dict(
                            text="Box Plot de Produção (sc/ha)",
                            font=font_bold
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Produção (sc/ha)",
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

                    st.plotly_chart(fig_box, use_container_width=True)



                # 📦 Boxplot de Nota Acamamento (AC)

                media = df_faixa_completo["AC"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Acamamento (AC)", expanded=False):
                    fig_box = go.Figure()

                    fig_box.add_trace(go.Box(
                        x=df_faixa_completo["AC"],
                        name="Nota Acamamento (AC)",
                        boxpoints="outliers",
                        fillcolor="lightblue",
                        marker_color="lightblue",
                        line=dict(color="black", width=1),
                        boxmean=True
                    ))

                    # Estilo dos títulos e rótulos
                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig_box.update_layout(
                        title=dict(
                            text="Box Plot de Nota Acamamento (AC)",
                            font=font_bold
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Nota Acamamento (AC)",
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

                    st.plotly_chart(fig_box, use_container_width=True)

                 

                # 📦 Boxplot de Peso de Mil Grãos (PMG)
                media = df_faixa_completo["PMG"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Peso de Mil Grãos (PMG)", expanded=False):
                    fig_box = go.Figure()

                    fig_box.add_trace(go.Box(
                        x=df_faixa_completo["PMG"],
                        name="Peso de Mil Grãos (PMG)",
                        boxpoints="outliers",
                        fillcolor="lightblue",
                        marker_color="lightblue",
                        line=dict(color="black", width=1),
                        boxmean=True
                    ))

                    # Estilo negrito e maior
                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig_box.update_layout(
                        title=dict(
                            text="Box Plot de Peso de Mil Grãos (PMG)",
                            font=font_bold
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Peso de Mil Grãos (PMG)",
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

                    st.plotly_chart(fig_box, use_container_width=True)



                # 📦 Boxplot de Engalhamento (ENG)

                media = df_faixa_completo["ENG"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Engalhamento (ENG)", expanded=False):
                    fig_box = go.Figure()

                    fig_box.add_trace(go.Box(
                        x=df_faixa_completo["ENG"],
                        name="Engalhamento (ENG)",
                        boxpoints="outliers",
                        fillcolor="lightblue",
                        marker_color="lightblue",
                        line=dict(color="black", width=1),
                        boxmean=True
                    ))

                    # Estilo negrito e maior
                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig_box.update_layout(
                        title=dict(
                            text="Box Plot de Nota Engalhamento (ENG)",
                            font=font_bold
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Engalhamento (ENG)",
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

                    st.plotly_chart(fig_box, use_container_width=True)

                # 📦 Boxplot de Altura de Inserção da Primeira Vagem (AIV)

                media = df_faixa_completo["AIV"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Altura de Inserção da Primeira Vagem (AIV)", expanded=False):
                    fig_box = go.Figure()

                    fig_box.add_trace(go.Box(
                        x=df_faixa_completo["AIV"],
                        name="Altura de Inserção da Primeira Vagem (AIV)",
                        boxpoints="outliers",
                        fillcolor="lightblue",
                        marker_color="lightblue",
                        line=dict(color="black", width=1),
                        boxmean=True
                    ))

                    # Estilo negrito e maior
                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig_box.update_layout(
                        title=dict(
                            text="Box Plot de Altura de Inserção da Primeira Vagem (AIV)",
                            font=font_bold
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Altura de Inserção da Primeira Vagem (AIV)",
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

                    st.plotly_chart(fig_box, use_container_width=True)


                # 📦 Boxplot de Altura de Planta (ALT)

                media = df_faixa_completo["ALT"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Altura de Planta (ALT)", expanded=False):
                    fig_box = go.Figure()

                    fig_box.add_trace(go.Box(
                        x=df_faixa_completo["ALT"],
                        name="Altura de Planta (ALT)",
                        boxpoints="outliers",
                        fillcolor="lightblue",
                        marker_color="lightblue",
                        line=dict(color="black", width=1),
                        boxmean=True
                    ))

                    # Estilo negrito e maior
                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig_box.update_layout(
                        title=dict(
                            text="Box Plot de Altura de Planta (ALT)",
                            font=font_bold
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Altura de Planta (ALT)",
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

                    st.plotly_chart(fig_box, use_container_width=True)               


                 
                # 🗺️ Cálculo de Índice Ambiental
                with st.expander("📉 Índice Ambiental: Média do Local x Produção do Material", expanded=False):
                    df_dispersao = df_faixa_completo.copy()

                    # Multiselect de cultivares
                    cultivares_disp = sorted(df_dispersao["Cultivar"].dropna().unique())
                    cultivar_default = "78KA42"

                    if cultivar_default in cultivares_disp:
                        valor_default = [cultivar_default]
                    elif cultivares_disp:
                        valor_default = [cultivares_disp[0]]
                    else:
                        valor_default = []

                    cultivares_selecionadas = st.multiselect("🧬 Selecione as Cultivares:", cultivares_disp, default=valor_default)
                    mostrar_outras = st.checkbox("👀 Mostrar outras cultivares", value=True)

                    if not df_dispersao.empty and "FazendaRef" in df_dispersao and "prod_sc_ha" in df_dispersao:
                        df_media_local = df_dispersao.groupby("FazendaRef")["prod_sc_ha"].mean().reset_index().rename(columns={"prod_sc_ha": "Media_Local"})
                        df_dispersao = df_dispersao.merge(df_media_local, on="FazendaRef", how="left")
                        df_dispersao = df_dispersao.dropna(subset=["Media_Local", "prod_sc_ha"])

                        if mostrar_outras:
                            df_dispersao["Cor"] = df_dispersao["Cultivar"].apply(lambda x: x if x in cultivares_selecionadas else "Outras")
                        else:
                            df_dispersao = df_dispersao[df_dispersao["Cultivar"].isin(cultivares_selecionadas)]
                            df_dispersao["Cor"] = df_dispersao["Cultivar"]

                        color_map = {cult: px.colors.qualitative.Plotly[i % 10] for i, cult in enumerate(cultivares_selecionadas)}
                        if mostrar_outras:
                            color_map["Outras"] = "#d3d3d3"

                        fig_disp = px.scatter(
                            df_dispersao,
                            x="Media_Local",
                            y="prod_sc_ha",
                            color="Cor",
                            color_discrete_map=color_map,
                            labels={
                                "Media_Local": "Média do Local",
                                "prod_sc_ha": "Produção do Material",
                                "Cor": "Cultivar"
                            }
                        )

                        import statsmodels.api as sm
                        for cultivar in cultivares_selecionadas:
                            df_cult = df_dispersao[df_dispersao["Cultivar"] == cultivar]
                            if not df_cult.empty and df_cult.shape[0] > 1:
                                X_train = df_cult[["Media_Local"]]
                                X_train = sm.add_constant(X_train)
                                y_train = df_cult["prod_sc_ha"]
                                model = sm.OLS(y_train, X_train).fit()

                                x_vals = np.linspace(df_dispersao["Media_Local"].min(), df_dispersao["Media_Local"].max(), 100)
                                X_pred = pd.DataFrame({"Media_Local": x_vals})
                                X_pred = sm.add_constant(X_pred)
                                y_pred = model.predict(X_pred)

                                fig_disp.add_trace(go.Scatter(
                                    x=x_vals,
                                    y=y_pred,
                                    mode="lines",
                                    name=f"Tendência - {cultivar}",
                                    line=dict(color=color_map.get(cultivar, "black"), dash="solid")
                                ))

                        # Fonte em negrito
                        font_bold = dict(size=20, family="Arial Bold", color="black")

                        fig_disp.update_layout(
                            plot_bgcolor="white",
                            title=dict(
                                text="Índice Ambiental: Cultivares Selecionadas",
                                font=font_bold
                            ),
                            xaxis=dict(
                                title=dict(
                                    text="Média do Local",
                                    font=font_bold
                                ),
                                tickfont=font_bold,
                                showgrid=True,
                                gridcolor="lightgray"
                            ),
                            yaxis=dict(
                                title=dict(
                                    text="Produção do Material",
                                    font=font_bold
                                ),
                                tickfont=font_bold,
                                showgrid=True,
                                gridcolor="lightgray"
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                                font=font_bold
                            )
                        )

                        st.plotly_chart(fig_disp, use_container_width=True)

                    else:
                        st.info("❌ Dados insuficientes para gerar o gráfico.")


                
                # 📉 Dispersão: GM x Produção Média por GM (com base nos filtros)

                with st.expander("📉 Dispersão: GM x Produção do Material", expanded=False):
                    df_dispersao = df_faixa_completo.copy()

                    if not df_dispersao.empty and "GM" in df_dispersao and "prod_sc_ha" in df_dispersao:
                        # Calcula a média dinâmica conforme filtros
                        df_grafico = (
                            df_dispersao
                            .groupby(["GM", "Cultivar"])["prod_sc_ha"]
                            .mean()
                            .reset_index()
                            .dropna()
                        )

                        media_y = df_grafico["prod_sc_ha"].mean()
                        font_bold = dict(size=20, family="Arial Bold", color="black")

                        fig_gm = px.scatter(
                            df_grafico,
                            x="GM",
                            y="prod_sc_ha",
                            color_discrete_sequence=["gray"],
                            text="Cultivar",
                            labels={
                                "GM": "Grupo de Maturação (GM)",
                                "prod_sc_ha": "Produção Média (sc/ha)"
                            },
                            title="Dispersão: GM x Produção Média (sc/ha)"
                        )

                        fig_gm.update_traces(textposition="top center")

                        # ⬇️ Rótulos em negrito e tamanho 16
                        fig_gm.update_traces(textfont=dict(size=16, family="Arial Bold", color="black"))


                        # Linha da média
                        fig_gm.add_trace(go.Scatter(
                            x=[df_grafico["GM"].min(), df_grafico["GM"].max()],
                            y=[media_y, media_y],
                            mode="lines",
                            name=f"Média: {media_y:.1f} sc/ha",
                            line=dict(color="red", width=2, dash="dash")
                        ))

                        fig_gm.update_layout(
                            title=dict(text="Dispersão: GM x Produção Média (sc/ha)", font=font_bold),
                            xaxis=dict(
                                title=dict(text="Grupo de Maturação (GM)", font=font_bold),
                                tickfont=font_bold,
                                showgrid=True,
                                gridcolor="lightgray",
                                dtick=1
                            ),
                            yaxis=dict(
                                title=dict(text="Produção Média (sc/ha)", font=font_bold),
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
                            plot_bgcolor="white"
                        )

                        st.plotly_chart(fig_gm, use_container_width=True)

                    else:
                        st.info("❌ Dados insuficientes para gerar o gráfico de GM.")


                 

                # 🧩 Heatmap Interativo: Desempenho Relativo por Local x Cultivar

                with st.expander("🧩 Heatmap Interativo: Desempenho Relativo por Local x Cultivar", expanded=False):
                    df_heatmap = df_faixa_completo.copy()

                    if not df_heatmap.empty and "prod_sc_ha" in df_heatmap.columns and "Cultivar" in df_heatmap.columns:
                        df_heatmap["Local"] = df_heatmap["Fazenda"].astype(str) + "_" + df_heatmap["Cidade"].astype(str)
                        df_heatmap["Prod_Max_Local"] = df_heatmap.groupby("Local")["prod_sc_ha"].transform("max")
                        df_heatmap["Prod_%"] = (df_heatmap["prod_sc_ha"] / df_heatmap["Prod_Max_Local"]) * 100

                        heatmap_pivot = df_heatmap.pivot_table(
                            index="Local",
                            columns="Cultivar",
                            values="Prod_%",
                            aggfunc="mean"
                        )

                        if "Microrregiao" in df_heatmap.columns:
                            locais_com_regional = df_heatmap[["Local", "Microrregiao"]].drop_duplicates()
                            locais_ordenados = (
                                locais_com_regional
                                .sort_values(by=["Microrregiao", "Local"])
                                .set_index("Local")
                            )
                            ordem_local = locais_ordenados.index.tolist()
                            heatmap_pivot = heatmap_pivot.loc[heatmap_pivot.index.intersection(ordem_local)]
                            heatmap_pivot = heatmap_pivot.reindex(ordem_local)

                        escala_de_cores = [
                            (0.00, "lightcoral"),
                            (0.35, "lightcoral"),
                            (0.45, "lightyellow"),
                            (0.55, "lightyellow"),
                            (0.70, "lightgreen"),
                            (0.80, "mediumseagreen"),
                            (1.00, "green")
                        ]

                        font_bold = dict(size=20, family="Arial Bold", color="black")

                        fig = px.imshow(
                            heatmap_pivot,
                            text_auto=".0f",
                            color_continuous_scale=escala_de_cores,
                            aspect="auto",
                            labels=dict(x="Cultivar", y="Local", color="Produtividade (%)")
                        )

                        fig.update_layout(
                            title=dict(text="Produção Relativa por Cultivar e Local (100% = Maior do Local)", font=font_bold),
                            xaxis=dict(title=dict(text="Cultivar", font=font_bold), tickfont=font_bold),
                            yaxis=dict(title=dict(text="Produtor + Cidade", font=font_bold), tickfont=font_bold),
                            plot_bgcolor="white",
                            coloraxis_colorbar=dict(
                                title=dict(text="Produtividade (%)", font=font_bold),
                                tickvals=[0, 20, 40, 60, 80, 100],
                                ticktext=["0%", "20%", "40%", "60%", "80%", "100%"],
                                tickfont=font_bold
                            )
                        )

                        # ⬇️ Aqui o ajuste do tamanho do texto nas células
                        fig.update_traces(textfont=dict(size=14, family="Arial Bold", color="black"))

                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("❌ Dados insuficientes para gerar o heatmap.")


            # 🏅 Heatmap Interativo: Ranking Relativo por Local x Cultivar

            with st.expander("🧩 Heatmap Interativo: Ranking Relativo por Local x Cultivar", expanded=False):
                df_heatmap = df_faixa_completo.copy()

                if not df_heatmap.empty and "prod_sc_ha" in df_heatmap.columns and "Cultivar" in df_heatmap.columns:
                    df_heatmap["Local"] = df_heatmap["Fazenda"].astype(str) + "_" + df_heatmap["Cidade"].astype(str)

                    # ⬇️ Calcular ranking (1 = melhor)
                    df_heatmap["Rank_Local"] = (
                        df_heatmap.groupby("Local")["prod_sc_ha"]
                        .rank(method="min", ascending=False)
                    )

                    # Pivot para gerar a matriz de rankings
                    heatmap_pivot = df_heatmap.pivot_table(
                        index="Local",
                        columns="Cultivar",
                        values="Rank_Local",
                        aggfunc="min"
                    )

                    # Ordena os locais
                    if "Microrregiao" in df_heatmap.columns:
                        locais_com_regional = df_heatmap[["Local", "Microrregiao"]].drop_duplicates()
                        locais_ordenados = (
                            locais_com_regional
                            .sort_values(by=["Microrregiao", "Local"])
                            .set_index("Local")
                        )
                        ordem_local = locais_ordenados.index.tolist()
                        heatmap_pivot = heatmap_pivot.loc[heatmap_pivot.index.intersection(ordem_local)]
                        heatmap_pivot = heatmap_pivot.reindex(ordem_local)

                    # Máximo ranking encontrado (ajuste automático)
                    max_rank = int(heatmap_pivot.max().max())

                    # Escala de cores: do verde escuro (ranking 1) ao verde claro (ranking alto)
                    escala_verde = [
                        (0.0, "#006400"),   # verde escuro (melhor)
                        (0.5, "#66CDAA"),   # verde médio
                        (1.0, "#C1E1C1")    # verde claro (pior)
                    ]

                    font_bold = dict(size=20, family="Arial Bold", color="black")

                    fig = px.imshow(
                        heatmap_pivot,
                        text_auto=True,
                        color_continuous_scale=escala_verde,
                        aspect="auto",
                        labels=dict(x="Cultivar", y="Local", color="Ranking")
                    )

                    fig.update_layout(
                        title=dict(text="Ranking Relativo por Cultivar e Local (1 = Melhor)", font=font_bold),
                        xaxis=dict(title=dict(text="Cultivar", font=font_bold), tickfont=font_bold),
                        yaxis=dict(title=dict(text="Produtor + Cidade", font=font_bold), tickfont=font_bold),
                        plot_bgcolor="white",
                        coloraxis_colorbar=dict(
                            title=dict(text="Ranking", font=font_bold),
                            tickfont=font_bold
                        )
                    )

                    fig.update_traces(textfont=dict(size=16, family="Arial Bold", color="black"))

                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.warning("❌ Dados insuficientes para gerar o heatmap.")


                             

                 

        st.session_state["df_final_av7"] = df_final_av7
        st.session_state["df_faixa_completo"] = df_faixa_completo

    else:
        st.warning("⚠️ O DataFrame está vazio ou não foi carregado corretamente.")
else:
    st.error("❌ Nenhum dado encontrado na sessão. Certifique-se de carregar os dados na página principal primeiro.")