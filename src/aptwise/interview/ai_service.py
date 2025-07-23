"""
AI Interview service using Google Gemini API.
"""
import os
import google.generativeai as genai
from typing import Dict, List, Any, Optional
import logging
import random
import json
from ..utils.qdrant_service import QdrantVectorService

logger = logging.getLogger(__name__)


class AIInterviewService:
    """Service for handling AI-powered interview interactions."""

    def __init__(self):
        """Initialize the AI Interview service."""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not \
                             found in environment variables")

        # Configure Gemini API
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

        # Initialize vector service for RAG
        self.vector_service = QdrantVectorService()

        logger.info("AI Interview service initialized")

    def get_skill_context(self, skills: List[str],
                          search_context: Optional[str] = None
                          ) -> str:
        """
        Get context from vector database for given skills or search context.

        Args:
            skills: List of skills to search for
            search_context: Specific topic to
            search for (from previous response)

        Returns:
            Formatted context string with questions and answers
        """
        if search_context:
            # Validate that search_context is in the user's skills list
            # Convert both to lowercase for case-insensitive comparison
            search_context_lower = search_context.lower()

            # Check if search_context matches any skill (partial match allowed)
            matching_skill = None
            for skill in skills:
                if search_context_lower in skill.lower() \
                        or skill.lower() in search_context_lower:
                    matching_skill = skill
                    break

            if matching_skill:
                selected_skill = matching_skill
                logger.info(f"Using validated \
                            search context: {selected_skill}")
            else:
                selected_skill = random.choice(skills)
                logger.info(f"Search context '{search_context}' \
                            not in skills list. " +
                            f"Falling back to random \
                            skill: {selected_skill}")
        elif skills:
            # For the first question, select a random skill
            selected_skill = random.choice(skills)
            logger.info("Selected skill for initial" +
                        f" context: {selected_skill}")
        else:
            return "No specific skills provided for context."

        # Search for questions related to the skill/topic
        try:
            search_results = self.vector_service.search(
                query_text=selected_skill,
                n_results=5
            )

            if not search_results:
                return f"No context found for topic: {selected_skill}"

            # Format the results
            context_parts = []
            for i, result in enumerate(search_results, 1):
                question = result.get('question', 'No question')
                answer = result.get('answer', 'No answer')
                context_parts.append(f"Q{i}: {question}")
                context_parts.append(f"A{i}: {answer}")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error getting skill context: {e}")
            return f"Error retrieving context for topic: {selected_skill}"

    def generate_interview_question(
        self,
        user_details: Dict[str, Any],
        skills: List[str],
        conversation_history: str,
        search_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an interview question using Gemini API.

        Args:
            user_details: User information including name, company, role
            skills: List of skills for the interview
            conversation_history: Previous conversation as a string
            search_context: Topic to search for from previous response

        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Get context from vector database
            skill_context = self.get_skill_context(skills,
                                                   search_context)

            # Build the prompt
            prompt = self._build_prompt(user_details,
                                        skills,
                                        skill_context,
                                        conversation_history)

            # Log the full prompt before calling Gemini API
            logger.info("=" * 80)
            logger.info("PROMPT BEING SENT TO GEMINI API:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)

            # Log basic info without printing full context
            logger.info("Gemini API Request - User:" +
                        f" {user_details.get('userName', 'candidate')}," +
                        f" Skills: {skills}")

            # Generate response using Gemini
            response = self.model.generate_content(prompt)

            if response.text:
                logger.info("Gemini API Response generated successfully")

                # Log the full LLM response
                logger.info("=" * 80)
                logger.info("GEMINI API RESPONSE:")
                logger.info("=" * 80)
                logger.info(response.text)
                logger.info("=" * 80)

                # Parse the JSON response
                try:
                    cleaned_response = response.text.strip()
                    if cleaned_response.startswith('```json'):
                        cleaned_response = cleaned_response[7:]
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()

                    response_data = json.loads(cleaned_response)

                    # Extract the components
                    user_response = response_data.get('Response', '')
                    next_search_context = \
                        response_data.get('SearchContext', '')
                    evaluation = response_data.get('Evaluation', {})

                    # Validate that next_search_context is in the skills list
                    if next_search_context:
                        context_lower = next_search_context.lower()

                        # Check if search_context matches any skill
                        valid_context = any(
                            context_lower in skill.lower()
                            or skill.lower() in context_lower
                            for skill in skills
                        )

                        if not valid_context:
                            next_search_context = random.choice(skills)
                            logger.warning("AI returned invalid \
                                            SearchContext. Replaced " +
                                           f"with: {next_search_context}")

                    logger.info(f"Successfully parsed JSON response.\
                    Next search context: {next_search_context}")

                    return {
                        'success': True,
                        'question': user_response,
                        'search_context': next_search_context,
                        'evaluation': evaluation
                    }

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON response: {e}")
                    logger.error(f"Raw response: {response.text}")

                    # Fallback to raw text if JSON parsing fails
                    return {
                        'success': True,
                        'question': response.text.strip(),
                        'search_context': None,
                        'evaluation': None
                    }

            else:
                logger.warning("Gemini API returned no response text")
                return {
                    'success': False,
                    'question': "I'm having trouble generating \
                    a question right now. Could you tell me \
                    about your experience?",
                    'search_context': None,
                    'evaluation': None
                }

        except Exception as e:
            logger.error(f"Error generating interview question: {e}")
            return {
                'success': False,
                'question': "I'm experiencing some technical \
                difficulties. Let's continue - could you tell \
                me about your background?",
                'search_context': None,
                'evaluation': None
            }

    def _build_prompt(
        self,
        user_details: Dict[str, Any],
        skills: List[str],
        skill_context: str,
        conversation_history: str
    ) -> str:
        """
        Build the prompt for Gemini API.

        Args:
            user_details: User information
            skills: List of skills for the interview
            skill_context: Context from vector database
            conversation_history: Previous conversation

        Returns:
            Formatted prompt string
        """
        user_name = user_details.get('userName', 'candidate')
        company = user_details.get('company', 'the company')
        role = user_details.get('role', 'the position')

        # Extract the user's latest response from conversation history
        user_response = "No previous response."
        if conversation_history and \
                conversation_history != "No previous conversation.":
            lines = conversation_history.strip().split('\n')
            if lines:
                # Get the last line which should be the user's latest response
                last_line = lines[-1]
                if last_line.startswith('user: '):
                    user_response = last_line[6:]  # Remove 'user: ' prefix

        prompt = f"""
        ## Core Objective & Persona
        You are an expert technical interviewer named AptWise. \
            Your goal is to conduct a realistic and engaging interview \
            with the user, {user_name}, who is applying for the {role} \
            role at {company}.
        -   **Persona:** Be friendly, professional, and encouraging. \
            Use the user's first name, {user_name}, to build rapport.
        -   **Interaction Style:** Your responses should be \
            conversational, concise, and feel like a real human \
            interaction. Avoid robotic or overly formal language.

        ---

        ## CRITICAL CONSTRAINT - SKILLS RESTRICTION
        **YOU MUST ONLY ASK QUESTIONS ABOUT THE FOLLOWING SKILLS:**
        {', '.join(skills)}

        **NEVER ask questions about skills not in this list. \
        ALL questions must be directly related to one or more \
        of these specific skills. Also keep it fast moving. Do \
        not linger on any one question for too long. Keep \
        changing the topic frequently. Do not keep asking \
        from the same topic again and again.**
        ---

        ## Core Task
        Your task is to generate a JSON object containing three keys: \
            "Response", "SearchContext", and "Evaluation".
        1.  **Evaluate the User's Last Answer:** Analyze `{user_response}`.
        2.  **Formulate a Reply:** Craft a "Response" that replies to \
            the user's answer.
        3.  **Ask a New Question:** In the same "Response", ask a new, \
            single question based on the provided `{skill_context}` and \
            the user's performance so far.
        4.  **Plan the Next Topic:** Decide what topic you will ask \
            about in the *following* turn and place it in "SearchContext".

        ---

        ## Key Instructions & Logic

        ### 1. Replying to the User
        -   **If Correct:** Acknowledge the correct answer briefly and \
            positively.
        -   **If Partially Correct or Incorrect:** Gently correct the user. \
            Provide a very brief and clear explanation of the mistake. You \
            can then ask a clarifying question on the same topic to test \
            their understanding or move on.
            -   *Example Correction:* "That's on the right track, \
                {user_name}, but there's a key distinction you missed. \
                React DOM is specifically the package that acts as the 'glue' \
                between the Virtual DOM and the browser's real DOM. It’s \
                not the DOM itself."

        ### 2. Questioning Strategy
        -   **SKILLS RESTRICTION:** You can ONLY ask questions \
            about the skills provided above.
        -   **One Question at a Time:** **NEVER** ask more than one \
            question in your response.
        -   **Adaptive Difficulty:** Adjust the question difficulty based \
            on the user's performance. If `{user_name}` is answering \
            well (high evaluation scores), ask more complex, scenario-based \
            questions. If they are struggling, ask more foundational, \
            theoretical questions.
        -   **Topic Selection:** You can ask follow-up questions \
            on the same topic to dig deeper or pivot to a new topic \
            from the allowed skills list above. You can choose a single \
            topic, mix topics and can ask direct questions, scenario \
            based questions, or conceptual questions.

        ### 3. The `SearchContext` Field - **CRITICAL INSTRUCTION**
        -   The `SearchContext` field is for **planning ahead**. \
            It must contain the topic of the question you intend \
            to ask in your **next turn** (i.e., *after* the user answers\
            the question you are asking in the current response).
        -   **IMPORTANT:** The SearchContext MUST be one of the skills \
            listed above.
        -   **Example:** If allowed skills are Python, Machine Learning, SQL, \
            you can only use these topics in SearchContext.

        ---

        ## Context for this Turn
        -   **User Details:**
            -   Name: {user_name}
            -   Company: {company}
            -   Applying for the Role: {role}
        -   **ALLOWED SKILLS (ONLY ask about these):** {', '.join(skills)}
        -   **Available Questions:** `{skill_context}`
        -   **Conversation History:** `{conversation_history}`
        -   **User's Latest Response:** `{user_response}`

        ---

        ## Output Format
        Generate your response **only** in the following JSON format\
                Do not add any text before or after the JSON object.

        ```json
        {{
            "Response": "Your full response to the user, \
                including feedback on their last answer and \
                the new question about one of the allowed \
                skills: {', '.join(skills)}.",
            "SearchContext": "One of these allowed skills \
                that you plan to ask \
                about in your NEXT turn: {', '.join(skills)}",
            "Evaluation": {{
                "confidence": "Score from 1-5",
                "correctness": "Score from 1-5",
                "completeness": "Score from 1-5"
            }}
        }}
        """
        return prompt

    def format_conversation_history(self,
                                    messages: List[Dict[str, Any]]
                                    ) -> str:
        """
        Format conversation history for the prompt.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted conversation string
        """
        if not messages:
            return "No previous conversation."

        history_parts = []
        for message in messages:
            role = message.get('role', 'unknown')
            content = message.get('content', '')

            if role == 'user':
                history_parts.append(f"user: {content}")
            elif role == 'assistant':
                history_parts.append(f"aptwise: {content}")

        return "\n".join(history_parts)
