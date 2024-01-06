import zulip

# Pass the path to your zuliprc file here.
client = zulip.Client(config_file="./.venv/.zuliprc")

result = client.get_stream_topics(332163)
for r in result['topics']:
  print(r)
	
