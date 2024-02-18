import weaviate

from llama_index.core import StorageContext, ServiceContext, VectorStoreIndex, Document, get_response_synthesizer, Settings
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core import DocumentSummaryIndex
from llama_index.llms.ollama import Ollama
from llama_index.llms.langchain import LangChainLLM
from langchain.embeddings import HuggingFaceEmbeddings
from llama_index.embeddings.langchain import LangchainEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core import PromptTemplate
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.extractors import ( TitleExtractor, QuestionsAnsweredExtractor)
import box
import yaml
import warnings
import rag
import json
import logging
import os
import time
import argparse
import sys

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

ZULIP_QUERY_TEMPLATE=(
    "context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    # "There are different topics discussed in the information provided.\n"
    "Use only the knowledge included in the topics to answer the user's question\n"
    "user's question: {query_str}\n"
    "Answer: "
)

class Rag:
    def __init__(self, config_path='./.venv/config.yml'):
        
        with open(config_path, 'r', encoding='utf8') as ymlfile:
            self.cfg = box.Box(yaml.safe_load(ymlfile))
        
        self.client = weaviate.Client(self.cfg.WEAVIATE_URL)
        
        # Settings.embed_model = OllamaEmbedding(self.cfg.LLM,embed_batch_size=self.cfg.CHUNK_SIZE)
        lc_embed_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        Settings.embed_model = LangchainEmbedding(langchain_embeddings=lc_embed_model,model_name=self.cfg.LLM,embed_batch_size=self.cfg.CHUNK_SIZE)
      
        # self.llm = Ollama(
        #     model=self.cfg.LLM,
        #     base_url=self.cfg.OLLAMA_BASE_URL,
        #     temperature=self.cfg.TEMPERATURE
        # )        
        self.llm = LangChainLLM(
            # model=self.cfg.LLM,
            # base_url=self.cfg.OLLAMA_BASE_URL,
            # temperature=self.cfg.TEMPERATURE
            llm=Ollama(
                model=self.cfg.LLM,
                base_url=self.cfg.OLLAMA_BASE_URL,
                temperature=self.cfg.TEMPERATURE
            )
        )        
        self.vector_store = WeaviateVectorStore(
            weaviate_client=self.client,
            # index_name="A1150"
            index_name=self.cfg.INDEX_NAME
        )
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        summary_prompt_template = PromptTemplate(SUMMARY_TEMPLATE)
        self.summary_response_synthesizer = get_response_synthesizer(
            response_mode="tree_summarize",
            use_async=False,
            # llm = self.llm,
            summary_template=summary_prompt_template
        )
        self.zulip_question_prompt_template = PromptTemplate(ZULIP_QUERY_TEMPLATE)
        self.zulip_question_response_synthesizer = get_response_synthesizer(
            # response_mode="tree_summarize",
            use_async=False,
            # llm = self.llm,
            text_qa_template=self.zulip_question_prompt_template,
        )

        self.zulip_index = VectorStoreIndex.from_vector_store(
            vector_store = self.vector_store,
        )
        self.retriever = VectorIndexRetriever(
            index=self.zulip_index,
            similarity_top_k=10,
        )        
        self.zulip_query_engine = self.zulip_index.as_query_engine(
            # llm=self.llm,
            response_synthesizer=self.zulip_question_response_synthesizer,
        )
        # self.zulip_query_engine = RetrieverQueryEngine(
        #     retriever=self.retriever,
        #     response_synthesizer=self.zulip_question_response_synthesizer,
        #     node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.3)]
        # )        


        self.index_doc = None
        self.documents = []
        self.doc_query_engine = None

        

    def get_summary(self, title): 
        # to-do: what happens if title doesn't exists: need to ingest    
        doc_summary_index = DocumentSummaryIndex.from_documents(
            self.documents,
            # llm = self.llm,
            response_synthesizer=self.summary_response_synthesizer,
            show_progress=True)
        print("Building summary index...")
        doc_summary = doc_summary_index.get_document_summary(doc_id = title)
        return doc_summary


    def ingest_text(self, text, title):
        document = Document(text=text, doc_id = title, metadata={"stream": title})
        self.documents = [document]
        logging.debug("Adding doc to index main index...")

        # transformations = [
        #     TokenTextSplitter(chunk_size=self.cfg.CHUNK_SIZE, chunk_overlap=128),
        #     TitleExtractor(nodes=5,
        #                     # llm=self.llm
        #                     ),
        #     QuestionsAnsweredExtractor(questions=3,
        #                             #    llm=self.llm
        #                                )
        # ]

        self.zulip_index.from_documents(
            [document],
            storage_context=self.storage_context,
            show_progress=False,
            # transformations=transformations
            )
        

    def ask_doc(self, question):
        print("Asking doc...")
        return self.doc_query_engine.query(question)
    

    def ask_zulip(self, question):
        logger.debug("Asking zulip...")
        retrieved = self.zulip_query_engine.retrieve(question)
        for r in retrieved:
            print(r)
        # s = self.zulip_query_engine.synthesize(question, retrieved)
        # print(s)
        return self.zulip_query_engine.query(question)




    def ingest_docs_in_folder(self, folder_name, max_files = 100000):
        processed_files = 1
        total_files = 0
        for _, _, filenames in os.walk(folder_name):
            total_files += len(filenames)

        duration = 0
        start_time = time.time()
        for filename in os.listdir(folder_name):
            if (processed_files <= max_files):
                file_path = os.path.join(folder_name, filename)
                print(f"\rFile {processed_files}/{total_files}. Time to complete: {duration}", end="", flush=True)
                if os.path.isfile(file_path):
                    text = ""
                    with open(file_path, 'r') as file:
                        text = " ".join(line.rstrip() for line in file)
                    self.ingest_text(text, filename)
                    processed_files += 1
                    processing_time = time.time() - start_time
                    estimated_time = ((total_files - processed_files) * processing_time) / processed_files
                    duration = time.strftime("%H:%M:%S", time.gmtime(estimated_time))

        
        end_time=time.time()
        duration = time.strftime("\n\nIngest time: %H:%M:%S", time.gmtime(end_time - start_time))
        print(duration)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(stream=sys.stdout, level = logging.CRITICAL)
    # logger.addHandler(logging.StreamHandler(stream = sys.stdout))
    # logging.getLogger("httpcore").setLevel(level = logging.CRITICAL)
    # logging.getLogger("urllib3").setLevel(level = logging.CRITICAL)
    # logging.getLogger("httpx").setLevel(level = logging.INFO)
 
    parser = argparse.ArgumentParser()
    parser.add_argument('--ingest', type = str, required = False, help = 'Folder with files to ingest recursively')
    args = parser.parse_args()

    rag = Rag()

    if args.ingest:
        rag.ingest_docs_in_folder(args.ingest)
    
    while True:
        try:
            question = input("\n\n> ")
            # question="describe the workarounds or solutions mentioned around beaglebone and the openvpn"
            response = rag.ask_zulip(question)
            print(response)
            

            # print("DOC")
            # response  = rag.ask_doc(question)
            # print(response)

        except EOFError:
            break