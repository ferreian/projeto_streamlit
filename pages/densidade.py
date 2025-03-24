import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("🌱 Resultados de Densidade - Ensaios de Faixa")

st.markdown(
    """
    Esta página apresenta os resultados de **densidade** dos ensaios de faixa. 
    Os dados são carregados da memória da aplicação (
    `session_state`) e devem ser importados na página principal.
    """
)

# Verifica se os dados estão carregados no session_state
if "df_final_av7" in st.session_state:
    df_final_av7 = st.session_state["df_final_av7"]

    # Filtra apenas os dados de Densidade
    df_densidade = df_final_av7[df_final_av7["Teste"] == "Densidade"].copy()

    if not df_densidade.empty:
        st.success("✅ Dados de densidade carregados com sucesso!")

        colunas_visiveis_densidade = [
            "Produtor", "Cultivar", "UF", "Plantio", "Colheita", "Index",
            "populacao", "GM", "Área Parcela", "plts_10m", "Pop_Final",
            "Umidade (%)", "prod_kg_ha", "prod_sc_ha", "PMG"
        ]

        df_visualizacao_densidade = df_densidade[[col for col in colunas_visiveis_densidade if col in df_densidade.columns]]

        st.dataframe(df_visualizacao_densidade, height=500, use_container_width=True)

        # Botão de download
        output_densidade = io.BytesIO()
        with pd.ExcelWriter(output_densidade, engine='xlsxwriter') as writer:
            df_densidade.to_excel(writer, index=False, sheet_name="resultado_densidade")

        st.download_button(
            label="📥 Baixar Resultado Densidade",
            data=output_densidade.getvalue(),
            file_name="resultado_densidade.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Armazena no session_state para usar em outras abas ou páginas
        st.session_state["df_densidade"] = df_densidade
    else:
        st.warning("⚠️ Nenhum dado com Teste = 'Densidade' encontrado.")
else:
    st.error("❌ Nenhum dado encontrado na sessão. Carregue os dados na página principal primeiro.")
