import zulip
import logging
from typing import Any, Dict, List
import time
import os

class ZulipHandler():
    def __init__(self, config_file):
        self.zulip_client = zulip.Client(config_file = config_file)
        self.logger = logging.getLogger(__name__)


    def get_subscriptions(self):
        # Replace this with the actual API call using requests library
        response = self.zulip_client.get_subscriptions()
        return response

    def get_topic_messages(self, stream, topic):
        narrow = [{"operator": "stream", "operand": stream}]
        narrow.append({"operator": "topic", "operand": topic})

        request = {
            # Initially we have the anchor as 0, so that it starts fetching
            # from the oldest message in the narrow
            "anchor": 0,
            "num_before": 0,
            "num_after": 1000,
            "narrow": narrow,
            "client_gravatar": False,
            "apply_markdown": False,
        }

        all_messages: List[Dict[str, Any]] = []
        found_newest = False

        while not found_newest:
            result = self.zulip_client.get_messages(request)
            try:
                found_newest = result["found_newest"]
                if result["messages"]:
                    # Setting the anchor to the next immediate message after the last fetched message.
                    request["anchor"] = result["messages"][-1]["id"] + 1

                    all_messages.extend(result["messages"])
            except KeyError:
                # Might occur when the request is not returned with a success status
                # self.logger(logging.DEBUG, "Error obtaining messages from topic")
                return ""
        text = ""
        for m in all_messages:
            text += " " + m['content']
        
        return text

    def search_topic_in_stream(self, stream_id, topic_keyword):
        result = []
        topics = self.zulip_client.get_stream_topics(stream_id)
        for topic in topics['topics']:
            if topic_keyword.lower() in str(topic).lower():
                result.append(topic['name'])
        return result
    
def make_folder(path):
    """Create a directory if it does not exist."""
    
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.exists(path):
            print(f"The folder {path} could not be created.")
        else:
            print(f"The folder {path} already exists.")


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG) 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.debug("Starting...")

    zc = ZulipHandler("./.venv/.zuliprc")
    subscriptions = zc.get_subscriptions()["subscriptions"]
    for s in subscriptions:
        stream = s["name"].replace('/', '___')
        logger.log(logging.DEBUG, stream)
        if not os.path.exists("data/" + stream):
            os.makedirs("./data/"+stream)
        topics = zc.search_topic_in_stream(s["stream_id"], "")
        for topic in topics:
            logger.log(logging.DEBUG, topic)
            filename = "./data/" + stream + "/" + topic.replace('/', '___')
            if not os.path.exists(filename):
                logger.debug("getting messages and writting file " + filename)
                messages = zc.get_topic_messages(stream, topic)
                with open(filename, 'w') as file:
                    file.write(messages)
            else:
                logger.debug("already exists")
