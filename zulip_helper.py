import zulip
import logging
from typing import Any, Dict, List
import time
import os

class ZulipHandler():
    def __init__(self, config_file):
        self.zulip_client = zulip.Client(config_file = config_file)
        self.logger = logging.getLogger(__name__)

        # Rate limit parameters
        self.requests_limit = 200  # Example: 100 requests
        self.time_window = 60  # Example: 60 seconds
        # Tracking variables
        self.request_count = 0
        self.start_time = time.time()


    def get_subscriptions(self):
        # Replace this with the actual API call using requests library
        self.check_rate_limit()
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
            self.check_rate_limit()
            result = self.zulip_client.get_messages(request)
            try:
                found_newest = result["found_newest"]
                if result["messages"]:
                    for m in result['messages']:
                        all_messages.extend("[START] [" + m['sender_full_name'] + "] " + m['content'] + " [END]\n")
                    # Setting the anchor to the next immediate message after the last fetched message.
                    request["anchor"] = result["messages"][-1]["id"] + 1

            except KeyError:
                # Might occur when the request is not returned with a success status
                # self.logger(logging.DEBUG, "Error obtaining messages from topic")
                return ""
            except :
                exit
        text = ""
        for m in all_messages:
            text += m
        
        return text

    def search_topic_in_stream(self, stream_id, topic_keyword):
        result = []
        try:
            self.check_rate_limit()
            topics = self.zulip_client.get_stream_topics(stream_id)
            for topic in topics['topics']:
                if topic_keyword.lower() in str(topic).lower():
                    result.append(topic['name'])
        except:
            logging.error("Error ontaining stream topics: " + str(stream_id))
        return result

    def check_rate_limit(self):
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        # Reset counter and timer if the time window has passed
        if elapsed_time > self.time_window:
            self.request_count = 0
            self.start_time = time.time()

        # Check if approaching the limit
        if self.request_count >= (self.requests_limit - 10):  # Example: start slowing down 10 requests before hitting the limit
            # Calculate sleep time: remaining time in the window plus a buffer (e.g., 1 second)
            sleep_time = (self.time_window - elapsed_time) + 1
            logger.debug(f"-----> Approaching rate limit, sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
            # Reset after sleeping
            self.request_count = 0
            self.start_time = time.time()
        else:
            self.request_count += 1    


def make_folder(path):
    """Create a directory if it does not exist."""
    
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.exists(path):
            logging.error(f"The folder {path} could not be created.")
        else:
            logging.error(f"The folder {path} already exists.")


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
        logger.log(logging.DEBUG, "[STREAM] "+ stream)
        if not os.path.exists("data/" + stream):
            os.makedirs("./data/"+stream)
        topics = zc.search_topic_in_stream(s["stream_id"], "")
        for topic in topics:
            logger.log(logging.DEBUG, "[STREAM] "+ stream + "[TOPIC] " + topic)
            filename = "./data/" + stream + "/" + topic.replace('/', '___')
            if not os.path.exists(filename):
                messages = zc.get_topic_messages(stream, topic)
                write_to_file = True
                if write_to_file:
                    try:
                        if not os.path.exists(filename):
                            # logger.debug("getting messages and writting file " + filename)
                            with open(filename, 'w') as file:
                                file.write(messages)
                        else:
                            logger.debug("already exists")
                    except:
                        logger.error("ERROR while trying to write " + filename)
                        logger.error(".....Skipping....")
            else:
                logger.debug("topic already in file: " + filename)
           