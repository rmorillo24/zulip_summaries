import streamlit as st
import requests
import timeit
from extract_fields import extract_fields
from get_history import get_topic_messages
import zulip
import sys

BASE_URL='http://localhost:11434/api/'
MODEL='llama2'
INSTRUCTIONS='Strictly write bullet points. Avoid an introduction. Write in third person. Generate output in markdown format. The text is the following: '
global messages
global zulip_client

def ask_model(question, model):
    #prompt the given model
    command='generate'
    data = {
        "model": model,
        "prompt": question,
        "stream": False,
            "options": {
                "temperature": 1
            }
    }
    response = requests.post(BASE_URL + command, json = data)
    if response.status_code == 200:
        r = response.json()
        return r['response']
    else:
        return ("Something went wrong asking the model: ", response.text)

def url_change():
    url = st.session_state.url
    if url:
        stream, topic = extract_fields(url)
        st.session_state.stream = stream
        st.session_state.topic = topic
        st.session_state.messages = get_topic_messages(st.session_state.zulip_client, stream, topic)
        st.session_state.new_topic = True
        st.session_state.summary= ""


# Initialize ST session state
if "zulip_client" not in st.session_state:
    # Accessing the zulip_config_file attribute
    zulip_client = zulip.Client(config_file = "./.venv/.zuliprc")
    st.session_state.zulip_client = zulip_client
if "new_topic" not in st.session_state:
    st.session_state.new_topic = True
if "messages" not in st.session_state:
    st.session_state.messages = ""

#start
st.title('Zulip topic summarizer')
topic_url = st.text_input('Enter Topic URL to summarize', on_change=url_change, key="url")
if (topic_url != None) & (topic_url != ""):
    if st.session_state.new_topic:
        prompt = "Find in the text the information required to generate a summary. " + INSTRUCTIONS
        prompt = prompt + ': ' + st.session_state.messages
        with st.spinner('Wait for it...'):
            st.session_state.summary = ask_model(prompt, MODEL)

    if st.session_state.summary != "":
        st.caption("Summary of " + st.session_state.stream + " > " + st.session_state.topic)
        st.markdown(st.session_state.summary)

    question = st.text_input("Any questions?")
    if question:
        prompt = "Find in the text the information required by this question '" + question + "'. " + INSTRUCTIONS + " " + st.session_state.messages
        with st.spinner('Wait for it...'):
            r = ask_model(prompt, MODEL)
        st.markdown(r)
    st.session_state.new_topic = False
