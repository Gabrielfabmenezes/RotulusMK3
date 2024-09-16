import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import requests



url = "https://api.movidesk.com/public/v1/tickets"
token = st.secrets["api_key"]

# Parâmetros para filtrar os tickets
params = {
    'token': token,
    '$select': 'id,subject,status,category,createdDate,ownerTeam',
    #'$filter': "createdDate ge 2024-01-01 and createdDate le 2040-08-29"
}


st.set_page_config(page_title="Rotulus")

# Background da aplicação
st.markdown("""
    <style>
    .app-background {
        height: 100vh;
        margin: 0;
        padding: 0;
    }
    .stApp {
        background: linear-gradient(to right, #000814, #00814); 
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    /* Estilo para a barra lateral */
    [data-testid="stSidebar"] {
        background-color: #080D0F; /* Cor de fundo da barra lateral */
    }

    /* Estilo para os itens selecionados no menu lateral */
    [data-testid="stSidebar"] .st-radio label {
        color: #FFFFFF; /* Cor do texto dos itens */
    }

    [data-testid="stSidebar"] .st-radio input:checked + span {
        background-color: #6A0D91; /* Cor de fundo do ponto ao selecionar */
        border-radius: 50%;
        border: 2px solid #6A0D91; /* Borda roxa do ponto */
    }

    /* Estilo para os itens de menu quando selecionados */
    [data-testid="stSidebar"] .st-radio input:checked + span {
        color: #FFFFFF; /* Cor do texto ao selecionar */
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    .stButton {
        display: flex;
        justify-content: center; 
        margin-top: 20px;  
    }
    .stButton>button {
        display: flex;
        justify-content: center;
        align-items: center;
        max-width: 300px;  
        background-color: white;
        color: #F05555;
        border: 2px solid #F5C3C3;
        border-radius: 5px;
        padding: 10px 30px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s, color 0.3s, border-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #F78484;
        color: white;
        border-color: #F57474;
    }
    </style>
""", unsafe_allow_html=True)

# connectar banco de dados
conn = sqlite3.connect('info_dados.db')
cursor = conn.cursor()

# Criar tabelas se não existirem usuário padrão
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bloqueios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        cnpj TEXT NOT NULL,
        data DATE NOT NULL,
        tipo_atendimento TEXT NOT NULL
    )
''')
#referente a visualização de ticket criação de tabela
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    subject TEXT,
    status TEXT,
    category TEXT,
    createdDate TEXT,
    ownerTeam TEXT
)
''')



# usuário padrão create
cursor.execute('SELECT COUNT(*) FROM usuarios WHERE username = ?', ('Administrador',))
if cursor.fetchone()[0] == 0:
    cursor.execute("""
        INSERT INTO usuarios (username, password)
        VALUES ('Administrador', 'SD@tec2024')
    """)
    conn.commit()

conn.commit()

# Função para verificar o login do usuário
def verificar_login(username, password):
    cursor.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?', (username, password))
    return cursor.fetchone() is not None

# Função para exibir bloqueios
def exibir_bloqueios():
    cursor.execute('SELECT id, cliente, cnpj, tipo_atendimento, data FROM bloqueios')
    registros = cursor.fetchall()
    for registro in registros:
        id_registro, cliente, cnpj, tipo_atendimento, data = registro
        data_formatada = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        st.write(f"**Cliente:** {cliente}")
        st.write(f"**CNPJ:** {cnpj}")
        st.write(f"**Tipo de Atendimento:** {tipo_atendimento}")
        st.write(f"**Data:** {data_formatada}")
        if st.checkbox(f"Excluir {cliente} - {cnpj}", key=id_registro):
            if st.button("Excluir Selecionados", key=f"btn_{id_registro}"):
                excluir_bloqueios(id_registro)
                st.success(f"Cliente {cliente} ativado com sucesso!")
        st.write("---")

def excluir_bloqueios(id):
    cursor.execute('DELETE FROM bloqueios WHERE id = ?', (id,))
    conn.commit()


#Referente a Visualização de Ticket
def visualizar_dados():
    conn = sqlite3.connect('info_dados.db')
    df = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()

    if df.empty:
        st.write("Nenhum dado disponível no banco de dados.")
    else:

        df['id'] = df['id'].astype(int)

        # Conversão para formato legível (data)
        df['createdDate'] = pd.to_datetime(df['createdDate']).dt.strftime('%d/%m/%Y')

        st.write("Dados dos tickets no banco de dados:")

        # Exibir cada linha separadamente
        for index, row in df.iterrows():
            st.write(f"**ID**: {row['id']}")
            st.write(f"**Assunto**: {row['subject']}")
            st.write(f"**Status**: {row['status']}")
            st.write(f"**Categoria**: {row['category']}")
            st.write(f"**Data de Criação**: {row['createdDate']}")
            st.write(f"**Equipe Responsável**: {row['ownerTeam']}")
            st.write("---")  # melhorar a visualização
def gerar_senha():
    now = datetime.now()
    hora = now.hour + 10
    dia = now.day + 10
    return f"{hora}{dia}"
def atualizar_banco():
    response = requests.get(url, params=params)

    if response.status_code == 200:
        tickets = response.json()

        # Conectar ao banco de dados SQLite3
        conn = sqlite3.connect('info_dados.db')
        cursor = conn.cursor()

        # Crie a tabela se não existir
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY,
            subject TEXT,
            status TEXT,
            category TEXT,
            createdDate TEXT,
            ownerTeam TEXT
        )
        ''')

        # Limpa a tabela existente antes de inserir novos dados
        cursor.execute('DELETE FROM tickets')

        # Insira os dados na tabela
        for ticket in tickets:
            cursor.execute('''
            INSERT OR REPLACE INTO tickets (id, subject, status, category, createdDate, ownerTeam)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (ticket.get('id'), ticket.get('subject'), ticket.get('status'), ticket.get('category'),
                  ticket.get('createdDate'), ticket.get('ownerTeam')))

        # Salve (commit) as mudanças e feche a conexão
        conn.commit()
        conn.close()

        st.success("Dados atualizados com sucesso no banco de dados.")
    else:
        st.error(f"Erro ao buscar tickets: {response.status_code}")
        st.error(response.text)

#referente ao formulário de bloqueio, adiciona os bloqueados no banco
def adicionar_bloqueio(cliente, cnpj, tipo_atendimento, data):
    data_formatada = data.strftime('%Y-%m-%d')

    try:
        cursor.execute('''
            SELECT id FROM bloqueios WHERE cnpj = ? AND cliente = ?
        ''', (cnpj, cliente))
        resultado = cursor.fetchone()

        if resultado:
            id_registro = resultado[0]
            cursor.execute('''
                UPDATE bloqueios
                SET tipo_atendimento = ?, data = ?
                WHERE id = ?
            ''', (tipo_atendimento, data_formatada, id_registro))
            st.success("Bloqueio atualizado com sucesso!")
        else:
            cursor.execute('''
                INSERT INTO bloqueios (cliente, cnpj, tipo_atendimento, data) 
                VALUES (?, ?, ?, ?)
            ''', (cliente, cnpj, tipo_atendimento, data_formatada))
            st.success("Bloqueio adicionado com sucesso!")

        conn.commit()

    except Exception as e:
        st.error(f"Ocorreu um erro ao adicionar ou atualizar o bloqueio informado: {e}")





# Tela de login
def tela_login():
    st.write(" ")
    st.write(" ")
    st.write("### Login")
    username = st.text_input("Nome de usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Login"):
        if verificar_login(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success("Login bem-sucedido!")
        else:
            st.error("Nome de usuário ou senha incorretos.")

# Verifica se o usuário está logado no sistema
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    tela_login()
else:
    # Interface principal
    st.sidebar.title("Menu")
    option = st.sidebar.radio("Escolha uma opção", ["Visualização de Ticket", "Formulário de Bloqueio"])

    st.markdown("""
        <style>
        .centered-title {
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        [data-testid="stSidebar"] h1 {
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    if option == "Visualização de Ticket":

        st.sidebar.header("Menu")

        # Pedir senha ao usuário front end
        senha_correta = gerar_senha()
        senha_digitada = st.sidebar.text_input("Digite a senha para atualizar o banco", type="password")

        if st.sidebar.button("Atualizar Banco Local"):
            if senha_digitada == senha_correta:
                atualizar_banco()
            else:
                st.error("Senha incorreta!")

        if st.sidebar.button("Visualizar Dados"):
            visualizar_dados()


    elif option == "Formulário de Bloqueio":
        st.title("Formulário de Bloqueio")
        fm_cliente = st.sidebar.text_input("Cliente")
        fm_cnpj = st.sidebar.text_input("CNPJ")
        fm_tipo = st.sidebar.multiselect("Tipo de Atendimento",
                                         ["Atendimento Presencial", "Telefônico", "Suporte Chat", "Invoicy"])
        fm_date = st.sidebar.date_input("Data do Bloqueio")
        fm_button = st.sidebar.button("Enviar Formulário")

        if fm_button:
            if fm_cliente and fm_cnpj and fm_tipo and fm_date:
                adicionar_bloqueio(fm_cliente, fm_cnpj, ', '.join(fm_tipo), fm_date)
                st.success("Formulário enviado com sucesso!")
            else:
                st.sidebar.error("Por favor, preencha todos os campos.")



        exibir_bloqueios()


conn.close()
