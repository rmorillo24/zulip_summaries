import urllib.parse

def extract_fields(url):
    # Parse the URL
    parsed_url = urllib.parse.urlparse(url)

    # Extract the fragment and split it to get the 'stream' and 'topicname' parts
    fragment_parts = parsed_url.fragment.split('/')

    # Assuming the structure is consistent with the provided URL
    if len(fragment_parts) >= 3:
        # Extract 'stream' and 'topicname' values
        # For 'stream', we split by '-' and take everything after the first element
        stream_parts = fragment_parts[2].split('-')[1:]
        stream = "-".join(stream_parts)
        # Replace '.2F' with '/' to handle special characters
        stream = stream.replace(".2F", "/")

        # For 'topicname', replace '.20' with space to handle special characters
        topicname = fragment_parts[-1].replace(".20", " ")
    else:
        stream = ""
        topicname = ""

    return stream, topicname

# Test the function with the provided URL
# url = "https://balena.zulipchat.com/#narrow/stream/345889-balena-io.2Fos/topic/balenaOS.20to.20balenaOS.20migrator"
# stream, topicname = extract_fields(url)

# print("Stream:", stream)
# print("Topicname:", topicname)
