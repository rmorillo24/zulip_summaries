import weaviate

from llama_index import StorageContext, SimpleDirectoryReader, ServiceContext, VectorStoreIndex, Document, get_response_synthesizer
from llama_index.vector_stores import WeaviateVectorStore
from llama_index.embeddings import LangchainEmbedding, OllamaEmbedding
from llama_index.indices.document_summary import DocumentSummaryIndex
from llama_index.llms import Ollama
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.postprocessor import SimilarityPostprocessor
from llama_index.retrievers import VectorIndexRetriever
from llama_index.prompts import PromptTemplate


import box
import yaml
import warnings
import rag
import json
import logger as log

warnings.filterwarnings("ignore", category=DeprecationWarning)


SUMMARY_TEMPLATE = (
    "context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "There are different topics discussed in the information provided.\n"
    "For each topic create a markdown output with the following structure:\n"
    "#### Topic:\n"
    "__Keypoints__:\n"
    "__Decissions and actions__:\n"
    # "answer the question: {query_str}\n"
    # "Answer: "
)

class Rag:
    def __init__(self, config_path='./.venv/config.yml', model_name = "llama2"):
        
        with open(config_path, 'r', encoding='utf8') as ymlfile:
            self.cfg = box.Box(yaml.safe_load(ymlfile))
        
        self.client = weaviate.Client(self.cfg.WEAVIATE_URL)
        
        self.embeddings = OllamaEmbedding(model_name=self.cfg.LLM)
        
        self.llm = Ollama(
            model=self.cfg.LLM,
            base_url=self.cfg.OLLAMA_BASE_URL,
            temperature=self.cfg.TEMPERATURE
        )        
        self.service_context = ServiceContext.from_defaults(
            embed_model=self.embeddings,
            llm=self.llm
        )        
        self.vector_store = WeaviateVectorStore(
            weaviate_client=self.client,
            index_name=self.cfg.INDEX_NAME
        )
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        summary_prompt_template = PromptTemplate(SUMMARY_TEMPLATE)
        self.response_synthesizer = get_response_synthesizer(
            response_mode="tree_summarize",
            use_async=False,
            service_context=self.service_context,
            summary_template=summary_prompt_template
        )        
        self.index_main = VectorStoreIndex.from_vector_store(
            vector_store = self.vector_store,
            service_context = self.service_context
        )
        self.retriever = VectorIndexRetriever(
            index=self.index_main,
            similarity_top_k=10,
        )        
        self.zulip_query_engine = self.index_main.as_query_engine()
        # self.zulip_query_engine = RetrieverQueryEngine(
        #     retriever=self.retriever,
        #     response_synthesizer=self.response_synthesizer,
        #     node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)]
        # )        
        self.index_doc = None
        self.documents = []
        self.doc_query_engine = None


    def set_model(self, model_name):
        self.cfg.LLM = model_name
        self.llm = Ollama(
            model=self.cfg.LLM,
            base_url=self.cfg.OLLAMA_BASE_URL,
            temperature=self.cfg.TEMPERATURE)
        self.service_context = ServiceContext.from_defaults(
            embed_model=self.embeddings,
            llm=self.llm)
        self.response_synthesizer = get_response_synthesizer(
            response_mode="tree_summarize",
            use_async=False,
            service_context=self.service_context)
        
        self.index_main = VectorStoreIndex.from_vector_store(
            vector_store = self.vector_store,
            service_context = self.service_context)
        

    def get_summary(self, title): 
        # to-do: what happens if title doesn't exists: need to ingest    
        doc_summary_index = DocumentSummaryIndex.from_documents(
            self.documents,
            service_context=self.service_context,
            response_synthesizer=self.response_synthesizer,
            show_progress=True)
        print("Building summary index...")
        doc_summary = doc_summary_index.get_document_summary(doc_id = title)
        return doc_summary


    def ingest_text(self, text, title):
        document = Document(text=text, doc_id = title, metadata={"stream": title})
        self.documents = [document]
        print("Adding doc to index main index...")
        self.index_main.insert(document, show_progress=True)
   
        # self.zulip_query_engine = self.index_main.as_query_engine()
                
        print("Building doc index...")
        self.index_doc = VectorStoreIndex.from_documents(self.documents,
                                                         service_context=self.service_context,
                                                         llm = self.llm,
                                                         show_progress=True)
        self.doc_query_engine = self.index_doc.as_query_engine()


    def ask_doc(self, question):
        print("Asking doc...")
        return self.doc_query_engine.query(question)
    

    def ask_zulip(self, question):
        print("Asking zulip...")
        return self.zulip_query_engine.query(question)
    

if __name__ == "__main__":
    logger = log.init_logger(__name__)
    logger.debug("start")

    rag = Rag()

    # title = "MYTESTTITLE"
    # with open('test.txt', 'r') as file:
    #     text = " ".join(line.rstrip() for line in file)

    # summary = rag.ingest_text(text, title)

    # query
    while True:
        try:
            question = input("\n\n> ")

            print("ZULIP")
            response = rag.ask_zulip(question)
            print(response)

            # print("DOC")
            # response  = rag.ask_doc(question)
            # print(response)

        except EOFError:
            break