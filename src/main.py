import streamlit as st
import os
import time
import json
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 1. CONFIGURACIÓN INICIAL Y ESTILOS ---
st.set_page_config(page_title="Simulador Nexus V3", page_icon="💻", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    h1 { text-align: center; color: #00BA37; }
    
    /* Estilo para el indicador RAG */
    .rag-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #cccccc;
        border-left: 5px solid #00BA37;
        color: #31333F;
        font-size: 0.9em;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Función para cargar RAG
def cargar_conocimiento():
    carpeta = "config" 
    archivo = "RAG_soporte.json"
    ruta_completa = os.path.join(carpeta, archivo)
    try:
        with open(ruta_completa, 'r', encoding='utf-8') as f:
            return json.load(f), ruta_completa    
    except FileNotFoundError:
        return {"error": f"No se encontró el archivo en: {ruta_completa}"}, "Error de Ruta"

politicas_empresa, nombre_rag = cargar_conocimiento()

#Función para obtener historial
def obtener_historial_como_texto():
    texto_historial = ""
    mensajes_recientes = st.session_state.mensajes[-8:]
    
    for msg in mensajes_recientes:
        rol = "SOPORTE" if msg["role"] == "assistant" else "CLIENTE"
        texto_historial += f"{rol}: {msg['content']}\n"
    return texto_historial

# --- 2. GESTIÓN DE ESTADO ---
if "pagina_actual" not in st.session_state: st.session_state.pagina_actual = "configuracion"
if "mensajes" not in st.session_state: st.session_state.mensajes = []
if "caso_activo" not in st.session_state: st.session_state.caso_activo = True
if "simulacion_corriendo" not in st.session_state: st.session_state.simulacion_corriendo = False


if "config_api_key" not in st.session_state: st.session_state.config_api_key = ""
if "config_proveedor" not in st.session_state: st.session_state.config_proveedor = "Groq (Llama 3)"
if "config_perfil" not in st.session_state: st.session_state.config_perfil = ""
if "config_instruccion" not in st.session_state: st.session_state.config_instruccion = ""
if "config_contexto" not in st.session_state: st.session_state.config_contexto = ""
if "config_intencion" not in st.session_state: st.session_state.config_intencion = ""


# --- PANTALLA 1: CONFIGURACIÓN ---
def mostrar_pantalla_configuracion():
    st.title("Agente Simulador Nexus")
    st.markdown("---")
    
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.subheader("RAG agregado")
        
        st.markdown(f"""
        <div class="rag-box">
            📂 <b>Base de Conocimiento Activa:</b><br>
            <code>{nombre_rag}</code><br>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()

        proveedor = st.selectbox(
            "Selecciona el LLM (Cerebro):",
            ["Seleccionar...", "Groq (Llama 3)", "Google (Gemini)"]
        )
        
        api_key_input = ""
        
        if proveedor == "Groq (Llama 3)":
            api_key_input = st.text_input("🔑 Tu Groq API Key:", type="password", value=st.session_state.config_api_key)
            st.caption("Modelo: llama-3.3-70b-versatile")
            
        elif proveedor == "Google (Gemini)":
            api_key_input = st.text_input("🔑 Tu Google API Key:", type="password", value=st.session_state.config_api_key)
            st.caption("Modelo: gemini-2.5-flash")
            
        elif proveedor == "Seleccionar...":
            st.info(" Selecciona un modelo para empezar.")

    with col_der:
        st.warning(" **Diseño del Cliente (Actor)**")
        
        with st.form("config_form"):
            c_perfil = st.text_area("Perfil",placeholder="Aquí describe al cliente: Edad, rasgos distintivos, nivel de conocimiento (ej: 'Le dice cajita al router')...", height=100)
            c_animo = st.selectbox("Ánimo Inicial", ["Tranquilo", "Confundido", "Molesto"])
            c_contexto = st.text_area("Contexto", placeholder="Describe la situación: ¿Desde cuándo falla? ¿Qué problema tiene con el servicio?...", height=80)
            c_intencion = st.text_area("Objetivo", placeholder="¿Qué quiere conseguir? (Ej: Que vaya un técnico, cancelar el servicio, un reembolso)...", height=80)
            
            submitted = st.form_submit_button("GUARDAR Y LANZAR SIMULACIÓN")
            
            if submitted:
                if proveedor == "Seleccionar..." or not api_key_input:
                    st.error("⚠️ Selecciona un proveedor e ingresa la API Key.")
                else:
                    instrucciones_tono = {
                        "Tranquilo": "El cliente se expresa de forma calmada y cooperativa. Responde con claridad y está dispuesto a seguir instrucciones.",
                        "Confundido": "El cliente muestra dudas, no entiende bien el problema o las indicaciones. Hace preguntas y requiere explicaciones simples.",
                        "Molesto": "El cliente expresa frustración o enojo. Responde de forma cortante y tiene baja tolerancia a errores."
                    }
                    
                    st.session_state.config_proveedor = proveedor
                    st.session_state.config_api_key = api_key_input
                    st.session_state.config_perfil = c_perfil
                    st.session_state.config_instruccion = instrucciones_tono.get(c_animo, "Neutral")
                    st.session_state.config_contexto = c_contexto
                    st.session_state.config_intencion = c_intencion
                    
                    st.session_state.mensajes = [{"role": "assistant", "content": "Hola, bienvenido a Soporte Técnico. ¿En qué puedo ayudarte hoy?"}]
                    st.session_state.caso_activo = True
                    st.session_state.simulacion_corriendo = False
                    st.session_state.pagina_actual = "chat"
                    st.rerun()

# --- PANTALLA 2: SIMULACIÓN ---
def mostrar_pantalla_chat():
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ Configuración"):
            st.session_state.pagina_actual = "configuracion"
            st.session_state.simulacion_corriendo = False
            st.rerun()
    with col_title:
        prov_actual = st.session_state.config_proveedor
        st.subheader(f"Simulación en Curso | {prov_actual}")

    api_key = st.session_state.get("config_api_key", "")
    proveedor = st.session_state.get("config_proveedor", "")
    
    if not api_key:
        st.error("⛔ Falta API Key.")
        return

# --- LLM ---
    llm = None
    try:
        if "Groq" in proveedor:
            if "ChatGroq" not in globals():
                 st.error("⚠️ Falta librería. Instala: pip install langchain-groq")
                 return
            os.environ["GROQ_API_KEY"] = api_key
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.9, max_retries=1)
            
        elif "Google" in proveedor:
            if "ChatGoogleGenerativeAI" not in globals():
                 st.error("⚠️ Falta librería. Instala: pip install langchain-google-genai")
                 return
            os.environ["GOOGLE_API_KEY"] = api_key
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.9)
            
    except Exception as e:
        st.error(f"Error conectando con {proveedor}: {e}")
        return

# --- PROMPTS ---
    prompt_cliente = PromptTemplate(
        input_variables=["perfil", "instruccion_actuacion", "contexto", "intencion", "mensaje_recibido","historial"],
        template="""
        Eres un cliente.
        PERFIL: {perfil}
        ACTITUD: {instruccion_actuacion}
        CONTEXTO: {contexto}
        OBJETIVO: {intencion}
        HISTORIAL: {historial}
        SOPORTE DICE: "{mensaje_recibido}"
        
        INSTRUCCIONES:
        - Respuesta CORTA (máx 30 palabras).
        - Si niegan tu petición 2 veces, acepta la alternativa.
        - Solo dices tu objetivo 1 vez
        - Si no tienes mas requerimientos y el soporte te pide que digas adios para cerrar la consulta debes decir adios en tu  mensaje
        
        TU RESPUESTA:
        """
    )
    cadena_cliente = prompt_cliente | llm

    prompt_soporte = PromptTemplate(
        input_variables=["mensaje_cliente", "knowledge", "historial"],
        template="""
        Eres agente de soporte "NexusNet".
        POLÍTICAS: {knowledge}
        HISTORIAL: {historial}
        CLIENTE DICE: "{mensaje_cliente}"
        
        INSTRUCCIONES:
        1. Responde según políticas. Máximo 40 palabras.
        2. Solo si el cliente se despide o si aclara que no tiene mas requerimientos, ES OBLIGATORIO escribir al final: "[CASO CERRADO]"
        """
    )
    cadena_soporte = prompt_soporte | llm

# --- BOTONES ---
    with st.container():
        col_st, col_ct = st.columns([2, 2])
        with col_st:
            if not st.session_state.caso_activo:
                st.success("✅ CASO CERRADO")
            else:
                st.info(f"Activo")
        with col_ct:
            if st.session_state.caso_activo:
                if not st.session_state.simulacion_corriendo:
                    if st.button("▶️ INICIAR", type="primary"):
                        if not st.session_state.mensajes:
                            st.session_state.mensajes = [{"role": "assistant", "content": "Hola."}]
                        st.session_state.simulacion_corriendo = True
                        st.rerun()
                else:
                    if st.button("⏹️ PAUSAR"):
                        st.session_state.simulacion_corriendo = False
                        st.rerun()
            else:
                if st.button("🔄 REINICIAR"):
                    st.session_state.mensajes = [{"role": "assistant", "content": "Hola."}]
                    st.session_state.caso_activo = True
                    st.rerun()

    st.divider()

#--- CHAT ---
    if not st.session_state.mensajes:
         st.session_state.mensajes = [{"role": "assistant", "content": "Hola, soporte técnico."}]

    for msg in st.session_state.mensajes:
        avatar = "🛠" if msg["role"] == "assistant" else "🧑"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    if st.session_state.caso_activo and st.session_state.simulacion_corriendo:
        
        ultimo_msg = st.session_state.mensajes[-1]
        historial_actual = obtener_historial_como_texto()

        try:
            if ultimo_msg["role"] == "assistant":
                with st.spinner(f'Cliente pensando...'):
                    time.sleep(3) 
                    res_cliente = cadena_cliente.invoke({
                        "perfil": st.session_state.config_perfil,
                        "instruccion_actuacion": st.session_state.config_instruccion,
                        "contexto": st.session_state.config_contexto,
                        "intencion": st.session_state.config_intencion,
                        "mensaje_recibido": ultimo_msg["content"],
                        "historial": historial_actual
                    })
                    txt_c = str(res_cliente.content)
                    if isinstance(res_cliente.content, list): txt_c = res_cliente.content[0].get("text", "")
                    
                    st.session_state.mensajes.append({"role": "user", "content": txt_c})
                    
                    if "ADIOS" in txt_c.upper() and len(txt_c.split()) < 5:
                        st.session_state.mensajes.append({"role": "system", "content": "SISTEMA: Cierre detectado."}) 
                    
                    st.rerun()

            elif ultimo_msg["role"] == "user":
                with st.spinner(f'Agente Nexus respondiendo...'):
                    time.sleep(4) 
                    texto_politicas = json.dumps(politicas_empresa, ensure_ascii=False)
                    res_soporte = cadena_soporte.invoke({
                        "mensaje_cliente": ultimo_msg["content"],
                        "knowledge": texto_politicas,
                        "historial": historial_actual
                    })
                    txt_s = str(res_soporte.content)
                    if isinstance(res_soporte.content, list): txt_s = res_soporte.content[0].get("text", "")
                    
                    if "[CASO CERRADO]" in txt_s.upper():
                        st.session_state.caso_activo = False
                        st.session_state.simulacion_corriendo = False
                    
                    msg_limpio = txt_s.replace("[CASO CERRADO]", "").replace("CASO CERRADO", "")
                    st.session_state.mensajes.append({"role": "assistant", "content": msg_limpio})
                    st.rerun()

        except Exception as e:
            st.error(f"⚠️ Error ({proveedor}): {e}")
            st.session_state.simulacion_corriendo = False


if st.session_state.pagina_actual == "configuracion":
    mostrar_pantalla_configuracion()
elif st.session_state.pagina_actual == "chat":
    mostrar_pantalla_chat()

#https://github.com/mariovicunaa/Semillero-ia-agente-simulador-Grupo-Nexus
