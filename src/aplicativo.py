import pandas as pd
import streamlit as st
import openpyxl
import base64
from pathlib import Path

#   CONFIGURAÇÃO DE DIRETÓRIOS

PROJECT_ROOT = Path(__file__).resolve().parent.parent      # raiz do projeto
DATA_DIR = PROJECT_ROOT / "data"                           # pasta de dados
IMAGES_DIR = DATA_DIR / "images"                           # pasta de imagens

#   FUNÇÃO PARA CARREGAR IMAGENS
def to_base64(path):
    """
    Recebe um nome de arquivo ou Path.
    Procura automaticamente em data/images/.
    """
    p = Path(path)
    if not p.is_absolute():
        p = IMAGES_DIR / p

    p = p.resolve()

    if not p.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {p}")

    b = p.read_bytes()
    return base64.b64encode(b).decode()

# Carregar imagens
img1 = to_base64("uepb.jpg")
img2 = to_base64("hu.jpg")



#   ESTILO DAS IMAGENS SUPERIORES
st.markdown(
    f"""
    <style>
    .top-left-container {{
        position: fixed;
        top: 80px;
        left: 10px;
        display: flex;
        gap: 10px;
        z-index: 1000;
    }}
    .top-left-container img {{
        width: 120px;
    }}
    </style>

    <div class="top-left-container">
        <img src="data:image/png;base64,{img1}">
        <img src="data:image/png;base64,{img2}">
    </div>
    """,
    unsafe_allow_html=True
)

#   CONFIG DA PÁGINA
st.set_page_config(page_title="Agendamento Cirúrgico🏥")
st.title("Agendamento Cirúrgico🏥")

st.text("""Hospital Universitário👨‍⚕
Universidade Estadual Da Paraíba📗
""")

#   FUNÇÃO DE CARREGAMENTO SEGURO DE EXCEL

def carregar_excel(nome_arquivo):
    caminho = DATA_DIR / nome_arquivo
    try:
        return pd.read_excel(caminho)
    except Exception as e:
        st.error(f"Erro ao carregar {nome_arquivo}: {e}")
        return pd.DataFrame()

# Carregar todos os arquivos
agendamento_cirurgias = carregar_excel("agendamentos_cirurgias.xlsx")
historico_cirurgico = carregar_excel("historico_cirurgias.xlsx")
escala_profissionais = carregar_excel("escala_profissionais.xlsx")
fila_paciente = carregar_excel("fila_pacientes.xlsx")
indicadores_salas = carregar_excel("indicadores_salas.xlsx")
materiais_agendados = carregar_excel("materiais_agendados.xlsx")
materiais_estoque = carregar_excel("materiais_estoque.xlsx")
profissionais = carregar_excel("profissionais.xlsx")
salas_cirurgicas = carregar_excel("salas_cirurgicas.xlsx")

#   GERAÇÃO AUTOMÁTICA DE AGENDA
def gerar_agenda(agendamentos, fila, profs, salas):

    def encontrar_coluna(possibles, df):
        cols_lower = {c.lower(): c for c in df.columns}
        for nome in possibles:
            nome_lower = nome.lower()
            for c in cols_lower:
                if nome_lower == c or nome_lower in c:
                    return cols_lower[c]
        return None

    col_paciente_id_ag = encontrar_coluna(["id_paciente", "paciente", "paciente_id"], agendamentos)
    col_prof_id_ag     = encontrar_coluna(["id_profissional", "profissional_id", "cirurgiao_id"], agendamentos)
    col_sala_id_ag     = encontrar_coluna(["id_sala", "sala_id", "sala"], agendamentos)

    col_paciente_id_fila = encontrar_coluna(["id", "paciente_id"], fila)
    col_prof_id_profs    = encontrar_coluna(["id", "id_profissional"], profs)
    col_sala_id_salas    = encontrar_coluna(["id", "id_sala"], salas)

    col_nome_paciente = encontrar_coluna(["nome", "paciente"], fila)
    col_nome_prof     = encontrar_coluna(["nome", "profissional", "cirurgiao"], profs)
    col_nome_sala     = encontrar_coluna(["nome_sala", "sala"], salas)

    agenda = []

    for _, row in agendamentos.iterrows():

        # Paciente
        paciente_nome = "Não encontrado"
        if col_paciente_id_ag and col_paciente_id_fila:
            pac = fila[fila[col_paciente_id_fila] == row[col_paciente_id_ag]]
            if not pac.empty:
                paciente_nome = pac[col_nome_paciente].values[0]

        # Profissional
        prof_nome = "Não encontrado"
        if col_prof_id_ag and col_prof_id_profs:
            p = profs[profs[col_prof_id_profs] == row[col_prof_id_ag]]
            if not p.empty:
                prof_nome = p[col_nome_prof].values[0]

        # Sala
        sala_nome = "Não encontrada"
        if col_sala_id_ag and col_sala_id_salas:
            s = salas[salas[col_sala_id_salas] == row[col_sala_id_ag]]
            if not s.empty:
                sala_nome = s[col_nome_sala].values[0]
        #adicionando os dados na agenda principal
        agenda.append({
            "Paciente": paciente_nome,
            "Cirurgião": prof_nome,
            "Sala": sala_nome,
            "Data": row.get("data_cirurgia"),
            "Hora Início": row.get("hora_inicio"),
            "Hora Fim": row.get("hora_fim"),
            "Gravidade": row.get("gravidade")
        })

    return pd.DataFrame(agenda)

#   INTERFACE EM TABS
tab1, tab2, tab3, tab4 = st.tabs([
    "Agenda do Dia📊",
    "Materiais e Estoque📁",
    "Profissionais e Escalas👨‍⚕",
    "Indicadores🧠"
])
# TAB 1
with tab1:
    st.subheader("Agenda Automática")

    if st.button("Gerar agenda automaticamente"):
        agenda = gerar_agenda(
            agendamento_cirurgias,
            fila_paciente,
            profissionais,
            salas_cirurgicas
        )
        st.session_state["agenda"] = agenda
        st.success("Agenda gerada com sucesso!")

    if "agenda" in st.session_state:
        st.dataframe(st.session_state["agenda"])
    else:
        st.info("Clique no botão para gerar a agenda.")
# TAB 2
with tab2:
    st.subheader("Materiais e Estoque")
    col1, col2 = st.columns(2)

    with col1:
        st.write("Materiais Agendados")
        st.dataframe(materiais_agendados)

    with col2:
        st.write("Materiais em Estoque")
        st.dataframe(materiais_estoque)
# TAB 3
with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.write("Profissionais")
        st.dataframe(profissionais)

    with col2:
        st.write("Escalas dos Profissionais")
        st.dataframe(escala_profissionais)
# TAB 4
with tab4:
    st.subheader("Salas Cirúrgicas")
    st.dataframe(salas_cirurgicas)