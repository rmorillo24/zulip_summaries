# Zulip zummarizer

## About
This projects is intended to summarize Zulip threads and to offer a a Chat with Zulip, or Chat-with-the-Thread feature, all in local mode except access to Zulip threads.

## Components

- **Ollama**: Ollama is a lightweight library service that provides a Python-friendly interface for interacting with LLaMA, which is a large language model developed by Meta AI. It simplifies the process of utilizing LLaMA's capabilities, such as generating text or processing natural language, by abstracting the complexities of directly interfacing with the model's C++ implementation.

- **Weaviate DB**: Weaviate is an open-source vector search engine that combines database functionality with machine learning to enable semantic search across text, images, and custom data types. It converts data into vectors for efficient, meaning-based searches, supporting features like scalability, real-time ingestion, and automatic classification. In this project it's used for storing embeddings

- **llama_index**: LlamaIndex is a versatile data framework designed to connect custom data sources with large language models (LLMs) like GPT-4. It serves as a bridge between enterprise data and LLM applications, enabling the creation of production-ready LLM applications by ingesting, storing, indexing, and querying data from various sources

- **Streamlit**: Streamlit is an open-source Python library designed for creating and sharing web apps focused on data analysis and machine learning projects. It allows developers and data scientists to transform data scripts into web apps through simple Python scripts, incorporating interactive elements like sliders, buttons, and charts

## Configuration
These two configuration files can live anywhere. I'm using .venv by default.

### Zulip client
Add a .zulip.rc file with:

```
[api]
email=_yourzulipuser_
key=_youapikey__
site=_yourzulipchatserverurl_
```

### Ollama and DB
Add a config.yml file with:

```
LLM: 'llama2'
EMBEDDINGS: 'local:llama2'
WEAVIATE_URL: 'http://127.0.0.1:8080'
INDEX_NAME: 'theindexofyourchoice'
CHUNK_SIZE: 512
OLLAMA_BASE_URL: 'http://127.0.0.1:11434'
TEMPERATURE: 0
```

## Running the application
''''
docker start ollama

docker exec -it ollama ollama pull _llm model_

docker start weaviate-db

stramlit run main.py
''''

if you just want to try ollama, run

> docker exec -it ollama ollama list
> docker exec -it ollama ollama pull mistral
> docker exec -it ollama ollama run mistral

