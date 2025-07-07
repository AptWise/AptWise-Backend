"""
Qdrant vector database service for AptWise backend.
Provides functionality for storing and
searching vector embeddings using Qdrant.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantVectorService:
    """Service for handling vector embeddings with Qdrant."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Qdrant vector service.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.collection_name = "python_questions"

        # Initialize Qdrant client
        self.qdrant_client = self._initialize_qdrant_client()

        logger.info("Qdrant vector service " +
                    f"initialized with model: {model_name}")
        logger.info(f"Embedding dimension: {self.embedding_dim}")

    def _initialize_qdrant_client(self) -> Optional[QdrantClient]:
        """Initialize Qdrant client using environment variables."""
        try:
            qdrant_url = os.getenv("QDRANT_URL")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")

            if not qdrant_url or not qdrant_api_key:
                logger.error("QDRANT_URL or QDRANT_API_KEY\
                              not found in environment variables")
                return None

            client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
            )

            logger.info("Successfully connected to Qdrant")
            return client

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            return None

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            List of floats representing the embedding
        """
        embedding = self.model.encode([text], convert_to_numpy=True)[0]
        return embedding.tolist()

    def _generate_deterministic_id(self, question: str, answer: str) -> str:
        """
        Generate a deterministic ID based on question and answer content.
        This prevents duplicate entries when re-indexing.

        Args:
            question: The question text
            answer: The answer text

        Returns:
            Deterministic string ID
        """
        content = f"{question}|{answer}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def create_collection(self) -> bool:
        """
        Create a collection in Qdrant if it doesn't exist.

        Returns:
            True if successful, False otherwise
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not initialized")
            return False

        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name}" +
                            " already exists")

            return True

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False

    def clear_collection(self) -> bool:
        """
        Clear all points from the collection.

        Returns:
            True if successful, False otherwise
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not initialized")
            return False

        try:
            # Delete the entire collection and recreate it
            logger.info(f"Deleting collection: {self.collection_name}")
            self.qdrant_client.delete_collection(
                collection_name=self.collection_name
                )

            # Recreate the collection
            logger.info(f"Recreating collection: {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )

            logger.info("Successfully cleared and recreated" +
                        f"collection: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False

    def collection_exists_and_has_data(self) -> bool:
        """Check if the collection exists and has documents."""
        if not self.qdrant_client:
            return False

        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                logger.info(f"Collection '{self.collection_name}'" +
                            " does not exist")
                return False

            # Check if collection has documents
            collection_info = self.qdrant_client.\
                get_collection(self.collection_name)

            # Handle cases where vectors_count might be None
            vectors_count = getattr(collection_info, 'vectors_count', None)
            if vectors_count is None:
                # Try alternative fields that might indicate document count
                vectors_count = getattr(collection_info, 'points_count', None)

            # Default to 0 if still None
            if vectors_count is None:
                vectors_count = 0

            has_data = vectors_count > 0

            if has_data:
                logger.info(f"Collection '{self.collection_name}'" +
                            f" exists with {vectors_count} documents")
            else:
                logger.info(f"Collection '{self.collection_name}' " +
                            "exists but is empty (vectors_count:" +
                            f" {vectors_count})")

            return has_data

        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False

    def load_data_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load data from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            List of loaded data
        """
        logger.info(f"Loading data from: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, dict) and 'questions' in data:
                return data['questions']
            elif isinstance(data, list):
                return data
            else:
                return [data]
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            return []

    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Index documents in Qdrant.

        Args:
            documents: List of documents with 'question' and 'answer' fields

        Returns:
            True if successful, False otherwise
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not initialized")
            return False

        try:
            points = []
            # Track IDs to prevent duplicates within this batch
            seen_ids = set()

            for i, doc in enumerate(documents):
                question = doc.get('question', '').strip()
                answer = doc.get('answer', '').strip()

                if not question:
                    logger.warning(f"Empty question at index {i}, skipping")
                    continue

                # Generate deterministic ID to prevent duplicates
                point_id = self._generate_deterministic_id(question, answer)

                # Skip if we've already seen this ID in this batch
                if point_id in seen_ids:
                    logger.debug("Duplicate document " +
                                 f"detected at index {i}, skipping")
                    continue

                seen_ids.add(point_id)

                # Generate embedding for the question
                embedding = self.generate_embedding(question)

                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        'question': question,
                        'answer': answer,
                        'source_index': i
                    }
                )
                points.append(point)

                # Log progress
                if (i + 1) % 20 == 0:
                    logger.info("Processed " +
                                f"{i + 1}/{len(documents)}" +
                                " documents")

            # Upload points to Qdrant
            if points:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"Successfully indexed {len(points)}" +
                            " unique documents in Qdrant")
                return True
            else:
                logger.warning("No valid documents to index")
                return False

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return False

    def search(self, query_text: str,
               n_results: int = 5
               ) -> List[Dict[str, Any]]:
        """
        Search for similar questions using Qdrant.

        Args:
            query_text: Query text
            n_results: Number of results to return

        Returns:
            List of search results
        """
        if not self.qdrant_client:
            logger.error("Qdrant client not initialized")
            return []

        try:
            logger.info(f"Searching for: {query_text[:50]}...")

            # Generate query embedding
            query_embedding = self.generate_embedding(query_text)

            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=n_results,
                with_payload=True
            )

            # Format results
            results = []
            for i, result in enumerate(search_results):
                results.append({
                    'id': str(result.id),
                    'question': result.payload.get('question', ''),
                    'answer': result.payload.get('answer', ''),
                    'similarity': float(result.score),
                    'rank': i + 1
                })

            logger.info(f"Found {len(results)} similar questions")
            return results

        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.

        Returns:
            Collection information
        """
        if not self.qdrant_client:
            return {"error": "Qdrant client not initialized"}

        try:
            collection_info = self.qdrant_client.\
                get_collection(self.collection_name)

            # Handle possible None values for counts
            vectors_count = getattr(collection_info,
                                    'vectors_count',
                                    None) or 0
            indexed_vectors_count = getattr(collection_info,
                                            'indexed_vectors_count',
                                            None) or 0
            points_count = getattr(collection_info,
                                   'points_count',
                                   None) or 0

            return {
                "name": self.collection_name,
                "status": "active",
                "vectors_count": vectors_count,
                "indexed_vectors_count": indexed_vectors_count,
                "points_count": points_count
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}

    def auto_initialize_if_needed(self) -> bool:
        """
        Automatically initialize the
        collection if it doesn't exist or is empty.

        Returns:
            True if collection is ready
            (existed or was created), False otherwise
        """
        try:
            # Check if collection already exists and has data
            if self.collection_exists_and_has_data():
                logger.info("✅ Collection is ready - no initialization needed")
                return True

            logger.info("🔄 Initializing collection with data...")
            success = self.load_all_data_files()

            if success:
                logger.info("✅ Collection initialized successfully")
            else:
                logger.error("❌ Failed to initialize collection")

            return success

        except Exception as e:
            logger.error(f"Error in auto-initialization: {e}")
            return False

    def load_all_data_files(self,
                            data_dir: str = "./data",
                            force_reload: bool = False
                            ) -> bool:
        """
        Load and index all JSON files from the data directory.

        Args:
            data_dir: Directory containing JSON data files
            force_reload: If True, clear existing data and reload everything

        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(data_dir):
                logger.error(f"Data directory {data_dir} does not exist")
                return False

            # Check if we already have data before proceeding
            if not force_reload and self.collection_exists_and_has_data():
                logger.info("Collection already \
                            has data, skipping initialization")
                return True

            # Create collection first
            if not self.create_collection():
                logger.error("Failed to create collection")
                return False

            # Clear existing data if force_reload or if we detected duplicates
            if force_reload:
                logger.info("🧹 Clearing existing data for fresh reload...")
                if not self.clear_collection():
                    logger.warning("Failed to \
                                   clear collection, continuing anyway...")

            all_documents = []

            # Load all JSON files
            for filename in os.listdir(data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(data_dir, filename)
                    logger.info(f"📁 Loading file: {filename}")

                    documents = self.load_data_from_json(file_path)
                    if documents:
                        all_documents.extend(documents)
                        logger.info(f"✅ Loaded {len(documents)}" +
                                    f" documents from {filename}")
                    else:
                        logger.warning(f"⚠️ No documents found in {filename}")

            if all_documents:
                logger.info("📊 Total documents to index:" +
                            f" {len(all_documents)}")

                # Remove duplicates based on question-answer pairs
                unique_docs = []
                seen_content = set()

                for doc in all_documents:
                    question = doc.get('question', '').strip()
                    answer = doc.get('answer', '').strip()
                    content_key = f"{question}|{answer}"

                    if content_key not in seen_content:
                        unique_docs.append(doc)
                        seen_content.add(content_key)

                logger.info(f"🔍 Found {len(unique_docs)}" +
                            " unique documents (removed" +
                            f" {len(all_documents) - len(unique_docs)}" +
                            "duplicates)")

                return self.index_documents(unique_docs)
            else:
                logger.warning("⚠️ No documents found to index")
                return False

        except Exception as e:
            logger.error(f"❌ Error loading data files: {e}")
            return False


# Global service instance
_vector_service = None


def get_qdrant_service() -> Optional[QdrantVectorService]:
    """Get or create Qdrant vector \
        instance with lazy initialization."""
    global _vector_service

    if _vector_service is None:
        try:
            _vector_service = QdrantVectorService()
            if _vector_service.qdrant_client is None:
                logger.error("Failed to initialize Qdrant service")
                return None

            logger.info("Qdrant service created successfully")

        except Exception as e:
            logger.error(f"Error creating Qdrant service: {e}")
            return None

    return _vector_service


def initialize_vector_database(force_reload:
                               bool = False
                               ) -> Optional[QdrantVectorService]:
    """Initialize vector database with all data files."""
    try:
        logger.info("Initializing Qdrant vector database...")
        service = get_qdrant_service()

        if not service:
            logger.error("Failed to create Qdrant service")
            return None

        # Force re-initialization if requested
        success = service.load_all_data_files(force_reload=force_reload)

        if success:
            logger.info("Vector database initialized successfully")
        else:
            logger.error("Failed to initialize vector database")

        return service

    except Exception as e:
        logger.error(f"Error initializing vector database: {e}")
        return None


def force_reindex_database() -> Optional[QdrantVectorService]:
    """Force a complete re-indexing of the vector database."""
    logger.info("🔄 Force re-indexing vector database...")
    return initialize_vector_database(force_reload=True)
