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
                "BÁNUS IPRO": "BÔNUS IPRO",
                "DOMÍNIO IPRO": "DOMÍNIO IPRO",
                "FÓRIA CE": "FÚRIA CE",
                "VÉNUS CE": "VÊNUS CE"
            })
        st.session_state["df_final_av7"] = df_final_av7
        

        colunas_visiveis = [
            "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index","populacao", "GM",
            "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
            "prod_kg_ha", "prod_sc_ha", "PMG"
        ]

        col_filtros, col_tabela = st.columns([1.5, 8.5])

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
            aba1, aba2, aba3 = st.tabs(["📊 Faixa + Densidade", "📋 Resultados Faixa", "🤜🏻🤛🏻 Análise Head to Head"])

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
                    "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index","populacao", "GM_obs", "AC",
                    "Pop_Final", "Umidade (%)", "prod_kg_ha", "prod_sc_ha", "PMG",
                    "ENG", "AIV", "ALT"
                ]

                df_visualizacao_faixa = df_faixa_completo[[col for col in colunas_visiveis_faixa if col in df_faixa_completo.columns]]
                st.dataframe(df_visualizacao_faixa, height=600)

                
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
                  df_faixa_completo.to_excel(writer, index=False, sheet_name="resultado_faixa")  

                st.download_button(
                    label="📅 Baixar Resultado Faixa",
                    data=output_faixa.getvalue(),
                    file_name="resultado_faixa.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # 📌 Resumo da produção sc/ha por FazendaRef
                df_resumo_fazendas = (
                    df_faixa_completo[df_faixa_completo["prod_sc_ha"].notna()]
                    .groupby("FazendaRef")
                    .agg(
                        Produtor=("Produtor", "first"),
                        Microregiao=("Microrregiao", "first"),
                        Cidade=("Cidade", "first"),
                        Estado=("UF", "first"),
                        Minimo=("prod_sc_ha", "min"),
                        Maximo=("prod_sc_ha", "max"),
                        Media=("prod_sc_ha", "mean"),
                        Desvio=("prod_sc_ha", "std"),
                    )
                    .reset_index()
                    .round(1)
                )

                # Limite de classificação
                col_input, _ = st.columns([1.5, 8.5]) # 15% + 85%
                with col_input:
                    limite_classificacao = st.number_input(
                        "Defina o valor mínimo para ser Favorável (sc/ha):",
                        value=50.0,
                        step=1.0,
                        format="%.1f"
                    )

                # Tenta converter para float
                try:
                    limite_classificacao = float(limite_classificacao)
                except ValueError:
                    st.warning("⚠️ Digite um número válido.")
                    limite_classificacao = 50 # Valor padrão

                
                df_resumo_fazendas["CV (%)"] = (df_resumo_fazendas["Desvio"] / df_resumo_fazendas["Media"] * 100)
                df_resumo_fazendas = df_resumo_fazendas.drop(columns=["Desvio"]) # Remove a coluna de desvio padrão
                df_resumo_fazendas["Classificação"] = df_resumo_fazendas["Media"].apply(
                    lambda x: "Favorável" if x >= limite_classificacao else "Desfavorável"
                )
                df_resumo_fazendas = df_resumo_fazendas.round(1)

               
                
                st.markdown("#### 📈 Resumo da Produção (sc/ha) por Fazenda")

                

                with st.expander("🎯 Filtrar por Classificação"):
                    mostrar_favoraveis = st.checkbox("Mostrar Favoráveis", value=True)
                    mostrar_desfavoraveis = st.checkbox("Mostrar Desfavoráveis", value=True)

                    opcoes = []
                    if mostrar_favoraveis:
                        opcoes.append("Favorável")
                    if mostrar_desfavoraveis:
                        opcoes.append("Desfavorável")
                    
                    df_resumo_fazendas = df_resumo_fazendas[df_resumo_fazendas["Classificação"].isin(opcoes)]
                
                df_resumo_fazendas = df_resumo_fazendas.sort_values(by=["Microregiao","Estado","Cidade"])
                    
                df_resumo_display = df_resumo_fazendas.drop(columns=["FazendaRef"])
                st.markdown("Resumo da Produção (sc/ha) por Fazenda")
                st.dataframe(df_resumo_display, use_container_width=True)

                # Botão para baixar
                output_resumo = io.BytesIO()
                with pd.ExcelWriter(output_resumo, engine="xlsxwriter") as writer:
                    df_resumo_fazendas.to_excel(writer, index=False, sheet_name="resumo_fazendas")

                st.download_button(
                    label="📥 Baixar Resumo de Produção por Fazenda",
                    data=output_resumo.getvalue(),
                    file_name="resumo_fazendas_fazendas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


                st.markdown("#### 📈 Estatísticas descritivas (por variável)")

                st.dataframe(df_stats, use_container_width=True)

                # Botão para exportar estatísticas descritivas em Excel
                output_stats = io.BytesIO()
                with pd.ExcelWriter(output_stats, engine="xlsxwriter") as writer:
                    df_stats.to_excel(writer, index=False, sheet_name="estatisticas_descritivas")
               
                # Histograma de Produção (kg/ha)
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
                    name= "Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y" # eixo primario
                ))

                # Adiciona curva de densidade (KDE - Kernel Density Estimation)
                #
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


                #Linha da média
                media = x_data.mean()
                fig_hist.add_trace(go.Scatter(
                    x=[media, media],
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # layout com dois eixos
                fig_hist.update_layout(
                    title="Histograma de Produção (kg/ha)",
                    xaxis=dict(
                        title="Produção (kg/ha)",
                        showgrid=True,
                        gridcolor="lightgray",
                        #range=[2, 30]
                    ),
                yaxis=dict(
                    title="Frequência",
                    showgrid=True,
                    gridcolor="lightgray"
                ),
                yaxis2=dict(
                    title="Densidade",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
               plot_bgcolor="white",
               bargap=0.1,
               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )    

                # mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Produção (kg/ha)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)      

                # Histograma de Produção (sc/ha)
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
                    name= "Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y" # eixo primario
                ))

                # Adiciona curva de densidade (KDE - Kernel Density Estimation)
                #
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


                #Linha da média
                media = x_data.mean()
                fig_hist.add_trace(go.Scatter(
                    x=[media, media],
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # layout com dois eixos
                fig_hist.update_layout(
                    title="Histograma de Produção (sc/ha)",
                    xaxis=dict(
                        title="Produção (sc/ha)",
                        showgrid=True,
                        gridcolor="lightgray",
                        #range=[2, 30]
                    ),
                yaxis=dict(
                    title="Frequência",
                    showgrid=True,
                    gridcolor="lightgray"
                ),
                yaxis2=dict(
                    title="Densidade",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
               plot_bgcolor="white",
               bargap=0.1,
               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )    

                # mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Produção (sc/ha)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True) 

                # Histograma de Acamanento (AC)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["AC"].notna()]
                df_hist = df_hist[df_hist["AC"] > 0]  # Apenas positivos
                df_hist["AC"] = pd.to_numeric(df_hist["AC"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["AC"].dropna()
                x_data = x_data[x_data > 0]
                
                # Cria o histograma
                fig_hist = go.Figure()

                fig_hist.add_trace(go.Histogram(
                    x=x_data,
                    nbinsx=50,
                    name= "Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y" # eixo primario
                ))

                # Adiciona curva de densidade (KDE - Kernel Density Estimation)
                #
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


                #Linha da média
                media = x_data.mean()
                fig_hist.add_trace(go.Scatter(
                    x=[media, media],
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # layout com dois eixos
                fig_hist.update_layout(
                    title="Histograma de Nota Acamamento (AC)",
                    xaxis=dict(
                        title="Nota Acamamento (AC)",
                        showgrid=True,
                        gridcolor="lightgray",
                        #range=[2, 30]
                    ),
                yaxis=dict(
                    title="Frequência",
                    showgrid=True,
                    gridcolor="lightgray"
                ),
                yaxis2=dict(
                    title="Densidade",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
               plot_bgcolor="white",
               bargap=0.1,
               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )    

                # mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Nota de Acamamento (AC)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)   

                # Histograma de Peso de Mil Grãos (PMG)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["PMG"].notna()]
                df_hist = df_hist[df_hist["PMG"] > 0]  # Apenas positivos
                df_hist["PMG"] = pd.to_numeric(df_hist["prod_sc_ha"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["PMG"].dropna()
                x_data = x_data[x_data > 0]
                
                # Cria o histograma
                fig_hist = go.Figure()

                fig_hist.add_trace(go.Histogram(
                    x=x_data,
                    nbinsx=50,
                    name= "Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y" # eixo primario
                ))

                # Adiciona curva de densidade (KDE - Kernel Density Estimation)
                #
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

               


                #Linha da média
                media = x_data.mean()
                fig_hist.add_trace(go.Scatter(
                    x=[media, media],
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # layout com dois eixos
                fig_hist.update_layout(
                    title="Histograma de Peso de Mil Grãos (PMG)",
                    xaxis=dict(
                        title="Peso de Mil Grãos (PMG)",
                        showgrid=True,
                        gridcolor="lightgray",
                        #range=[2, 30]
                    ),
                yaxis=dict(
                    title="Frequência",
                    showgrid=True,
                    gridcolor="lightgray"
                ),
                yaxis2=dict(
                    title="Densidade",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
               plot_bgcolor="white",
               bargap=0.1,
               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )   
                # mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Peso de Mil Grãos (PMG)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                # Histograma de Engalhamneto (ENG)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["ENG"].notna()]
                df_hist = df_hist[df_hist["ENG"] > 0]  # Apenas positivos
                df_hist["ENG"] = pd.to_numeric(df_hist["ENG"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["ENG"].dropna()
                x_data = x_data[x_data > 0]
                
                # Cria o histograma
                fig_hist = go.Figure()

                fig_hist.add_trace(go.Histogram(
                    x=x_data,
                    nbinsx=50,
                    name= "Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y" # eixo primario
                ))

                # Adiciona curva de densidade (KDE - Kernel Density Estimation)
                #
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


                # layout com dois eixos
                fig_hist.update_layout(
                    title="Histograma de Nota Engalhamento (ENG)",
                    xaxis=dict(
                        title="Engalhamento (ENG)",
                        showgrid=True,
                        gridcolor="lightgray",
                        range=[0, 10]
                    ),
                yaxis=dict(
                    title="Frequência",
                    showgrid=True,
                    gridcolor="lightgray"
                ),
                yaxis2=dict(
                    title="Densidade",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
               plot_bgcolor="white",
               bargap=0.1,
               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )    

                # mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Engalhamento (ENG)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)

                 
                # Histograma de Altura de Inserção da Primeira Vagem (AIV)
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["AIV"].notna()]
                df_hist = df_hist[df_hist["AIV"] > 0]  # Apenas positivos
                df_hist["AIV"] = pd.to_numeric(df_hist["AIV"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["AIV"].dropna()
                x_data = x_data[x_data > 0]
                
                # Cria o histograma
                fig_hist = go.Figure()

                fig_hist.add_trace(go.Histogram(
                    x=x_data,
                    nbinsx=50,
                    name= "Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y" # eixo primario
                ))

                # Adiciona curva de densidade (KDE - Kernel Density Estimation)
                #
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


                #Linha da média
                media = x_data.mean()
                fig_hist.add_trace(go.Scatter(
                    x=[media, media],
                    y=[0, y_vals.max()],
                    mode="lines",
                    name=f"Média: {media:.1f}",
                    line=dict(color="red", width=2, dash="dash"),
                    yaxis="y2"
                ))

                # layout com dois eixos
                fig_hist.update_layout(
                    title="Histograma de Altura de Inserção da Primeira Vagem (AIV)",
                    xaxis=dict(
                        title="AIV",
                        showgrid=True,
                        gridcolor="lightgray",
                        #range=[2, 30]
                    ),
                yaxis=dict(
                    title="Frequência",
                    showgrid=True,
                    gridcolor="lightgray"
                ),
                yaxis2=dict(
                    title="Densidade",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
               plot_bgcolor="white",
               bargap=0.1,
               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )    

                # mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Altura de Inserção da Primeira Vagem (AIV)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                # Histograma de Altura da Planta (ALT)                
                df_hist = df_faixa_completo.copy()
                df_hist = df_hist[df_hist["ALT"].notna()]
                df_hist = df_hist[df_hist["ALT"] > 0]  # Apenas positivos
                df_hist["ALT"] = pd.to_numeric(df_hist["ALT"], errors="coerce")

                # Dados para o eixo x
                x_data = df_faixa_completo["ALT"].dropna()
                x_data = x_data[x_data > 0]
                
                # Cria o histograma
                fig_hist = go.Figure()

                fig_hist.add_trace(go.Histogram(
                    x=x_data,
                    nbinsx=50,
                    name= "Frequência",
                    marker_color="lightblue",
                    marker_line_color="black",
                    marker_line_width=1.5,
                    opacity=0.75,
                    yaxis="y" # eixo primario
                ))

                # Adiciona curva de densidade (KDE - Kernel Density Estimation)
                #
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


                # layout com dois eixos
                fig_hist.update_layout(
                    title="Histograma de Altura de Altura de Planta (ALT)",
                    xaxis=dict(
                        title="ALT",
                        showgrid=True,
                        gridcolor="lightgray",
                        #range=[2, 30]
                    ),
                yaxis=dict(
                    title="Frequência",
                    showgrid=True,
                    gridcolor="lightgray"
                ),
                yaxis2=dict(
                    title="Densidade",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
               plot_bgcolor="white",
               bargap=0.1,
               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )    

                # mostra o gráfico
                with st.expander("📊 Visualizar Histograma de Altura de Planta (ALT)", expanded=False):
                    st.plotly_chart(fig_hist, use_container_width=True)

                # boxplot de Produção (kg/ha)
                media = df_faixa_completo["prod_kg_ha"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Produção (kg/ha)", expanded=False):
                 fig_box = go.Figure()

                 fig_box.add_trace(go.Box(
                    x=df_faixa_completo["prod_kg_ha"], # x é a coluna de produção
                    name="Produção (kg/ha)",
                    boxpoints="outliers", #mostra os outliers
                    fillcolor="lightblue", # cor de preenchimento
                    marker_color="lightblue",
                    line=dict(color="black", width=1),# cor da linha
                    boxmean=True # desliga a média manualmente
                    ))
                 
                # Layout
                 fig_box.update_layout(
                     xaxis_title="Produção (kg/ha)",
                     title="Box Plot de Produção (kg/ha)",
                     plot_bgcolor="white",
                     showlegend=True,
                     yaxis=dict(showticklabels=False)
                )

                 st.plotly_chart(fig_box, use_container_width=True)

                # boxplot de Produção (sc/ha)
                media = df_faixa_completo["prod_sc_ha"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Produção (sc/ha)", expanded=False):
                 fig_box = go.Figure()

                 fig_box.add_trace(go.Box(
                    x=df_faixa_completo["prod_sc_ha"], # x é a coluna de produção
                    name="Produção (sc/ha)",
                    boxpoints="outliers", #mostra os outliers
                    fillcolor="lightblue", # cor de preenchimento
                    marker_color="lightblue",
                    line=dict(color="black", width=1),# cor da linha
                    boxmean=True # desliga a média manualmente
                    ))
                 
                # Layout
                 fig_box.update_layout(
                     xaxis_title="Produção (sc/ha)",
                     title="Box Plot de Produção (sc/ha)",
                     plot_bgcolor="white",
                     showlegend=True,
                     yaxis=dict(showticklabels=False)
                )

                 st.plotly_chart(fig_box, use_container_width=True)

                # boxplot de Nota Acamamento (AC)
                media = df_faixa_completo["AC"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Acamamento (AC)", expanded=False):
                 fig_box = go.Figure()

                 fig_box.add_trace(go.Box(
                    x=df_faixa_completo["AC"], # x é a coluna de produção
                    name="Nota Acamamento (AC)",
                    boxpoints="outliers", #mostra os outliers
                    fillcolor="lightblue", # cor de preenchimento
                    marker_color="lightblue",
                    line=dict(color="black", width=1),# cor da linha
                    boxmean=True # desliga a média manualmente
                    ))
                 
                # Layout
                 fig_box.update_layout(
                     xaxis_title="Nota Acamamento (AC)",
                     title="Box Plot de Nota Acamamento (AC)",
                     plot_bgcolor="white",
                     showlegend=True,
                     yaxis=dict(showticklabels=False)
                )

                 st.plotly_chart(fig_box, use_container_width=True)

                # boxplot de Peso de Mil Grãos (PMG)
                media = df_faixa_completo["PMG"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Peso de Mil Grãos (PMG)", expanded=False):
                 fig_box = go.Figure()

                 fig_box.add_trace(go.Box(
                    x=df_faixa_completo["PMG"], # x é a coluna de produção
                    name="Peso de Mil Grãos (PMG)",
                    boxpoints="outliers", #mostra os outliers
                    fillcolor="lightblue", # cor de preenchimento
                    marker_color="lightblue",
                    line=dict(color="black", width=1),# cor da linha
                    boxmean=True # desliga a média manualmente
                    ))
                 
                # Layout
                 fig_box.update_layout(
                     xaxis_title="Peso de Mil Grãos (PMG)",
                     title="Box Plot de Peso de Mil Grãos (PMG)",
                     plot_bgcolor="white",
                     showlegend=True,
                     yaxis=dict(showticklabels=False)
                )

                 st.plotly_chart(fig_box, use_container_width=True)

                # boxplot de Engalhamento (ENG)
                media = df_faixa_completo["ENG"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de Engalhamento (ENG)", expanded=False):
                 fig_box = go.Figure()

                 fig_box.add_trace(go.Box(
                    x=df_faixa_completo["ENG"], # x é a coluna de produção
                    name="Engalhamento (ENG)", 
                    boxpoints="outliers", #mostra os outliers
                    fillcolor="lightblue", # cor de preenchimento
                    marker_color="lightblue",
                    line=dict(color="black", width=1),# cor da linha
                    boxmean=True # desliga a média manualmente
                    ))
                 
                # Layout
                 fig_box.update_layout(
                     xaxis_title="Engalhamento (ENG)",
                     title="Box Plot de Nota Engalhamento (ENG)",
                     plot_bgcolor="white",
                     showlegend=True,
                     yaxis=dict(showticklabels=False)
                )

                 st.plotly_chart(fig_box, use_container_width=True)

                # boxplot de População Final
                media = df_faixa_completo["Pop_Final"].dropna().mean()

                with st.expander("📦 Visualizar Box Plot de População Final", expanded=False):
                 fig_box = go.Figure()

                 fig_box.add_trace(go.Box(
                    x=df_faixa_completo["Pop_Final"], # x é a coluna de produção
                    name="População Final", 
                    boxpoints="outliers", #mostra os outliers
                    fillcolor="lightblue", # cor de preenchimento
                    marker_color="lightblue",
                    line=dict(color="black", width=1),# cor da linha
                    boxmean=True # desliga a média manualmente
                    ))
                 
                # Layout
                 fig_box.update_layout(
                     xaxis_title="População Final",
                     title="Box Plot de População Final",
                     plot_bgcolor="white",
                     showlegend=True,
                     yaxis=dict(showticklabels=False)
                )

                 st.plotly_chart(fig_box, use_container_width=True)

                 
                # Cálculo de Índice Ambiental
                with st.expander("📉 Índice Ambiental: Média do Local x Produção do Material", expanded=False):
                    df_dispersao = df_faixa_completo.copy()

                    # Multiselect de cultivares
                    cultivares_disp = sorted(df_dispersao["Cultivar"].dropna().unique())
                    cultivar_default = "78KA42"

                    # Verifica se a cultivar padrão está presente, senão usa a primeira disponível (se houver)
                    if cultivar_default in cultivares_disp:
                        valor_default = [cultivar_default]
                    elif cultivares_disp:
                        valor_default = [cultivares_disp[0]]
                    else:
                        valor_default = []

                    cultivares_selecionadas = st.multiselect("🧬 Selecione as Cultivares:", cultivares_disp, default=valor_default)


                    mostrar_outras = st.checkbox("👁️ Mostrar outras cultivares", value=True)

                    if not df_dispersao.empty and "FazendaRef" in df_dispersao and "prod_sc_ha" in df_dispersao:
                        # Média do local
                        df_media_local = df_dispersao.groupby("FazendaRef")["prod_sc_ha"].mean().reset_index().rename(columns={"prod_sc_ha": "Media_Local"})
                        df_dispersao = df_dispersao.merge(df_media_local, on="FazendaRef", how="left")
                        df_dispersao = df_dispersao.dropna(subset=["Media_Local", "prod_sc_ha"])

                        if mostrar_outras:
                            df_dispersao["Cor"] = df_dispersao["Cultivar"].apply(lambda x: x if x in cultivares_selecionadas else "Outras")
                        else:
                            df_dispersao = df_dispersao[df_dispersao["Cultivar"].isin(cultivares_selecionadas)]
                            df_dispersao["Cor"] = df_dispersao["Cultivar"]

                        # Cores
                        color_map = {cult: px.colors.qualitative.Plotly[i % 10] for i, cult in enumerate(cultivares_selecionadas)}
                        if mostrar_outras:
                            color_map["Outras"] = "#d3d3d3"  # cinza claro

                        # Gráfico
                        fig_disp = px.scatter(
                            df_dispersao,
                            x="prod_sc_ha",
                            y="Media_Local",
                            color="Cor",
                            color_discrete_map=color_map,
                            labels={
                                "Media_Local": "Média do Local",
                                "prod_sc_ha": "Produção do Material",
                                "Cor": "Cultivar"
                            },
                            title="Índice Ambiental: Cultivares Selecionadas"
                        )

                        
                        # Reta(s)
                        import statsmodels.api as sm
                        for cultivar in cultivares_selecionadas:
                            df_cult = df_dispersao[df_dispersao["Cultivar"] == cultivar]
                            if not df_cult.empty and df_cult.shape[0] > 1:
                                # Treinamento
                                X_train = df_cult[["prod_sc_ha"]]
                                X_train = sm.add_constant(X_train)
                                y_train = df_cult["Media_Local"]
                                model = sm.OLS(y_train, X_train).fit()

                                # Predição
                                x_vals = np.linspace(df_dispersao["prod_sc_ha"].min(), df_dispersao["prod_sc_ha"].max(), 100)
                                X_pred = pd.DataFrame({"prod_sc_ha": x_vals})
                                X_pred = sm.add_constant(X_pred)

                                y_pred = model.predict(X_pred)

                                fig_disp.add_trace(go.Scatter(
                                    x=x_vals,
                                    y=y_pred,
                                    mode="lines",
                                    name=f"Tendência - {cultivar}",
                                    line=dict(color=color_map.get(cultivar, "black"), dash="solid")
                                ))



                        fig_disp.update_layout(
                            plot_bgcolor="white",
                            xaxis=dict(showgrid=True, gridcolor="lightgray"),
                            yaxis=dict(showgrid=True, gridcolor="lightgray")
                        )

                        st.plotly_chart(fig_disp, use_container_width=True)

                    else:
                        st.info("❌ Dados insuficientes para gerar o gráfico.")
                
                # 📉 Dispersão: GM x Produção Média por GM (com base nos filtros)
                
                # Dispersão: GM x Produção (média por GM por cultivar)
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
                        fig_gm.update_layout(
                            plot_bgcolor="white",
                            xaxis=dict(showgrid=True, gridcolor="lightgray", dtick=1),
                            yaxis=dict(showgrid=True, gridcolor="lightgray")
                        )

                        st.plotly_chart(fig_gm, use_container_width=True)

                    else:
                        st.info("❌ Dados insuficientes para gerar o gráfico de GM.")

                #🧩 Heatmap Interativo: Desempenho Relativo por Local x Cultivar
               
                with st.expander("🧩 Heatmap Interativo: Desempenho Relativo por Local x Cultivar", expanded=False):
                    df_heatmap = df_faixa_completo.copy()

                    if not df_heatmap.empty and "prod_sc_ha" in df_heatmap.columns and "Cultivar" in df_heatmap.columns:
                        # Cria coluna Local
                        df_heatmap["Local"] = df_heatmap["Fazenda"].astype(str) + "_" + df_heatmap["Cidade"].astype(str)

                        # Calcula % com base no maior valor de cada local
                        df_heatmap["Prod_Max_Local"] = df_heatmap.groupby("Local")["prod_sc_ha"].transform("max")
                        df_heatmap["Prod_%"] = (df_heatmap["prod_sc_ha"] / df_heatmap["Prod_Max_Local"]) * 100

                        # Pivot: linhas = Local, colunas = Cultivar, valores = Prod %
                        heatmap_pivot = df_heatmap.pivot_table(
                            index="Local",
                            columns="Cultivar",
                            values="Prod_%",
                            aggfunc="mean"
                        )

                        # Ordena locais por Microrregião, se existir
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

                        # Escala de cores ajustada (mais amarelo e verde, menos rosa)
                        escala_de_cores = [
                        (0.00, "lightcoral"),     # até 35% -> rosa claro
                        (0.35, "lightcoral"),
                        (0.45, "lightyellow"),    # 45-55% -> amarelo
                        (0.55, "lightyellow"),
                        (0.70, "lightgreen"),     # 55-70% -> verde claro
                        (0.80, "mediumseagreen"), # 70-80% -> verde médio
                        (1.00, "green")           # 80-100% -> verde escuro
                    ]


                        # Heatmap
                        fig = px.imshow(
                            heatmap_pivot,
                            text_auto=".0f",
                            color_continuous_scale=escala_de_cores,
                            aspect="auto",
                            labels=dict(x="Cultivar", y="Local", color="Produtividade (%)")
                        )

                        fig.update_layout(
                            title="Produção Relativa por Cultivar e Local (100% = Maior do Local)",
                            xaxis_title="Cultivar",
                            yaxis_title="Produtor + Cidade",
                            plot_bgcolor="white",
                            coloraxis_colorbar=dict(
                                title="Produtividade (%)",
                                tickvals=[0, 20, 40, 60, 80, 100],
                                ticktext=["0%", "20%", "40%", "60%", "80%", "100%"]
                            )
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("❌ Dados insuficientes para gerar o heatmap.")                       
                 

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
            #
            with aba3:
                st.markdown("### 🤜🏻🤛🏻 Análise Head to Head")

                if not df_faixa_completo.empty:
                    colunas_visiveis_faixa = [
                        "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index", "populacao", "GM",
                        "Área Parcela", "plts_10m", "Pop_Final", "Umidade (%)",
                        "prod_kg_ha", "prod_sc_ha", "PMG"
                    ]

                    df_visualizacao_faixa = df_faixa_completo[
                        [col for col in colunas_visiveis_faixa if col in df_faixa_completo.columns]
                    ]

                    st.dataframe(df_visualizacao_faixa, height=500)
#--------------------------------------------------------------
                 

        st.session_state["df_final_av7"] = df_final_av7
        st.session_state["df_faixa_completo"] = df_faixa_completo

    else:
        st.warning("⚠️ O DataFrame está vazio ou não foi carregado corretamente.")
else:
    st.error("❌ Nenhum dado encontrado na sessão. Certifique-se de carregar os dados na página principal primeiro.")