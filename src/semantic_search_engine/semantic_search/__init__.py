import shelve
from semantic_search_engine.together_llm import TogetherLLM
from langchain import LLMChain, PromptTemplate
from semantic_search_engine.chroma import ChromaSingleton
from semantic_search_engine.constants import DEFAULT_CHROMA_N_RESULTS, DEFAULT_MAX_CHROMA_DISTANCE, CHROMA_SHELVE
from semantic_search_engine.shelves import create_default_shelve

prompt_template = PromptTemplate( input_variables=["context", "query", "user"], template="""\
[INST]\n
<<SYS>>
You are a helpful assistant and your name is "SearchNET".
Look at the following chat messages between the triple quotes.

### Chat messages:
```
\n{context}\n
```

My name is '{user}' and I'm asking the following question:

### Question: 
\n{query}\n

Write a response that answers the question based on what is discussed in the chat messages.
You must answer the question based on only the list of messages you are given.
Don't answer anything outside the context(chat messages) you are provided and do not respond with anything from your general knowledge.
If the messages are not related to the question, just mention that the topic was not discussed previously.
Do not provide any explanations leading to your response. Your responses should be concise and straightforward. 
<</SYS>>\n
[/INST]\
"""
)
# Try to mention the people that you get the context from and the times the messages were posted.

# A custom built langchain LLM 
together_llm = TogetherLLM()
# A langchain chain constructed with the above attributes
chain = LLMChain(
        llm=together_llm, 
        prompt=prompt_template,
        verbose=True
        # include the necessary output parser
    )

# Get or create a chroma collection
collection = ChromaSingleton().get_chroma_collection()


# Set default chroma_n_results && max_chroma_distance if they don't exist
create_default_shelve(
    shelve_name=CHROMA_SHELVE,
    max_chroma_distance=DEFAULT_MAX_CHROMA_DISTANCE,
    chroma_n_results=DEFAULT_CHROMA_N_RESULTS
)
# with shelve.open( CHROMA_SHELVE ) as chroma_shelve:
#     name, value = DEFAULT_MAX_CHROMA_DISTANCE
#     if not chroma_shelve.get( name, False ):
#         chroma_shelve[ name ] = value
    
#     name, value = DEFAULT_CHROMA_N_RESULTS
#     if not chroma_shelve.get( name, False ):
#         chroma_shelve[ name ] = value