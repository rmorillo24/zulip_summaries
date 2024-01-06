import streamlit as st
from json_converter.json_mapper import JsonMapper
from random import randrange

st.set_page_config(page_title="Zulip GPT", layout="wide")
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


global threads
threads = {
    "msg": "",
    "result": "success",
    "streams": [
        {
            "can_remove_subscribers_group": 10,
            "date_created": 1691057093,
            "description": "balena.io/os",
            "first_message_id": 18,
            "history_public_to_subscribers": False,
            "invite_only": True,
            "is_announcement_only": False,
            "is_default": False,
            "is_web_public": False,
            "message_retention_days": None,
            "name": "management",
            "rendered_description": "<p>A private stream</p>",
            "stream_id": 2,
            "stream_post_policy": 1,
            "stream_weekly_traffic": None
        },
        {
            "can_remove_subscribers_group": 9,
            "date_created": 1691057093,
            "description": "aspect/customer_success",
            "first_message_id": 21,
            "history_public_to_subscribers": True,
            "invite_only": False,
            "is_announcement_only": False,
            "is_default": True,
            "is_web_public": False,
            "message_retention_days": None,
            "name": "welcome",
            "rendered_description": "<p>A default public stream</p>",
            "stream_id": 1,
            "stream_post_policy": 1,
            "stream_weekly_traffic": None
        }
    ]
}

treeData = []
selected_stream = 1
for stream in threads['streams']:
    children = []
    if selected_stream == stream['stream_id']:
        # topics = zulipClient.getTopicsInStreams
        topics = { #get zulip api
                "msg": "",
                "result": "success",
                "topics": [
                    {
                        "max_id": 26,
                        "name": "Denmark3"
                    },
                    {
                        "max_id": 23,
                        "name": "Denmark1"
                    },
                    {
                        "max_id": 6,
                        "name": "Denmark2"
                    }
                ]
            }
        for topic in topics['topics']:
            children.append(
                {"label": topic["name"],
                 "value": topic["max_id"]}
            )
    treeData.append(
        {
            "label": stream['description'],
            "value": stream['stream_id'],
            "children": children
        }
    )

def search_topic_in_stream(stream, topic_keyword):
    result = []
    # topics = zulipClient.getTopicsInStreams
    if stream == "balena.io/os":
        topics = { #get zulip api
                "msg": "",
                "result": "success",
                "topics": [
                    {
                        "max_id": 26,
                        "name": "Denmark3"
                    },
                    {
                        "max_id": 23,
                        "name": "Denmark1"
                    },
                    {
                        "max_id": 6,
                        "name": "Denmark2"
                    }
                ]
            }
    else:
        topics = {"topics":[]}
    for topic in topics['topics']:
        if str(topic).find(topic_keyword) != -1:
            result.append(topic['name'])
    return result

def stream_option_changed():
    st.session_state["topic_keyword"] = "" # delete the searh box
    st.session_state["topic_summary"] = "" # delete the summary
    st.session_state.messages = []


def topic_option_changed():
    st.session_state["topic_summary"] = "" #delete the summary
    st.session_state.messages = []


st.session_state["topic_summary"] = ""

stream_options = []
for stream in threads['streams']:
    stream_options.append(stream["description"])


with st.sidebar:
    selected_topic = ""
    selected_stream = ""
    selected_stream = st.selectbox("Select stream", stream_options, on_change=stream_option_changed)
    if selected_stream:
        topic_keyword = st.text_input("Search topic", key="topic_keyword")
        if topic_keyword:
            topic_candidates = search_topic_in_stream(selected_stream, topic_keyword)
            if topic_candidates != []:
                selected_topic = st.selectbox(label = "Select topic", options=topic_candidates, on_change=topic_option_changed)
            else:
                st.caption("No topics found")

if (selected_topic != "") & (selected_stream != ""):
    st.subheader(selected_stream + " > " + selected_topic)
    
    tab1, tab2 = st.tabs(("Topic Summary", "Chat with the topic"))
    
    #summary
    with tab1:
        # Summary has not been generated yet
        if (st.session_state["topic_summary"] == ""):
            # generate summary
            summary = "This is a summary" + str(randrange(1,1000))
        st.session_state["topic_summary"] = summary
        st.write(summary)
    
    # Chat
    with tab2:
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
        response = f"Echo: {prompt}"
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
