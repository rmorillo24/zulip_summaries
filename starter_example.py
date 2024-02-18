import os.path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama


# llm = Ollama(
#     model="mistral",
#     base_url='http://127.0.0.1:11434',
#     temperature=0
# )      
# check if storage already exists
PERSIST_DIR = "./data/storage"
if not os.path.exists(PERSIST_DIR):
    # load the documents and create the index
    documents = SimpleDirectoryReader("./data/SAMPLE").load_data()
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

# Either way we can now query the index
query_engine = index.as_query_engine()
while True:
    try:
        question = input("\n\n> ")
        response = query_engine.query(question)
        print(response)
    except EOFError:
        break


"""
> describe the workarounds or solutions mentioned around beaglebone and the openvpn
One workaround mentioned around BeagleBone and OpenVPN is to consider the startup ordering of OpenVPN and `balena-proxy-config`. It was discussed whether OpenVPN should depend on `balena-proxy-config` for startup ordering to ensure that the VPN connection is established over the proxy in a restrictive network. Additionally, there was a suggestion to have `balena-proxy-config` restart any networking daemon after applying the configuration to ensure that all network daemons are proxied and to maintain VPN access for debugging if the proxy settings don't work. The discussion also touched upon the sequence of services startup and the potential race condition caused by the processing power of the BeagleBone, highlighting the need for careful consideration of the startup sequence to address connectivity issues in restrictive network environments.

 """