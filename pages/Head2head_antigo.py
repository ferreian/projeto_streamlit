import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🤜🏻🤛🏻 Análise Head to Head")

# 🔁 Checa se o df_faixa_completo foi carregado na sessão
if "df_faixa_completo" not in st.session_state:
    st.warning("⚠️ O DataFrame 'df_faixa_completo' não foi carregado.")
    st.stop()

df = st.session_state["df_faixa_completo"]
df = df[df["Teste"] == "Faixa"].copy()

# Layout com duas colunas: 15% (filtros), 85% (conteúdo)
col_filtros, col_conteudo = st.columns([0.15, 0.85])

# 🎛️ Filtros em Expanders com Checkbox (desmarcados por padrão)
with col_filtros:
    st.markdown("### 🎛️ Filtros")

    # 👉 Microrregião
    if "Microrregiao" in df.columns:
        with st.expander("🌎 Microrregião", expanded=False):
            microrregioes = sorted(df["Microrregiao"].dropna().unique())
            microrregioes_selecionadas = [
                m for m in microrregioes if st.checkbox(m, key=f"microrregiao_{m}", value=False)
            ]
            if microrregioes_selecionadas:
                df = df[df["Microrregiao"].isin(microrregioes_selecionadas)]

    # 👉 Estado
    if "Estado" in df.columns:
        with st.expander("🗺️ Estado", expanded=False):
            estados = sorted(df["Estado"].dropna().unique())
            estados_selecionados = [
                e for e in estados if st.checkbox(e, key=f"estado_{e}", value=False)
            ]
            if estados_selecionados:
                df = df[df["Estado"].isin(estados_selecionados)]

    # 👉 Cidade
    if "Cidade" in df.columns:
        with st.expander("🏘️ Cidade", expanded=False):
            cidades = sorted(df["Cidade"].dropna().unique())
            cidades_selecionadas = [
                c for c in cidades if st.checkbox(c, key=f"cidade_{c}", value=False)
            ]
            if cidades_selecionadas:
                df = df[df["Cidade"].isin(cidades_selecionadas)]

    # 👉 Fazenda
    if "Fazenda" in df.columns:
        with st.expander("🏡 Fazenda", expanded=False):
            fazendas = sorted(df["Fazenda"].dropna().unique())
            fazendas_selecionadas = [
                f for f in fazendas if st.checkbox(f, key=f"fazenda_{f}", value=False)
            ]
            if fazendas_selecionadas:
                df = df[df["Fazenda"].isin(fazendas_selecionadas)]
#====


# 👉 Lado direito: análise head to head
with col_conteudo:
    # Função de comparação
    def gerar_comparacoes(df):
        resultados = []
        cultivares = df["Cultivar"].dropna().unique()

        for head in cultivares:
            dados_head = df[df["Cultivar"] == head]
            for check in cultivares:
                if head == check:
                    continue

                dados_check = df[df["Cultivar"] == check]
                comparacoes = pd.merge(
                    dados_head, dados_check, on="FazendaRef", suffixes=("_head", "_check")
                )
                comparacoes = comparacoes[
                    (comparacoes["Cultivar_head"] == head) &
                    (comparacoes["Cultivar_check"] == check)
                ]

                if comparacoes.empty:
                    continue

                comparacoes["Diferenca"] = comparacoes["prod_sc_ha_head"] - comparacoes["prod_sc_ha_check"]
                comparacoes["Win"] = (comparacoes["Diferenca"] > 0).astype(int)

                resultados.append({
                    "Head": head,
                    "Check": check,
                    "Head Média (sc/ha)": comparacoes["prod_sc_ha_head"].mean(),
                    "Check Média (sc/ha)": comparacoes["prod_sc_ha_check"].mean(),
                    "Diferença Média (sc/ha)": comparacoes["Diferenca"].mean(),
                    "Nº de Comparações": len(comparacoes),
                    "Vitórias do Head": comparacoes["Win"].sum(),
                    "% Vitórias Head": round(comparacoes["Win"].mean() * 100, 1),

                    # 🧬 HEAD
                    "População Head": comparacoes["Pop_Final_head"].mean() if "Pop_Final_head" in comparacoes else None,
                    "AIV Head": comparacoes["AIV_head"].mean() if "AIV_head" in comparacoes else None,
                    "ALT Head": comparacoes["ALT_head"].mean() if "ALT_head" in comparacoes else None,
                    "PMG Head": comparacoes["PMG_head"].mean() if "PMG_head" in comparacoes else None,
                    "ENG Head": comparacoes["ENG_head"].mean() if "ENG_head" in comparacoes else None,
                    "AC Head": comparacoes["AC_head"].mean() if "AC_head" in comparacoes else None,

                    # 🧪 CHECK
                    "População Check": comparacoes["Pop_Final_check"].mean() if "Pop_Final_check" in comparacoes else None,
                    "AIV Check": comparacoes["AIV_check"].mean() if "AIV_check" in comparacoes else None,
                    "ALT Check": comparacoes["ALT_check"].mean() if "ALT_check" in comparacoes else None,
                    "PMG Check": comparacoes["PMG_check"].mean() if "PMG_check" in comparacoes else None,
                    "ENG Check": comparacoes["ENG_check"].mean() if "ENG_check" in comparacoes else None,
                    "AC Check": comparacoes["AC_check"].mean() if "AC_check" in comparacoes else None,
                })

        return pd.DataFrame(resultados)




    st.markdown("### ⚙️ Comparações entre Cultivares")

    if st.button("🔄 Gerar Comparações", key="btn_gerar"):
        st.session_state["resultado_h2h"] = gerar_comparacoes(df)

    if "resultado_h2h" in st.session_state:
        df_resultado = st.session_state["resultado_h2h"]

        if df_resultado.empty:
            st.warning("Nenhuma comparação disponível.")
            st.stop()

        st.markdown("### 📋 Tabela Head to Head")

        # Ordena as colunas de forma mais clara
        colunas_ordenadas = [
            "Head", "Check",
            "Head Média (sc/ha)", "Check Média (sc/ha)", "Diferença Média (sc/ha)",
            "Nº de Comparações", "Vitórias do Head", "% Vitórias Head",

            # Head info
            "População Head", "AIV Head", "ALT Head", "PMG Head", "ENG Head", "AC Head",

            # Check info
            "População Check", "AIV Check", "ALT Check", "PMG Check", "ENG Check", "AC Check"
        ]

        # Apenas as colunas que realmente existem
        colunas_existentes = [col for col in colunas_ordenadas if col in df_resultado.columns]

        # Exibe no app
        st.dataframe(df_resultado[colunas_existentes], use_container_width=True)

        csv = df_resultado.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar Comparações", data=csv, file_name="head_to_head_resultado.csv", mime="text/csv")

        st.markdown("### 🎯 Comparar Cultivares Específicos")

        col1, col2 = st.columns(2)
        cultivares = sorted(df["Cultivar"].dropna().unique())
        with col1:
            head_cultivar = st.selectbox("🧬 Cultivar HEAD", cultivares, key="head_select")
        with col2:
            check_cultivar = st.selectbox("🧪 Cultivar CHECK", cultivares, key="check_select")

        if head_cultivar and check_cultivar and head_cultivar != check_cultivar:
            df_detalhado = df[df["Cultivar"].isin([head_cultivar, check_cultivar])]
            df_head = df_detalhado[df_detalhado["Cultivar"] == head_cultivar]
            df_check = df_detalhado[df_detalhado["Cultivar"] == check_cultivar]

            df_comparacoes = pd.merge(
                df_head, df_check, on="FazendaRef", suffixes=("_head", "_check")
            )
            df_comparacoes = df_comparacoes[
                (df_comparacoes["Cultivar_head"] == head_cultivar) &
                (df_comparacoes["Cultivar_check"] == check_cultivar)
            ]

            if not df_comparacoes.empty:
                df_comparacoes["Diferenca"] = df_comparacoes["prod_sc_ha_head"] - df_comparacoes["prod_sc_ha_check"]
                df_comparacoes["Resultado"] = df_comparacoes["Diferenca"].apply(lambda x: "Vitória" if x > 0 else "Derrota")
                df_comparacoes["Local"] = df_comparacoes["Fazenda_head"] + " - " + df_comparacoes["Cidade_head"]

                fig = px.bar(
                    df_comparacoes,
                    x="Local",
                    y="Diferenca",
                    color="Resultado",
                    color_discrete_map={"Vitória": "#4CAF50", "Derrota": "#F44336"},
                    text="Diferenca",
                    labels={"Diferenca": "Diferença de Produtividade (sc/ha)", "Local": "Local"},
                    title=f"Diferença de Produtividade - {head_cultivar} vs {check_cultivar}"
                )

                fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig.update_layout(xaxis_tickangle=-45, height=500, plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Nenhuma comparação encontrada entre os dois cultivares.")
