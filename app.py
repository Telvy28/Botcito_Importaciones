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
    st.markdown("# 🤖 Asistente IA")
    st.markdown('<p class="firma">by Telvy Pizarro</p>', unsafe_allow_html=True)
    st.markdown("---")
    
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
    
    # ====== INPUT Y BOTÓN ARRIBA (siempre visibles) ======
    prompt = st.chat_input("Pregunta sobre importaciones...")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.session_state.chat_v4 = []
            st.session_state.chat_v5 = []
            st.rerun()
    
    st.divider()
    
    # ====== CONTENEDOR DE MENSAJES CON SCROLL ======
    # Reducido a 350px para que input quede visible sin scroll
    chat_container = st.container(height=350, border=True)
    
    # Determinar chat activo
    current_chat = []
    if chat_mode == "💬 Chat v4.0 (Rápido)":
        if "chat_v4" not in st.session_state: 
            st.session_state.chat_v4 = []
        current_chat = st.session_state.chat_v4
    else:
        if "chat_v5" not in st.session_state: 
            st.session_state.chat_v5 = []
        current_chat = st.session_state.chat_v5
    
    # Renderizar historial dentro del contenedor
    with chat_container:
        for msg in current_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # ====== PROCESAMIENTO DEL PROMPT ======
    if prompt:
        # Añadir mensaje del usuario
        current_chat.append({"role": "user", "content": prompt})
        
        # Procesar respuesta
        try:
            response = ""
            if chat_mode == "💬 Chat v4.0 (Rápido)":
                bot = ImportacionesChatbot(db, provider=provider)
                with st.spinner("🔍 Analizando..."):
                    response = bot.chat(prompt)
            else:
                # Chat v5.0 - SQL Agent
                try:
                    from utils.langchain_chatbot import LangChainChatbot
                except ImportError:
                    from langchain_chatbot import LangChainChatbot
                
                with st.spinner("🧠 Ejecutando consulta SQL..."):
                    agent = LangChainChatbot(provider=provider)
                    response = agent.chat(prompt)
                    
                    # Limpiar respuesta verbose
                    if "Thought:" in response:
                        if "Final Answer:" in response:
                            response = response.split("Final Answer:")[-1].strip()
            
            # Añadir respuesta del asistente
            current_chat.append({"role": "assistant", "content": response})
            
            # Forzar rerun para actualizar el chat
            st.rerun()
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")

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
