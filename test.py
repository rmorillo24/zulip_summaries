import weaviate

from llama_index import StorageContext, SimpleDirectoryReader, ServiceContext, VectorStoreIndex, Document, get_response_synthesizer
from llama_index.vector_stores import WeaviateVectorStore
from llama_index.embeddings import LangchainEmbedding, OllamaEmbedding
from llama_index.indices.document_summary import DocumentSummaryIndex
from llama_index.llms import Ollama
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.postprocessor import SimilarityPostprocessor
from llama_index.retrievers import VectorIndexRetriever


import box
import yaml
import warnings


def load_documents():
    documents = SimpleDirectoryReader("./data", required_exts=[".txt"],filename_as_id=True).load_data()
    print(f"Loaded {len(documents)} documents")
    print(f"First document: {documents[0]}")
    return documents

with open(".venv/config.yml", 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))

client = weaviate.Client(cfg.WEAVIATE_URL)

embeddings = OllamaEmbedding(model_name=cfg.LLM)

llm = Ollama(
    model=cfg.LLM,
    base_url=cfg.OLLAMA_BASE_URL,
    temperature=cfg.TEMPERATURE
)        
service_context = ServiceContext.from_defaults(
    embed_model=embeddings,
    llm=llm
)        
vector_store = WeaviateVectorStore(
    weaviate_client=client,
    index_name=cfg.INDEX_NAME
)
storage_context = StorageContext.from_defaults(
    vector_store=vector_store
)        
response_synthesizer = get_response_synthesizer(
    response_mode="tree_summarize",
    use_async=False,
    service_context=service_context
)        
index_main = VectorStoreIndex.from_vector_store(
    vector_store = vector_store,
    service_context = service_context
)
# documents = load_documents()
# index_main =  VectorStoreIndex.from_documents(
#         documents,
#         service_context=service_context,
#         storage_context=storage_context,show_progress=True
# )
retriever = VectorIndexRetriever(
    index=index_main,
    similarity_top_k=10,
)        
zulip_query_engine = index_main.as_query_engine()
# zulip_query_engine = RetrieverQueryEngine(
#     retriever=retriever,
#     response_synthesizer=response_synthesizer,
#     node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)]
# )

retreiver = index_main.as_retriever()


while True:
    try:
        question = input(">")
        print("RETREIVER")
        nodes = retreiver.retrieve(question)
        # response = zulip_query_engine.aquery(question)
        # nodes = zulip_query_engine.retrieve(question)
        # engine = index_main.as_query_engine()
        # response = engine.query(question)
        # print(response)
        # print("----")
        for n in nodes:
            print(n.node_id, n.score, n.metadata)
    except EOFError:
        break