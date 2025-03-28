import streamlit as st
import pandas as pd
import io
from supabase import create_client
from streamlit import cache_data

# Configuração do Supabase
SUPABASE_URL = 'https://lwklfogmduwitmbqbgyp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3a2xmb2dtZHV3aXRtYnFiZ3lwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg1MjIyNDQsImV4cCI6MjA1NDA5ODI0NH0.3RMzkQnRcnZj2XtK3YZm4z4VHpLlwe3N8ulOiqcbC-I'

# Criando cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuração da página
st.set_page_config(layout="wide")

# 👉 Descrição da página

st.title("🎲 Avaliações de Soja")
st.subheader("👏🏻👏🏻 Bem-vindo ao **JAUM** Análise de Dados")
st.divider()

st.markdown("## 🌱 JAUM – Jornada de Avaliação Unificada de Materiais")

st.markdown("""
**O que é o JAUM?**  
JAUM representa uma etapa essencial conduzida pelo **Time de Desenvolvimento Técnico de Culturas**, responsável por avaliar, monitorar e posicionar cultivares em diferentes regiões do Brasil antes do lançamento comercial.

Essa jornada busca entender o desempenho agronômico dos materiais, auxiliando na tomada de decisão e recomendação técnica com base em dados reais de campo.

---

### 🔠 Significado da sigla:

- **J – Jornada**  
  Percurso que o cultivar faz desde os testes iniciais até sua recomendação para lançamento, considerando diferentes regiões, ambientes e manejos.

- **A – Avaliação**  
  Análise detalhada do desempenho agronômico, sanidade, produtividade e estabilidade dos cultivares ao longo dos ciclos.

- **U – Unificação**  
  Consolidação das informações geradas nos ensaios, permitindo uma visão integrada e comparativa entre diferentes materiais.

- **M – Monitoramento**  
  Acompanhamento contínuo e **posicionamento técnico** baseado em dados reais de campo, apoiando decisões estratégicas e operacionais.

---
""")


st.markdown("""
Esta página é responsável por **carregar, integrar e exibir os dados das avaliações** de soja diretamente do banco Supabase.
Você pode optar por carregar com cache (mais rápido) ou buscar os dados mais atualizados (mais lento).
""")

# Tabelas a serem carregadas
TABELAS = [
    "av1TratamentoSoja", "av2TratamentoSoja", "av3TratamentoSoja", "av4TratamentoSoja", "av5TratamentoSoja", 
    "av6TratamentoSoja", "av7TratamentoSoja", "avaliacao", "fazenda", "cidade", "estado", "tratamentoBase", "users"
]

# Função para buscar dados do Supabase com cache
@cache_data
def fetch_table(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Erro ao obter dados da tabela {table_name}: {response.error}")
            return pd.DataFrame()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao processar a tabela {table_name}: {str(e)}")
        return pd.DataFrame()

# Botão para carregar os dados do Supabase
col1, col2, col3 = st.columns([2.5, 2.5, 6]) # proporcional: 25%, 25%, 60%

with col1:
    st.markdown("✅ Usa dados em cache (mais rápido).")
    if st.button("🔄 Carregar Dados do Supabase (com cache)"):
        dataframes = {tabela: fetch_table(tabela) for tabela in TABELAS}
        st.session_state["dataframes"] = dataframes
        st.success("✅ Dados carregados e armazenados!")

with col2:
    st.markdown("⚠️ Atualiza dados direto do Supabase (mais lento).")
    if st.button("♻️ Carregar Dados do Supabase (sem cache)"):
        fetch_table.clear() # limpa o cache da função
        dataframes = {tabela: fetch_table(tabela) for tabela in TABELAS}
        st.session_state["dataframes"] = dataframes
        st.success("✅ Dados carregados direto do Supabase!")

# col3 fica vazia para ocupar o resto do espaço e alinhar botões à direita

# Verifica se os dados já foram carregados
if "dataframes" in st.session_state:
    dataframes = st.session_state["dataframes"]
    avaliacao = dataframes.get("avaliacao")
    fazenda = dataframes.get("fazenda")
    users = dataframes.get("users")
    cidade = dataframes.get("cidade")
    estado = dataframes.get("estado")

    # Função para realizar merges
    def merge_with_avaliacao(df, avaliacao):
        if df is not None and not df.empty and avaliacao is not None:
            return df.merge(
                avaliacao[['uuid', 'fazendaRef', 'tipoAvaliacao', 'avaliado']],
                left_on='avaliacaoRef',
                right_on='uuid',
                how='left'
            ).drop(columns=['uuid'], errors='ignore')
        return None
    
    merged_dataframes = {
        f"{tabela}_Avaliacao": merge_with_avaliacao(dataframes.get(tabela), avaliacao)
        for tabela in ["av1TratamentoSoja", "av2TratamentoSoja", "av3TratamentoSoja", "av4TratamentoSoja", 
                       "av5TratamentoSoja", "av6TratamentoSoja", "av7TratamentoSoja"]
    }
    
    def merge_with_fazenda(df, fazenda):
        if df is not None and not df.empty and fazenda is not None:
            return df.merge(
                fazenda[['uuid', 'nomeFazenda', 'nomeProdutor', 'latitude', 'longitude', 'altitude', 'regional', 'dataPlantio', 'dataColheita', 'dtcResponsavelRef', 'cidadeRef']],
                left_on='fazendaRef',
                right_on='uuid',
                how='left'
            ).drop(columns=['uuid'], errors='ignore')
        return None
    
    merged_dataframes_fazenda = {
        f"{key}_Fazenda": merge_with_fazenda(merged_dataframes[key], fazenda)
        for key in merged_dataframes.keys()
    }
    
    def merge_with_users(df, users):
        if df is not None and not df.empty and users is not None:
            return df.merge(
                users[['uuid', 'displayName']],
                left_on='dtcResponsavelRef',
                right_on='uuid',
                how='left'
            ).drop(columns=['uuid'], errors='ignore')
        return None
    
    merged_dataframes_users = {
        f"{key}_Users": merge_with_users(merged_dataframes_fazenda[key], users)
        for key in merged_dataframes_fazenda.keys()
    }
    
    def merge_with_cidade(df, cidade):
        if df is not None and not df.empty and cidade is not None:
            return df.merge(
                cidade[['uuid', 'nomeCidade', 'estadoRef']],
                left_on='cidadeRef',
                right_on='uuid',
                how='left'
            ).drop(columns=['uuid'], errors='ignore')
        return None
    
    merged_dataframes_cidade = {
        f"{key}_Cidade": merge_with_cidade(merged_dataframes_users[key], cidade)
        for key in merged_dataframes_users.keys()
    }

    def merge_with_estado(df, estado):
        if df is not None and not df.empty and estado is not None:
            return df.merge(
                estado[['uuid', 'codigoEstado', 'nomeEstado']],
                left_on='estadoRef',
                right_on='uuid',
                how='left'
            ).drop(columns=['uuid'], errors='ignore')
        return None

    # Aplicando a mesclagem com a tabela estado
    merged_dataframes_estado = {
        f"{key}_Estado": merge_with_estado(merged_dataframes_cidade[key], estado)
        for key in merged_dataframes_cidade.keys()
    }

    # **Salvando os DataFrames no session_state para uso em outras páginas**
    st.session_state["merged_dataframes"] = merged_dataframes_estado

    # Exibir os dados mesclados com estado
    with st.expander("🔹 Base de dados sem tratamento"):
        st.subheader("📄 Visualização dos Dados carregados")

        df_merged_selectbox = st.selectbox(
            "Escolha uma avaliacão para visualizar",
            list(merged_dataframes_estado.keys())
        )

        selected_merged_df = merged_dataframes_estado.get(df_merged_selectbox, None)

        if selected_merged_df is not None:
            st.dataframe(selected_merged_df, height=400)

            # Exportação para Excel com os dados finais
            output_merged = io.BytesIO()
            with pd.ExcelWriter(output_merged, engine='xlsxwriter') as writer:
                selected_merged_df.to_excel(writer, index=False, sheet_name=df_merged_selectbox[:31])

            st.download_button(
                label=f"📥 Baixar {df_merged_selectbox}",
                data=output_merged.getvalue(),
                file_name=f"{df_merged_selectbox}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("❌ Nenhum dado disponível para exibição.")

else:
    st.error("❌ Os dados ainda não foram carregados. Clique no botão acima para carregá-los.")
