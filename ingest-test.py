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
import rag


warnings.filterwarnings("ignore", category=DeprecationWarning)


def load_documents(docs_path):
    # documents = SimpleDirectoryReader(input_dir=docs_path).load_data()
    documents = SimpleDirectoryReader(input_files=['data/intentionalworkframework.txt']).load_data()
    print(f"Loaded {len(documents)} documents")
    print(f"First document: {documents[0]}")
    return documents

def load_embedding_model(model_name):
    # embeddings = LangchainEmbedding(
    #     HuggingFaceEmbeddings(model_name=model_name)
    # )
    print("Model name: ", model_name)
    embeddings = OllamaEmbedding(model_name=model_name)
    return embeddings


def build_summary(documents, embed_model, llm):
    print("Building summary...")
    service_context = ServiceContext.from_defaults(embed_model=embed_model, llm=llm)

    response_synthesizer = get_response_synthesizer(
        response_mode="tree_summarize",
        use_async=False,
        service_context=service_context
    )
    doc_summary_index = DocumentSummaryIndex.from_documents(
        documents,
        service_context=service_context,
        response_synthesizer=response_synthesizer,
        show_progress=True,
    )
    return doc_summary_index


def build_index(weaviate_client, embed_model, documents, index_name, llm):

    service_context = ServiceContext.from_defaults(embed_model=embed_model, llm=llm)
    vector_store = WeaviateVectorStore(weaviate_client=weaviate_client, index_name=index_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
 
    index = VectorStoreIndex.from_documents(
        documents,
        service_context=service_context,
        storage_context=storage_context,
    )


    return index


def ingest_and_summarize(text, title):
    # Import config vars
    with open('./.venv/config.yml', 'r', encoding='utf8') as ymlfile:
        cfg = box.Box(yaml.safe_load(ymlfile))

    print("Connecting to Weaviate")
    client = weaviate.Client(cfg.WEAVIATE_URL)

    print("Loading documents...")
    documents = [Document(text = text, doc_id = title)]


    print("Loading embedding model...")
    embeddings = load_embedding_model(model_name=cfg.EMBEDDINGS)

    print("Loading Ollama...")
    llm = Ollama(model=cfg.LLM, base_url=cfg.OLLAMA_BASE_URL, temperature=cfg.TEMPERATURE)

    print("Building index...")
    index = build_index(client, embeddings, documents, cfg.INDEX_NAME, llm = llm)
    summaries = build_summary(documents, embeddings, llm)
    return summaries.get_document_summary(title)

if __name__ == "__main__":
    # Import config vars
    with open('./.venv/config.yml', 'r', encoding='utf8') as ymlfile:
        cfg = box.Box(yaml.safe_load(ymlfile))
    title = "MYTESTTITLE"
    with open('test.txt','r') as file:
        text = " ".join(line.rstrip() for line in file)
    summary = ingest_and_summarize(text, title)
    print(summary)

    # chatting with the document
    documents = [Document(text=text, doc_id = title)]
    embeddings = load_embedding_model(model_name=cfg.EMBEDDINGS)
    llm = Ollama(model=cfg.LLM, base_url=cfg.OLLAMA_BASE_URL, temperature=cfg.TEMPERATURE)
    service_context = ServiceContext.from_defaults(embed_model=embeddings, llm=llm)
    
    # build index
    index = VectorStoreIndex.from_documents(documents, service_context=service_context, llm = llm)
    
    # configure retriever
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=10,
    )

    # configure response synthesizer
    response_synthesizer = get_response_synthesizer(service_context=service_context)

    # assemble query engine
    query_engine = index.as_query_engine()

    # query
    while True:
        try:
            question = input("\n\n> ")
            response = query_engine.query(question)
            print(response)
        except EOFError:
            break