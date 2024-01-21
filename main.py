import streamlit as st
# from json_converter.json_mapper import JsonMapper
from random import randrange
import requests
from typing import Any, Dict, List
import ingest
import rag
from zulip_helper import ZulipHandler


def stream_option_changed():
    # st.session_state["topic_keyword"] = "" # delete the searh box
    st.session_state["topic_summary"] = "" # delete the summary
    st.session_state.messages = []

def chat_with_changed():
    # st.session_state["topic_keyword"] = "" # delete the searh box
    st.session_state["topic_summary"] = "" # delete the summary
    st.session_state.messages = []


def topic_option_changed():
    st.session_state["topic_summary"] = "" #delete the summary
    st.session_state.messages = []

def model_changed():
    st.session_state["topic_summary"] = "" # delete the summary
    st.session_state.messages = []
    st.session_state.rag.set_model(st.session_state.model)


def get_stream_name_by_id(stream_id):
    name = ""
    for stream in st.session_state.subscriptions:
        if stream_id == stream["stream_id"]:
            name = stream["name"]
            return name
    return name


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

def get_models():
    #ping to get models
    command = 'tags'
    response = requests.get(BASE_URL + command)
    if response.status_code == 200:
        models_json = response.json()['models']
        return [model["name"] for model in models_json]
    else:
        print("Error retreiving models: ", response.status_code)
        return []


BASE_URL='http://localhost:11434/api/'
# MODEL='llama2'
# # INSTRUCTIONS='Strictly write bullet points. Avoid an introduction. Write in third person. Generate output in markdown format. The text is the following: '
# INSTRUCTIONS='Strictly write bullet points. Avoid an introduction. Write in third person. Generate output in markdown format. The text is the following: '


st.set_page_config(page_title="Zulip GPT", layout="wide")
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
# Initialize summary
    if "topic_summary" not in st.session_state:
        st.session_state["topic_summary"] = ""

# global zulip_client
if "zulip_client" not in st.session_state:
    # Accessing the zulip_config_file attribute
    zulip_client = ZulipHandler(config_file = "./.venv/.zuliprc")
    st.session_state.zulip_client = zulip_client

if "subscriptions" not in st.session_state:
    result = st.session_state.zulip_client.get_subscriptions()
    if result["result"] != "success":
        st.error("Error getting Zulip subscriptions")
        st.session_state.subscriptions={}
    else:
        st.session_state.subscriptions = result["subscriptions"]

if "rag" not in st.session_state:
    st.session_state.rag = ingest.Rag()

if "model" not in st.session_state:
    st.session_state.model = ""

stream_options = []
for stream in st.session_state.subscriptions:
    stream_options.append(stream["stream_id"])


with st.sidebar:
    # st.session_state.model = st.selectbox("Select LLM model", options = get_models(), on_change = model_changed)
    chat_with_topic = st.toggle("Ask questions ONLY to a selected topic instead of all Zulip",
                                value=True,
                                on_change = chat_with_changed)
    if chat_with_topic:
        selected_topic = None
        selected_stream = None
        selected_stream = st.selectbox("Select stream", stream_options, format_func=get_stream_name_by_id, on_change=stream_option_changed, index=None)
        if selected_stream:
            topic_candidates = st.session_state.zulip_client.search_topic_in_stream(selected_stream, "")
            selected_topic = st.selectbox(label = "Select topic", options=topic_candidates, on_change=topic_option_changed, index=None)


if chat_with_topic:
    if (selected_topic != None) & (selected_stream != None):
        title = get_stream_name_by_id(selected_stream) + " > " + selected_topic
        st.subheader(title)
        
        # summary
        # Summary has not been generated yet
        if (st.session_state["topic_summary"] == ""):
            with st.spinner("Retreiving messages from topic..."):
                messages = st.session_state.zulip_client.get_topic_messages(get_stream_name_by_id(selected_stream), selected_topic)
            with st.spinner("updating LLM DB..."):
                st.session_state.rag.ingest_text(messages, title)
                st.session_state.topic_summary = st.session_state.rag.get_summary(title)
        st.caption("Summary")
        st.markdown(st.session_state.topic_summary)
        
        # Chat
        
        st.caption("Chat with the topic")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        # React to user input
        if prompt := st.chat_input("Any questions?"):
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Looking for an answer..."):
                response = st.session_state.rag.ask_doc(prompt)
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.caption("Chat with Zulip")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    # React to user input
    if prompt := st.chat_input("Any questions?"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Looking for an answer..."):
            response = st.session_state.rag.ask_zulip(prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})