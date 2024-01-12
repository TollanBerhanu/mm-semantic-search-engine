from threading import Lock, Thread
from semantic_search_engine import constants
import chromadb
from chromadb.utils import embedding_functions

class _ChromaSingletonMeta(type):
    """A thread-safe implementation of a singleton class that creates chroma clients.\
    this meta class is used to control the instance creation of the ChromaSinglton class.
    """

    _instances = {}

    _lock: Lock = Lock()  # synchronizes threads during first access to the Singleton.
    

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """

        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class ChromaSingleton(metaclass=_ChromaSingletonMeta):
    """A class responsible for creating chroma connection. It's instance creation is\
    managed by the _ChromaSingletonMeta class.
    """
    _connection = None

    def __init__(
            self,
            use_path : bool = True, 
            database_path : str = constants.CHROMA_PATH, 
            host : str = constants.CHROMA_HOST, 
            port : str = constants.CHROMA_PORT,
            embedding_function : chromadb.EmbeddingFunction = embedding_functions.DefaultEmbeddingFunction()
        ) -> None:
        """Instantiates different parameters required for creating a Chroma client

        Parameters
        ----------
        use_path : bool, optional
            if true a path is created in local storage else an http client is used,\
            by default True.
        database_path : str, optional
            the local chroma client path to connect to, only valid if use_path is\
            true, by default constants.CHROMA_PATH.
        host : str, optional
            the remote host address of chroma db,only valid if use_path is false\
            ,by default constants.CHROMA_HOST
        port : _type_, optional
            the remote port of chroma db, only valid if use_path is false, by \
            default constants.CHROMA_PORT
        """

        self.use_path = use_path
        self.database_path = database_path
        self.host = host
        self.port = port
        self.embedding_function = embedding_function

    def get_connection(self) -> chromadb.API:
        """Returns a single chroma client even on multiple calls

        Returns
        -------
        chroma.API
            a chroma client (API class)
        """
        if self._connection is None:
            if self.use_path: # use local storage
                self._connection = chromadb.PersistentClient(path=self.database_path)
            else:  # use http client
                # TODO : handle the case where the two parameters does not exist
                self._connection = chromadb.HttpClient(self.host, self.port)

        return self._connection

    def get_chroma_collection(self) -> chromadb.Collection:
        collection = self.get_connection().\
            get_or_create_collection(
                constants.CHROMA_COLLECTION,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"} 
            )
        return collection