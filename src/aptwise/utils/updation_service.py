"""
Updation Service for managing question storage in vector database.
Handles checking and storing of LLM-generated interview questions.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import hashlib
from .qdrant_service import QdrantVectorService

logger = logging.getLogger(__name__)


class QuestionUpdationService:
    """Service for managing question storage and updates in vector database."""

    def __init__(self):
        """Initialize the updation service."""
        self.vector_service = QdrantVectorService()
        self.similarity_threshold = 0.85
        # Threshold for considering questions similar
        logger.info("Question Updation Service initialized")

    def _generate_question_id(self, question: str, answer: str = "") -> str:
        """
        Generate a deterministic ID for a question-answer pair.

        Args:
            question: The question text
            answer: The answer text (optional)

        Returns:
            Deterministic string ID
        """
        content = f"{question.strip()}|{answer.strip()}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _normalize_question(self, question: str) -> str:
        """
        Normalize question text for comparison.

        Args:
            question: Raw question text

        Returns:
            Normalized question text
        """
        # Remove extra whitespace, convert to
        # lowercase, remove punctuation at the end
        normalized = question.strip().lower()
        # Remove common trailing punctuation
        while normalized and normalized[-1] in '?.!':
            normalized = normalized[:-1]
        return normalized.strip()

    def check_question_exists(self, question: str,
                              threshold: Optional[float] =
                              None) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a question already exists in the vector database.

        Args:
            question: The question to check
            threshold: Similarity threshold (uses default if None)

        Returns:
            Tuple of (exists, existing_question_data)
            - exists: True if a similar question is found
            - existing_question_data: Data of the existing question if found
        """
        if threshold is None:
            threshold = self.similarity_threshold

        try:
            # Search for similar questions
            search_results = self.vector_service.search(
                query_text=question,
                n_results=5  # Check top 5 results
            )

            if not search_results:
                logger.info("No similar questions found in vector database")
                return False, None

            # Check if any result meets the similarity threshold
            for result in search_results:
                similarity = result.get('similarity', 0.0)
                existing_question = result.get('question', '')

                logger.debug(f"Comparing questions - \
                             Similarity: {similarity:.3f}")
                logger.debug(f"Existing: {existing_question[:100]}...")
                logger.debug(f"New: {question[:100]}...")

                if similarity >= threshold:
                    logger.info(f"Found similar question with \
                                similarity {similarity:.3f}")
                    return True, result

            # Also check for exact normalized matches (case-insensitive)
            normalized_new = self._normalize_question(question)
            for result in search_results:
                existing_question = result.get('question', '')
                normalized_existing = \
                    self._normalize_question(existing_question)

                if normalized_new == normalized_existing:
                    logger.info("Found exact normalized match")
                    return True, result

            logger.info("No similar questions found above threshold")
            return False, None

        except Exception as e:
            logger.error(f"Error checking question existence: {e}")
            return False, None

    def store_question(self, question: str, answer: str = "",
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a new question in the vector database.

        Args:
            question: The question text
            answer: The answer text (optional but recommended)
            metadata: Additional metadata to store with the question

        Returns:
            True if successfully stored, False otherwise
        """
        try:
            if not question.strip():
                logger.warning("Cannot store empty question")
                return False

            # Create document structure
            document = {
                'question': question.strip(),
                'answer': answer.strip() if answer else "",
                'source': 'llm_generated',
                'timestamp': metadata.get('timestamp') if metadata else None,
                'skill_context':
                    metadata.get('skill_context') if metadata else None,
                'user_id': metadata.get('user_id') if metadata else None,
                'interview_session':
                    metadata.get('interview_session') if metadata else None
            }

            # Store in vector database
            success = self.vector_service.index_documents([document])

            if success:
                logger.info(f"Successfully stored question: \
                            {question[:100]}...")
                return True
            else:
                logger.error("Failed to store question in vector database")
                return False

        except Exception as e:
            logger.error(f"Error storing question: {e}")
            return False

    def check_and_store_question(self,
                                 question: str,
                                 answer: str = "",
                                 metadata: Optional[Dict[str, Any]] = None,
                                 force_store: bool = False) -> Dict[str, Any]:
        """
        Check if a question exists and store it if it doesn't.

        Args:
            question: The question text
            answer: The answer text (optional)
            metadata: Additional metadata
            force_store: If True, store even if similar question exists

        Returns:
            Dictionary with operation results
        """
        try:
            result = {
                'question': question,
                'exists': False,
                'stored': False,
                'similar_question': None,
                'similarity_score': 0.0,
                'action_taken': 'none'
            }

            # Check if question already exists
            exists, existing_data = self.check_question_exists(question)
            result['exists'] = exists

            if existing_data:
                result['similar_question'] = existing_data.get('question')
                result['similarity_score'] = \
                    existing_data.get('similarity', 0.0)

            if not exists or force_store:
                # Store the question
                stored = self.store_question(question, answer, metadata)
                result['stored'] = stored

                if stored:
                    if exists and force_store:
                        result['action_taken'] = 'stored_despite_similarity'
                    else:
                        result['action_taken'] = 'stored_new_question'
                else:
                    result['action_taken'] = 'storage_failed'
            else:
                result['action_taken'] = 'skipped_similar_exists'
                logger.info(f"Skipping storage - similar question exists with \
                            similarity {result['similarity_score']:.3f}")

            return result

        except Exception as e:
            logger.error(f"Error in check_and_store_question: {e}")
            return {
                'question': question,
                'exists': False,
                'stored': False,
                'similar_question': None,
                'similarity_score': 0.0,
                'action_taken': 'error',
                'error': str(e)
            }

    def batch_check_and_store(self, questions_data:
                              List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch process multiple questions for checking and storing.

        Args:
            questions_data: List of dictionaries containing question data
                Each dict should have:
                {'question': str, 'answer': str, 'metadata': dict}

        Returns:
            List of results for each question
        """
        results = []

        for i, question_data in enumerate(questions_data):
            question = question_data.get('question', '')
            answer = question_data.get('answer', '')
            metadata = question_data.get('metadata', {})

            logger.info(f"Processing question {i+1}/{len(questions_data)}")

            result = self.check_and_store_question(question, answer, metadata)
            result['batch_index'] = i
            results.append(result)

        # Log summary
        stored_count = sum(1 for r in results if r['stored'])
        skipped_count = sum(1 for r in results
                            if r['action_taken'] ==
                            'skipped_similar_exists')
        error_count = sum(1 for r in results if r['action_taken'] == 'error')

        logger.info(f"Batch processing complete: {stored_count} stored, "
                    f"{skipped_count} skipped, {error_count} errors")

        return results

    def update_similarity_threshold(self, new_threshold: float) -> bool:
        """
        Update the similarity threshold for question comparison.

        Args:
            new_threshold: New threshold value (0.0 to 1.0)

        Returns:
            True if updated successfully
        """
        if 0.0 <= new_threshold <= 1.0:
            old_threshold = self.similarity_threshold
            self.similarity_threshold = new_threshold
            logger.info(f"Updated similarity threshold \
                from {old_threshold} to {new_threshold}")
            return True
        else:
            logger.error(f"Invalid threshold value: \
                {new_threshold}. Must be between 0.0 and 1.0")
            return False

    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the updation service and vector database.

        Returns:
            Dictionary with service statistics
        """
        try:
            collection_info = self.vector_service.get_collection_info()

            return {
                'service_status': 'active',
                'similarity_threshold': self.similarity_threshold,
                'vector_service_connected':
                self.vector_service.qdrant_client is not None,
                'collection_info': collection_info
            }
        except Exception as e:
            logger.error(f"Error getting service stats: {e}")
            return {
                'service_status': 'error',
                'error': str(e)
            }


# Global service instance for easy access
_updation_service = None


def get_updation_service() -> QuestionUpdationService:
    """Get or create the global updation service instance."""
    global _updation_service

    if _updation_service is None:
        _updation_service = QuestionUpdationService()
        logger.info("Created new QuestionUpdationService instance")

    return _updation_service


def check_and_store_interview_question(question: str,
                                       answer: str = "",
                                       skill_context: str = "",
                                       user_id: str = "",
                                       interview_session: str = "") \
                                         -> Dict[str, Any]:
    """
    Convenience function for interview question storage.

    Args:
        question: The interview question
        answer: Expected or sample answer
        skill_context: The skill/topic context
        user_id: User ID for tracking
        interview_session: Interview session ID

    Returns:
        Result dictionary from check_and_store_question
    """
    service = get_updation_service()

    metadata = {
        'skill_context': skill_context,
        'user_id': user_id,
        'interview_session': interview_session,
        'timestamp': None  # Will be set automatically if needed
    }

    return service.check_and_store_question(question, answer, metadata)
