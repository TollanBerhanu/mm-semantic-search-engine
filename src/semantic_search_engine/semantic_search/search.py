import shelve
from json import dumps as to_json
from flask import Response
from semantic_search_engine.constants import CHROMA_SHELVE
from semantic_search_engine.semantic_search.ss_details import SemanticSearchDetails
from semantic_search_engine.shelves import retrieve
from . import collection, chain

class SemanticSearch():

    def __init__(self, access_token: str, user_info: dict) -> None:
        self.ss_details = SemanticSearchDetails(
            access_token=access_token,
            user_info=user_info
        )
        self.user_name = user_info['name']

        # Get the number of results to be returned by Chroma from shelve
        chroma_shelve = retrieve( CHROMA_SHELVE, 'chroma_n_results', 'max_chroma_distance' )
        self.chroma_n_results = int( chroma_shelve[0] )
        self.max_chroma_distance = float( chroma_shelve[1] )

        # with shelve.open(CHROMA_SHELVE) as chroma_shelve:
        #     self.chroma_n_results = int(chroma_shelve[ 'chroma_n_results' ])
        #     self.max_chroma_distance = float(chroma_shelve[ 'max_chroma_distance' ])
       
    # def semantic_search(self, query : str, with_llm: bool = True):
    def get_chroma_metadata(self, query : str):
        """executes a semantic search on an LLM based on a certain query from a\
        vector db.

        Parameters
        ----------
        query : str
            the search query text
        api_key : str, optional, deprecated
            prevously used to represent a togetherAI api_key but currently not\
            used, by default None

        Returns
        -------
        str
            an explanation of for the query provided by the LLM
        """
        
        filtered_chroma_indices = []
        try:
            # Get the list of channels for the User
            channels_list = self.ss_details.get_user_channel_list()

            query_result = collection.query(
                query_texts=[query],
                n_results=self.chroma_n_results,
                where = { "channel_id": { "$in": channels_list } } # Fiter chroma reslults by channel_id
            )

            # Filter out the results with distances below a certain threshold
            for idx, distance in enumerate(query_result["distances"][0]):
                if distance < self.max_chroma_distance:
                    filtered_chroma_indices.append(idx)

            print('Max Distance:  ', self.max_chroma_distance)
            print('Filtered idx result:  ', filtered_chroma_indices)
            print('All distances:  ', query_result["distances"][0])
            
             # Simply return if no relevant data is found
            if not filtered_chroma_indices:
                return None, None

        except Exception as err:
            raise('Failed to add to Chroma!', err)
        
        # Get the context to build the LLM prompt
        context = '\n'.join( [ query_result["documents"][0][idx] for idx in filtered_chroma_indices ] )

        # Get the details for each user, channel and message returned from chroma
        try:
            metadata_details = self.ss_details.get_metadata_details(
                ids=[ query_result["ids"][0][idx] for idx in filtered_chroma_indices ],
                metadatas=[ query_result["metadatas"][0][idx] for idx in filtered_chroma_indices ],
                distances=[ query_result["distances"][0][idx] for idx in filtered_chroma_indices ]
            )
            
        except Exception as err:
            raise('Fetching context details failed!', err)

        return context, metadata_details

    def get_llm_response(self, query, context) -> str:
        # Get the response from the LLM
        try:
            llm_response = chain.run(
                { 
                    "context" : context,
                    "query" : query,
                    "user": self.user_name
                }
            )
        except Exception as err:
            raise('LLM response failed!', err)

        return llm_response

    
    def semantic_search(self, query : str, with_llm: bool = True):
        try:
            context, metadata_details = self.get_chroma_metadata(query=query)

        except Exception as err:
            return Response(to_json({
                'message' : 'Something went wrong while fetching data from ChromaDB!',
                'log': err
                }), status=500, mimetype='application/json')

        llm_response = ''

        if not bool(context and metadata_details):
            llm_response = "Unable to find conversations related to your query."

        elif with_llm:
            try:
                llm_response = self.get_llm_response(
                    query=query,
                    context=context
                )
            except Exception as err:
                return Response(to_json({
                    'message' : 'Something went wrong while getting response from LLM!',
                    'log': err
                    }), status=500, mimetype='application/json')

        return {
            "llm": llm_response,
            "context": metadata_details or []
        }