import streamlit as st
from llm_chains import load_normal_chain
from streamlit_mic_recorder import mic_recorder
from langchain.memory import StreamlitChatMessageHistory
from image_handler import handle_images
from utils import save_chat_history_json, load_chat_history_json, get_timestamp
import yaml
import os
from audio_handler import transcribe_audio
with open("config.yml","r") as f:
    config = yaml.safe_load(f)

def load_chain(chat_history):
    return load_normal_chain(chat_history)

def clear_input_field():
    st.session_state.user_question = st.session_state.user_input
    st.session_state.user_input=""
    

def set_send_input():
    st.session_state.send_input = True
    clear_input_field()
    
def save_chat_history():
    if st.session_state.history != []:
        if st.session_state.session_key == "new_session":
            st.session_state.new_session_key = get_timestamp().replace(":", "-") + ".json"
            file_path = os.path.join(config["chat_history_path"], st.session_state.new_session_key)
            save_chat_history_json(st.session_state.history, file_path)
        else:
            file_path = os.path.join(config["chat_history_path"], st.session_state.session_key)
            save_chat_history_json(st.session_state.history, file_path)
            
      
def main():
    st.title("YAAR-GPT")
    
    chat_container  = st.container()
    st.sidebar.title("chat sessions")
    chat_sessions = ["new_session"] + os.listdir(config["chat_history_path"])
    
    if "send_input" not in st.session_state:
        st.session_state.session_key = "new_session"
        st.session_state.send_input = False
        st.session_state.user_question= ""
        st.session_state.new_session_key= None
        st.session_state.session_index_tracker = "new_session"
        
    if st.session_state.session_key == "new_session" and st.session_state.new_session_key != None:
        st.session_state.session_index_tracker = st.session_state.new_session_key
        st.session_state.new_session_key = None
    
    index = chat_sessions.index(st.session_state.session_index_tracker) 
        
    st.sidebar.selectbox("Select a chat session", chat_sessions, key = "session_key", index=index)
    
    if st.session_state.session_key != "new_session":
        st.session_state.history = load_chat_history_json(config["chat_history_path"]+ st.session_state.session_key)
    else:
        st.session_state.history = []
    
    chat_history = StreamlitChatMessageHistory(key ="history")
    llm_chain = load_chain(chat_history)
    
    
    user_input = st.text_input("type ur text here", key = "user_input", on_change=set_send_input)
    voice_recording_column, send_button_column = st.columns(2)
    with voice_recording_column:
        voice_recording=mic_recorder(start_prompt="Start recording", stop_prompt="Stop recording", just_once=True)
    with send_button_column:
        send_button = st.button("send", key = "send_button", on_click = clear_input_field)
    
    uploaded_image = st.sidebar.file_uploader("Upload Your Image", accept_multiple_files=True, key = "image_upload", type=["jpg", "jpeg", "png"])
   
    
   
   
    if voice_recording:
        transcribed_audio = transcribe_audio(voice_recording["bytes"])
        llm_chain.run(transcribed_audio)
    
    if send_button or st.session_state.send_input:
        if uploaded_image:  
           with st.spinner("Buckle up this might take few sec..."):
               user_message = "Explain this image to a 8 year old please"
               if st.session_state.user_question!= "":
                   user_message = st.session_state.user_question
                   st.session_state.user_question = ""
               image_bytes_list = [image.read() for image in uploaded_image]
               llm_answer = handle_images(image_bytes_list, user_message)
               chat_history.add_user_message(user_message)
               chat_history.add_ai_message(llm_answer[0])
            
        
        if st.session_state.user_question != "":
            
            st.chat_message("user").write(st.session_state.user_question)
            llm_response = llm_chain.run(st.session_state.user_question)
            st.session_state.user_question = ""
    if chat_history.messages != []:
        with chat_container:
            st.write("Chat History:")
            for message in chat_history.messages:
                st.chat_message(message.type).write(message.content)
    save_chat_history()
  
if __name__ == "__main__":
    main()