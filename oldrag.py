import weaviate
import timeit
import argparse
import json
import time
import box
import yaml
import warnings
from llama_index.core import VectorStoreIndex, ServiceContext, get_response_synthesizer
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from llama_index.core import DocumentSummaryIndex


def get_rag_response(query, chain, debug=False):
    result = chain.query(query)
    if debug:
        print(result)
    try:
        # Convert and pretty print
        data = json.loads(str(result))
        data = json.dumps(data, indent=4)
    except (json.decoder.JSONDecodeError, TypeError):
        if debug:
            print("The response is not in JSON format.")
        data = result
        
    return data


def load_embedding_model(model_name):
    embeddings = OllamaEmbedding(model_name=model_name)
    return embeddings



def build_index(chunk_size, llm, embed_model, weaviate_client, index_name):
    service_context = ServiceContext.from_defaults(
        chunk_size=chunk_size,
        llm=llm,
        embed_model=embed_model
    )

    vector_store = WeaviateVectorStore(weaviate_client=weaviate_client, index_name=index_name)

    index = VectorStoreIndex.from_vector_store(
        vector_store, service_context=service_context
    )

    return index


def build_rag_pipeline(debug=False):
    # Import config vars
    with open('./.venv/config.yml', 'r', encoding='utf8') as ymlfile:
        cfg = box.Box(yaml.safe_load(ymlfile))

    print("Connecting to Weaviate")
    client = weaviate.Client(cfg.WEAVIATE_URL)

    print("Loading Ollama...")
    llm = Ollama(model=cfg.LLM, base_url=cfg.OLLAMA_BASE_URL, temperature=cfg.TEMPERATURE)

    print("Loading embedding model...")
    embeddings = load_embedding_model(model_name=cfg.EMBEDDINGS)

    print("Building index...")
    index = build_index(cfg.CHUNK_SIZE, llm, embeddings, client, cfg.INDEX_NAME)

    print("Constructing query engine...")

    query_engine = index.as_query_engine(
        streaming=False
    )

    return query_engine


def chat_with_model(user_question):
    parser = argparse.ArgumentParser()
    # parser.add_argument('input',
    #                     type=str,
    #                     help='Enter the query to pass into the LLM')
    parser.add_argument('--debug',
                        action='store_true',
                        default=False,
                        help='Enable debug mode')
    args = parser.parse_args()
    rag_chain = build_rag_pipeline(args.debug)

    try:
        if user_question != "":
            start = timeit.default_timer()
            answer = get_rag_response(user_question, rag_chain, args.debug)
            end = timeit.default_timer()
            print(f'\n{end - start}:\n{answer}')
        else:
            print("no question")
    except EOFError:
        pass

def get_topic_summary(topic_title):
    # Import config vars
    with open('./.venv/config.yml', 'r', encoding='utf8') as ymlfile:
        cfg = box.Box(yaml.safe_load(ymlfile))

    print("Connecting to Weaviate")
    client = weaviate.Client(cfg.WEAVIATE_URL)

    print("Loading Ollama...")
    llm = Ollama(model=cfg.LLM, base_url=cfg.OLLAMA_BASE_URL, temperature=cfg.TEMPERATURE)
    embeddings = load_embedding_model(model_name=cfg.EMBEDDINGS)

    service_context = ServiceContext.from_defaults(llm=llm, chunk_size=1024, embed_model=embeddings)
    # default mode of building the index
    response_synthesizer = get_response_synthesizer(
        response_mode="tree_summarize",
        use_async=False,
        service_context=service_context
    )
    doc_summary_index = DocumentSummaryIndex.from_documents(
        [[topic_title]],
        service_context=service_context,
        response_synthesizer=response_synthesizer,
        show_progress=True,
    )
    