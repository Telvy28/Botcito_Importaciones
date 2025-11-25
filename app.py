import streamlit as st
import os
from dotenv import load_dotenv
from utils.supabase_client import SupabaseClient
from utils.chatbot import ImportacionesChatbot

# Cargar variables
load_dotenv()

# Configuración de página
st.set_page_config(
    page_title="Chatbot Importaciones IA", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS MEJORADO: Sidebar más estrecho y mejor distribución
st.markdown("""
<style>
    /* Sidebar más estrecho */
    section[data-testid="stSidebar"] {
        width: 320px !important;
        min-width: 320px !important;
        max-width: 320px !important;
    }
    
    /* Ajuste del contenido principal cuando hay sidebar */
    .main > div {
        margin-left: 320px;
    }
    
    /* Ajuste global */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Estilo para el contenedor del Power BI */
    .powerbi-container {
        margin-top: 20px;
        height: 85vh;
        width: 100%;
    }
    
    /* Mejoras en el chat */
    .stChatMessage {
        font-size: 0.9rem;
    }
    
    /* Input del chat más visible */
    .stChatInputContainer {
        padding-top: 0.5rem;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ========== INICIALIZACIÓN ==========
@st.cache_resource
def init_db():
    return SupabaseClient()

db = init_db()

# ========== SIDEBAR: CHATBOT ==========
with st.sidebar:
    st.title("🤖 Asistente IA")
    
    # Selectores
    chat_mode = st.radio(
        "Versión:",
        ["💬 Chat v4.0 (Rápido)", "🚀 Chat v5.0 (SQL Agent)"]
    )
    
    st.divider()
    
    model_option = st.selectbox(
        "🧠 Modelo IA:",
        ["🆓 Groq (Llama 3.3 - Potente)", "💰 DeepSeek (Chat)", "🌟 OpenAI (GPT-4o)"]
    )
    
    # Mapeo de providers
    if "Groq" in model_option: provider = "groq"
    elif "DeepSeek" in model_option: provider = "deepseek"
    else: provider = "openai"

    st.divider()

    # --- LÓGICA DEL CHAT CON SCROLL ---
    # Usamos st.container con height fijo para crear el scroll
    chat_container = st.container(height=500, border=True)
    
    # Input fuera del contenedor de scroll para que siempre esté visible abajo (o arriba según prefieras)
    # Nota: En sidebar el input siempre va al final o al principio.
    
    # 1. Renderizar historial dentro del contenedor con scroll
    with chat_container:
        current_chat = []
        if chat_mode == "💬 Chat v4.0 (Rápido)":
            if "chat_v4" not in st.session_state: st.session_state.chat_v4 = []
            current_chat = st.session_state.chat_v4
        else:
            if "chat_v5" not in st.session_state: st.session_state.chat_v5 = []
            current_chat = st.session_state.chat_v5
            
        for msg in current_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 2. Input del Chat
    if prompt := st.chat_input("Pregunta sobre importaciones..."):
        # Añadir usuario
        current_chat.append({"role": "user", "content": prompt})
        with chat_container: # Mostrar inmediatamente en la caja
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # Procesar respuesta
        try:
            response = ""
            if chat_mode == "💬 Chat v4.0 (Rápido)":
                bot = ImportacionesChatbot(db, provider=provider)
                # Spinner en el sidebar
                with st.spinner("🔍 Analizando..."):
                    response = bot.chat(prompt)
            else:
                # Chat v5.0 - SQL Agent
                try:
                    from utils.langchain_chatbot import LangChainChatbot
                except ImportError:
                    # Si falla, intentar importación directa
                    from langchain_chatbot import LangChainChatbot
                
                with st.spinner("🧠 Ejecutando consulta SQL..."):
                    agent = LangChainChatbot(provider=provider)
                    response = agent.chat(prompt)
                    # Limpiar respuesta verbose si es necesario
                    if "Thought:" in response:
                        # Extraer solo la respuesta final
                        if "Final Answer:" in response:
                            response = response.split("Final Answer:")[-1].strip()
            
            # Añadir respuesta
            current_chat.append({"role": "assistant", "content": response})
            with chat_container: # Mostrar en la caja
                with st.chat_message("assistant"):
                    st.markdown(response)
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Botón limpiar
    if st.button("🗑️ Limpiar", use_container_width=True):
        st.session_state.chat_v4 = []
        st.session_state.chat_v5 = []
        st.rerun()

# ========== ÁREA PRINCIPAL: POWER BI ==========
powerbi_url = os.getenv("POWERBI_URL", "")

if powerbi_url:
    # Usamos un div contenedor con padding-top inline para bajarlo visualmente
    st.markdown(f"""
        <div style="padding-top: 30px; height: 90vh;">
            <iframe 
                title="Dashboard Importaciones" 
                width="100%" 
                height="100%" 
                src="{powerbi_url}" 
                frameborder="0" 
                allowFullScreen="true">
            </iframe>
        </div>
    """, unsafe_allow_html=True)
else:
    st.info("👈 Configura POWERBI_URL en tu archivo .env")