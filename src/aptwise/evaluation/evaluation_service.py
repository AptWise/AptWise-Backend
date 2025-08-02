"""
Interview evaluation service using Gemini AI with vector database context.
"""
import os
import json
from typing import Dict, List, Any
import google.generativeai as genai
from datetime import datetime
import logging
from ..utils.qdrant_service import QdrantVectorService
from ..database import get_user_skills, update_user_skills_from_evaluation

logger = logging.getLogger(__name__)


class InterviewEvaluationService:
    """Service for evaluating interview performance using Gemini AI with
    vector database context."""

    def __init__(self):
        """Initialize the Gemini AI client and vector service."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

        # Initialize vector service for reference answers
        self.vector_service = QdrantVectorService()

        logger.info("Interview evaluation service initialized with vector "
                    "database support")

    def get_reference_context(self, skills: List[str],
                              conversation_history: List[Dict[str, str]]
                              ) -> Dict[str, Any]:
        """
        Get reference question-answer pairs from vector database based on
        skills and conversation context.

        Args:
            skills: List of skills assessed in the interview
            conversation_history: Conversation messages to extract questions
                from

        Returns:
            Dictionary containing reference context with questions and
                expected answers
        """
        try:
            # Extract interview questions from conversation history
            interview_questions = []
            for message in conversation_history:
                if message.get('role') == 'assistant':
                    content = message.get('content', '')
                    # Filter out system messages and keep actual questions
                    if content and not content.startswith(('Hello', 'Hi',
                                                           'Welcome',
                                                           'Thank you')):
                        interview_questions.append(content.strip())

            reference_context = {
                'questions_with_references': [],
                'skills_assessed': skills
            }

            # For each question, find the most similar reference Q&A pair
            for i, question in enumerate(interview_questions):
                # Search for similar questions in vector DB
                search_results = self.vector_service.search(
                    query_text=question,
                    n_results=3  # Get top 3 similar questions
                )

                if search_results:
                    # Take the most similar result
                    best_match = search_results[0]
                    reference_context['questions_with_references'].append({
                        'question_index': i,
                        'interview_question': question,
                        'reference_question': best_match.get('question', ''),
                        'reference_answer': best_match.get('answer', ''),
                        'similarity_score': best_match.get('similarity', 0.0)
                    })
                else:
                    # If no reference found, still include the question
                    reference_context['questions_with_references'].append({
                        'question_index': i,
                        'interview_question': question,
                        'reference_question': '',
                        'reference_answer': 'No reference answer available',
                        'similarity_score': 0.0
                    })

            logger.info(f"Retrieved reference context for "
                        f"{len(interview_questions)} questions")
            return reference_context

        except Exception as e:
            logger.error(f"Error getting reference context: {e}")
            return {
                'questions_with_references': [],
                'skills_assessed': skills,
                'error': str(e)
            }

    def get_user_current_skills(self, user_email: str) -> Dict[str, int]:
        """
        Get user's current skill levels from the database.

        Args:
            user_email: User's email address

        Returns:
            Dictionary mapping skill names to proficiency levels (1-5)
        """
        try:
            user_skills = get_user_skills(user_email)
            return {skill['skill']: int(skill['proficiency'])
                    for skill in user_skills}
        except Exception as e:
            logger.error(f"Error fetching user skills: {e}")
            return {}

    def _add_unassessed_skills(self,
                               evaluation_result: Dict[str, Any],
                               expected_skills: List[str]
                               ) -> Dict[str, Any]:
        """
        Add unassessed skills to a separate section for frontend display.

        Args:
            evaluation_result: The parsed evaluation result
            expected_skills: List of skills that were expected to be assessed

        Returns:
            Enhanced evaluation result with unassessed skills section
        """
        try:
            # Get skills that were actually assessed
            assessed_skills = set()
            if 'skill_performance_summary' in evaluation_result:
                assessed_skills.update(
                    evaluation_result['skill_performance_summary'].keys()
                    )
            if 'skill_level_assessment' in evaluation_result:
                assessed_skills.update(
                    evaluation_result['skill_level_assessment'].keys()
                    )

            # Find skills that were expected but not assessed
            expected_skills_set = set(expected_skills) \
                if expected_skills else set()
            unassessed_skills = expected_skills_set - assessed_skills

            # Add unassessed skills section
            if unassessed_skills:
                unassessed_list = []
                for skill in unassessed_skills:
                    unassessed_list.append({
                        'skill': skill,
                        'reason': f"No questions about {skill} \
                            were asked during the interview"
                    })

                evaluation_result['skills_not_assessed'] = unassessed_list
                logger.info(f"Added {len(unassessed_skills)} \
                            unassessed skills to evaluation result")
            else:
                evaluation_result['skills_not_assessed'] = []

            return evaluation_result

        except Exception as e:
            logger.error(f"Error adding unassessed skills: {e}")
            # Ensure the field exists even if there's an error
            evaluation_result['skills_not_assessed'] = []
            return evaluation_result

    def evaluate_interview(self,
                           interview_data: Dict[str, Any],
                           conversation_history: List[Dict[str, str]],
                           user_email: str = None
                           ) -> Dict[str, Any]:
        """
        Evaluate an interview using Gemini AI with vector database reference
        context and update user skill levels.

        Args:
            interview_data: Dictionary containing interview metadata
            conversation_history: List of conversation messages
            user_email: User's email for skill level updates (optional)

        Returns:
            Dictionary containing evaluation results
        """
        try:
            # Get reference context from vector database
            skills = interview_data.get('skills', [])
            reference_context = \
                self.get_reference_context(skills,
                                           conversation_history)

            # Get user's current skill levels if email is provided
            current_user_skills = {}
            if user_email:
                current_user_skills = self.get_user_current_skills(user_email)

            # Build the evaluation prompt with
            # reference context and current skills
            prompt = self._build_evaluation_prompt_with_context(
                interview_data,
                conversation_history,
                reference_context,
                current_user_skills
            )

            # Get evaluation from Gemini
            response = self.model.generate_content(prompt)

            # Parse the response
            evaluation_result = self._parse_evaluation_response(response.text)

            # Add expected skills information for proper not-assessed handling
            evaluation_result = self.\
                _add_unassessed_skills(evaluation_result, skills)

            # Update user skill levels if email is provided
            # and we have skill evaluations
            if user_email and 'skill_level_assessment' in evaluation_result:
                skill_updates = evaluation_result['skill_level_assessment']
                try:
                    update_success = \
                        update_user_skills_from_evaluation(user_email,
                                                           skill_updates)
                    if update_success:
                        logger.info(f"Successfully updated skill levels \
                                    for user {user_email}")
                    else:
                        logger.warning(f"Failed to update skill \
                                       levels for user {user_email}")
                except Exception as e:
                    logger.error(f"Error updating user skills: {e}")

            return {
                "success": True,
                "evaluation": evaluation_result,
                "evaluated_at": datetime.now().isoformat(),
                "reference_context_used": len(reference_context.get(
                    'questions_with_references', [])),
                "skills_updated": user_email is not None
            }

        except Exception as e:
            logger.error(f"Error in interview evaluation: {e}")
            return {
                "success": False,
                "error": str(e),
                "evaluation": None
            }

    def _build_evaluation_prompt_with_context(self,
                                              interview_data:
                                              Dict[str, Any],
                                              conversation_history:
                                              List[Dict[str, str]],
                                              reference_context:
                                              Dict[str, Any],
                                              current_user_skills:
                                              Dict[str, int] = None
                                              ) -> str:
        """Build the evaluation prompt with vector database reference
        context and user's current skill levels."""

        # Extract interview context
        company = interview_data.get('company', 'Unknown Company')
        role = interview_data.get('role', 'Unknown Role')
        skills = interview_data.get('skills', [])
        user_name = interview_data.get('userName', 'Candidate')

        # Format conversation history
        conversation_text = ""
        user_answers = []

        for message in conversation_history:
            role_label = ("Interviewer" if message['role'] == 'assistant'
                          else "Candidate")
            conversation_text += f"{role_label}: {message['content']}\n\n"

            # Extract user answers for individual assessment
            if message['role'] == 'user':
                user_answers.append({
                    'answer_index': len(user_answers),
                    'content': message['content']
                })

        skills_text = ", ".join(skills) \
                      if skills else "General interview skills"

        # Format reference context
        reference_text = ""
        questions_with_refs = reference_context.get(
            'questions_with_references', [])

        if questions_with_refs:
            reference_text = "\n**REFERENCE QUESTION-ANSWER PAIRS:**\n"
            for ref in questions_with_refs:
                similarity = ref.get('similarity_score', 0.0)
                reference_text += f"""
Q{ref['question_index'] + 1}: {ref['interview_question']}
Reference Answer: {ref['reference_answer']}
Similarity Score: {similarity:.2f}
---"""
        else:
            reference_text = ("\n**No reference answers available from "
                              "vector database.**\n")

        # Format current user skills
        current_skills_text = ""
        if current_user_skills:
            current_skills_text = "\n**USER'S CURRENT SKILL LEVELS:**\n"
            for skill, level in current_user_skills.items():
                current_skills_text += f"{skill}: Level {level}/5\n"
            current_skills_text += "---\n"
        else:
            current_skills_text = "\n**No previous skill \
                assessments available.**\n"

        prompt = f"""
        ## Core Objective & Persona
        You are a discerning and insightful career coach. \
            Your goal is to provide a comprehensive, fair, and \
            actionable evaluation of an interview performance. \
            You will analyze the entire conversation, compare the \
            candidate's responses to the provided reference answers, \
            and produce a structured JSON report.

        ---

        ## Core Task
        Your task is to generate a single JSON object that \
        evaluates the user's entire interview performance.
        1.  **Analyze the Full Transcript:** \
            Review the entire `{conversation_text}`.
        2.  **Compare to Ground Truth:** \
            For each user answer, critically compare it to the \
            corresponding `{reference_text}` If the user answer \
            is not related to the ground truth then use your \
            own judgement to evaluate its relevance to the \
            question.
        3.  **Evaluate on Key Metrics:** \
            Assess each answer based on Correctness, Completeness, \
            and Confidence.
        4.  **Aggregate by Skill:** \
            Synthesize the performance for each skill assessed \
            during the interview.
        5.  **Generate the Final Report:** \
            Output the complete evaluation in the specified JSON format.

        ---

        ## CONTEXT FOR EVALUATION
        -   **Company:** {company}
        -   **Role:** {role}
        -   **Candidate:** {user_name}
        -   **Skills Assessed:** {skills_text}
        -   **Full Conversation Transcript:** `{conversation_text}`
        -   **Reference Answers (Ground Truth):** `{reference_text}`
        -   **User's Current Skill Levels:** `{current_skills_text}`

        ---

        ## KEY EVALUATION DIRECTIVES

        ### 1. Primary Evaluation Metrics
        Base all your feedback on these three pillars. \
        The reference answer is the benchmark for "Excellent" (100).
        -   **Correctness:** \
            How technically accurate was the answer \
            compared to the reference? Was the information factually right?
        -   **Completeness:** \
            Did the answer cover all the key points and nuances \
            mentioned in the reference answer? How deep was the knowledge?
            If the user answer and the reference answer are of different \
            topics then judge based on your understanding of the user's \
            answer and the question asked to the user.
        -   **Confidence:** \
            How was the answer delivered? Was it structured, \
            clear, and assertive, or hesitant and disorganized?

        ### 2. Skill-Level Performance Tracking (CRITICAL)
        You MUST provide a summary for each \
        individual skill listed in `{skills_text}`.
        -   **Analyze & Aggregate:** \
            For each skill (e.g., "Python"), look at all questions \
            that touched upon that topic.
        -   **Assign a Score:** \
            Based on the user's performance across those specific \
            questions, assign a score that reflects their overall \
            proficiency in that skill.
        -   **Provide Feedback:** \
            Briefly explain why you gave that score. If their \
            performance met expectations for the role, state that. \
            If it was below expectations, note the key gaps.

        ### 3. Conservative Skill Level Assessment (NEW - CRITICAL)
        For each skill in the skill_level_assessment section, \
        provide a CONSERVATIVE estimate of the candidate's \
        actual skill level on a 1-5 scale:
        -   **Level 1:** Beginner - Basic understanding, \
            needs significant guidance
        -   **Level 2:** Novice - Some knowledge, requires \
            supervision
        -   **Level 3:** Intermediate - Solid foundation, can \
            work independently on basic tasks
        -   **Level 4:** Advanced - Strong proficiency, can \
            handle complex tasks
        -   **Level 5:** Expert - Deep expertise, can mentor \
            others and solve complex problems

        **IMPORTANT:** Be conservative in your assessment. \
        Consider the user's current skill levels provided above. \
        Only assign higher levels if the interview clearly demonstrates \
        mastery at that level. When in doubt, assign the lower level.

        ### 4. Reference Answer Generation (CRITICAL)
        For each question in the detailed breakdown, \
        you MUST provide a reference answer:
        -   **Use Available References:** \
            When reference answers are provided above, \
            use them as the baseline for the optimal response.
        -   **Generate Optimal Answers:** \
            When no reference is available, generate the optimal \
            answer that would demonstrate excellence for that \
            specific question.
        -   **Role-Specific:** \
            Tailor the reference answer to be appropriate \
            for the {role} position at {company}.
        -   **Completeness:** \
            Ensure the reference answer covers all key \
            points that should be addressed for maximum \
            correctness and completeness.

        ---

        ## OUTPUT FORMAT
        **CRITICAL:** Generate your response **only** in the \
        following JSON format. \
        Do not add any text before or after the JSON object.

        ```json
        {{
            "final_score": <number, weighted average from 1-100>,
            "overall_feedback": "<A 2-3 sentence summary of \
            the candidate's performance, \
            highlighting their general fit for the \
            role's technical requirements \
            based on the interview.>",
            "skill_performance_summary": {{
                "<skill_1_name>": {{
                    "score": <number from 1-100>,
                    "feedback": \
                    "<Brief assessment of proficiency in this skill. \
                    State if it meets or is below expectations for the role. \
                    e.g., 'Exceeded expectations. \
                    Demonstrated deep understanding \
                    of async patterns.' or 'Below expectations. \
                    Struggled with fundamental concepts like joins.'>"
                }},
            "<skill_2_name>": {{
                "score": <number from 1-100>,
                "feedback": "<Feedback for the second skill...>"
            }}
        }},
        "strengths": [
            "<A specific, concise strength observed, \
            tied to an example from the interview.>",
            "<Another specific strength.>"
        ],
        "areas_for_improvement": [
            "<A specific, actionable area for improvement, \
            referencing a gap compared to the reference answer.>",
            "<Another specific area for improvement.>"
        ],
        "detailed_breakdown": [
            {{
                "question_number": 1,
                "question": "<The first question asked>",
                "user_answer": "<The user's answer to the first question>",
                "reference_answer": \
                    "<The optimal/expected answer \
                    based on the reference knowledge base>",
                "evaluation": {{
                "correctness": \
                    {{ "score": <number from 1-100>, \
                        "feedback": "<Brief justification for \
                        correctness score.>" }},
                "completeness": \
                    {{ "score": <number from 1-100>, \
                        "feedback": "<Brief justification for \
                        completeness score.>" }},
                "confidence": \
                {{ "score": <number from 1-100>, \
                    "feedback": "<Brief justification \
                    for confidence score.>" }}
            }}
        }}
    ],
    "skill_level_assessment": {{
        "<skill_1_name>": \
            <conservative integer from 1-5 representing \
            actual skill level>,
        "<skill_2_name>": \
            <conservative integer from 1-5 representing \
            actual skill level>
    }}
}}
"""
        return prompt

    def _build_evaluation_prompt(self,
                                 interview_data: Dict[str, Any],
                                 conversation_history: List[Dict[str, str]]
                                 ) -> str:
        """Build the evaluation prompt for Gemini AI."""

        # Extract interview context
        company = interview_data.get('company', 'Unknown Company')
        role = interview_data.get('role', 'Unknown Role')
        skills = interview_data.get('skills', [])
        user_name = interview_data.get('userName', 'Candidate')

        # Format conversation history
        conversation_text = ""
        for message in conversation_history:
            role_label = ("Interviewer"
                          if message['role'] == 'assistant'
                          else "Candidate")
            conversation_text += f"{role_label}: {message['content']}\n\n"

        skills_text = (", ".join(skills)
                       if skills else "General interview skills")

        prompt = f"""
        ## Core Objective & Persona
        You are a discerning and insightful career coach. \
        Your goal is to provide a comprehensive, fair, and \
        actionable evaluation of an interview performance. \
        You will analyze the entire conversation, compare the \
        candidate's responses to the provided reference answers, \
        and produce a structured JSON report.

        ---

        ## Core Task
        Your task is to generate a single JSON \
        object that evaluates the user's entire \
        interview performance.
        1.  **Analyze the Full Transcript:** \
            Review the entire `{conversation_text}`.
        2.  **Compare to Ground Truth:** \
            For each user answer, critically compare it to \
            the corresponding reference answers if available.
        3.  **Evaluate on Key Metrics:** \
            Assess each answer based on Correctness, \
            Completeness, and Confidence.
        4.  **Aggregate by Skill:** \
            Synthesize the performance for each skill \
            assessed during the interview.
        5.  **Generate the Final Report:** \
            Output the complete evaluation in the specified JSON format.

        ---

        ## CONTEXT FOR EVALUATION
        -   **Company:** {company}
        -   **Role:** {role}
        -   **Candidate:** {user_name}
        -   **Skills Assessed:** {skills_text}
        -   **Full Conversation Transcript:** `{conversation_text}`

        ---

        ## KEY EVALUATION DIRECTIVES

        ### 1. Primary Evaluation Metrics
        Base all your feedback on these three pillars. \
        Reference answers (when available) are the \
        benchmark for "Excellent" (100).
        -   **Correctness:** \
            How technically accurate was the answer compared \
            to expected knowledge? Was the information factually right?
        -   **Completeness:** \
            Did the answer cover all the key points that \
            should be addressed? How deep was the knowledge?
        -   **Confidence:** \
            How was the answer delivered? Was it structured, \
            clear, and assertive, or hesitant and disorganized?

        ### 2. Skill-Level Performance Tracking (CRITICAL)
        You MUST provide a summary for each \
        individual skill listed in `{skills_text}`.
        -   **Analyze & Aggregate:** \
            For each skill (e.g., "Python"), look at all questions \
            that touched upon that topic.
        -   **Assign a Score:** \
            Based on the user's performance across those specific \
            questions, assign a score that reflects their overall \
            proficiency in that skill.
        -   **Provide Feedback:** \
            Briefly explain why you gave that score. If their \
            performance met expectations for the role, state that. \
            If it was below expectations, note the key gaps.

        ### 3. Reference Answer Generation (CRITICAL)
        For each question in the detailed breakdown, \
        you MUST provide a reference answer:
        -   **Use Available References:** \
            When reference answers are provided in \
            the context, use them as a baseline.
        -   **Generate Optimal Answers:** \
            When no reference is available, generate the optimal \
            answer that would demonstrate excellence for that \
            specific question.
        -   **Role-Specific:** \
            Tailor the reference answer to be appropriate \
            for the {role} position at {company}.
        -   **Completeness:** \
            Ensure the reference answer covers all key \
            points that should be addressed for maximum \
            correctness and completeness.

        ---

        ## OUTPUT FORMAT
        **CRITICAL:** Generate your response **only** in the \
        following JSON format. Do not add any text before or \
        after the JSON object.

        {{
            "final_score": <number, weighted average from 1-100>,
            "overall_feedback":
            "<A 2-3 sentence summary of the candidate's performance, \
            highlighting their general fit for the role's technical \
            requirements based on the interview.>",
            "skill_performance_summary": {{
                "<skill_1_name>": {{
                    "score": <number from 1-100>,
                    "feedback":
                    "<Brief assessment of proficiency in this skill. \
                    State if it meets or is below expectations for the \
                    role. e.g., 'Exceeded expectations. Demonstrated \
                    deep understanding of async patterns.' or \
                    'Below expectations. Struggled with fundamental \
                    concepts like joins.'>"
                }},
                "<skill_2_name>": {{
                    "score": <number from 1-100>,
                    "feedback": "<Feedback for the second skill...>"
                }}
            }},
            "strengths": [
                "<A specific, concise strength observed, \
                tied to an example from the interview.>",
                "<Another specific strength.>"
            ],
            "areas_for_improvement": [
                "<A specific, actionable area for improvement, \
                referencing a gap compared to expected knowledge.>",
                "<Another specific area for improvement.>"
            ],
            "detailed_breakdown": [
                {{
                    "question_number": 1,
                    "question": "<The first question asked>",
                    "user_answer": "<The user's answer to the first question>",
                    "reference_answer":
                    "<The optimal/expected answer based on \
                        the reference knowledge base>",
                    "evaluation": {{
                        "correctness": {{ "score": <number from 1-100>,
                        "feedback":
                        "<Brief justification for correctness score.>" }},
                        "completeness": {{ "score": <number from 1-100>,
                        "feedback":
                        "<Brief justification for completeness score.>" }},
                        "confidence": {{ "score": <number from 1-100>,
                        "feedback":
                        "<Brief justification for confidence score.>" }}
                    }}
                }}
            ]
        }}
        """
        return prompt

    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the evaluation response from Gemini AI with enhanced
        structure."""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()

            # Remove any markdown code blocks if present
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]

            cleaned_text = cleaned_text.strip()

            # Parse JSON
            evaluation = json.loads(cleaned_text)

            # Sanitize overall evaluation data
            evaluation = self._sanitize_evaluation_data(evaluation)

            # Validate required fields (enhanced structure)
            required_fields = [
                'final_score', 'overall_feedback', 'strengths',
                'areas_for_improvement', 'skill_performance_summary',
                'detailed_breakdown'
            ]

            for field in required_fields:
                if field not in evaluation:
                    logger.warning(f"Missing required field: {field}")

            # Validate and sanitize individual answer assessments if present
            if 'individual_answer_assessments' in evaluation:
                assessments = evaluation['individual_answer_assessments']
                sanitized_assessments = []

                for i, assessment in enumerate(assessments):
                    sanitized_assessment = \
                        self._sanitize_assessment(assessment, i)
                    if sanitized_assessment:
                        sanitized_assessments.append(sanitized_assessment)

                evaluation['individual_answer_assessments'] =\
                    sanitized_assessments

            return evaluation

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            # Return a fallback evaluation
            return self._create_fallback_evaluation(response_text)
        except Exception as e:
            logger.error(f"Error parsing evaluation response: {e}")
            return self._create_fallback_evaluation(response_text)

    def _sanitize_score(self, score, default=50):
        """Ensure score is valid (>= 1)."""
        if score is None or not isinstance(score, (int, float)):
            return default
        return max(1, int(score))

    def _sanitize_string(self, value, default=""):
        """Ensure string value is valid."""
        if value is None or not isinstance(value, str):
            return default
        return str(value).strip() if value else default

    def _sanitize_evaluation_data(self, evaluation:
                                  Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize evaluation data to
            ensure all scores meet minimum requirements."""
        try:
            sanitized = evaluation.copy()

            # Ensure final_score is valid (>= 1)
            sanitized['final_score'] = self._sanitize_score(
                sanitized.get('final_score'), 50
            )

            # Handle legacy overall_score field mapping
            # (always populate for backward compatibility)
            sanitized['overall_score'] = self._sanitize_score(
                sanitized.get('overall_score',
                              sanitized.get('final_score')), 50
            )

            # Ensure overall_feedback exists and map to
            # performance_summary for backward compatibility
            sanitized['overall_feedback'] = self._sanitize_string(
                sanitized.get('overall_feedback') or
                sanitized.get('performance_summary'),
                "Unable to provide detailed feedback"
            )

            # Always populate performance_summary for backward compatibility
            sanitized['performance_summary'] = sanitized['overall_feedback']

            # Ensure skill_performance_summary exists and sanitize scores
            if 'skill_performance_summary' not in sanitized or \
                    not isinstance(sanitized['skill_performance_summary'],
                                   dict):
                sanitized['skill_performance_summary'] = {}
            else:
                # Sanitize each skill's score and feedback
                for skill_name, skill_data in \
                        sanitized['skill_performance_summary'].items():
                    if not isinstance(skill_data, dict):
                        sanitized['skill_performance_summary'][skill_name] = {
                            'score': 50,
                            'feedback': f"Unable to assess {skill_name}"
                        }
                    else:
                        # Ensure score is valid (>= 1)
                        skill_data['score'] = \
                            self._sanitize_score(skill_data.get('score'), 50)
                        # Ensure feedback exists
                        skill_data['feedback'] = self._sanitize_string(
                            skill_data.get('feedback'),
                            f"Assessment for {skill_name} unavailable"
                        )

            # Ensure detailed_breakdown exists and sanitize
            if 'detailed_breakdown' not in sanitized or \
                    not isinstance(sanitized['detailed_breakdown'], list):
                sanitized['detailed_breakdown'] = []
            else:
                # Sanitize each question breakdown
                for i, breakdown in enumerate(sanitized['detailed_breakdown']):
                    if not isinstance(breakdown, dict):
                        continue

                    # Ensure user_answer is a valid string
                    breakdown['user_answer'] = self._sanitize_string(
                        breakdown.get('user_answer'), "No answer provided"
                    )

                    # Ensure question is a valid string
                    breakdown['question'] = self._sanitize_string(
                        breakdown.get('question'),
                        f"Interview question {i + 1}"
                    )

                    # Ensure reference_answer is a valid string
                    breakdown['reference_answer'] = self._sanitize_string(
                        breakdown.get('reference_answer'),
                        "No reference answer available"
                    )

                    # Ensure question_number is valid
                    if 'question_number' not in breakdown or \
                            breakdown['question_number'] is None:
                        breakdown['question_number'] = i + 1

                    # Sanitize evaluation metrics
                    if 'evaluation' not in breakdown or \
                            not isinstance(breakdown['evaluation'], dict):
                        breakdown['evaluation'] = {
                            'correctness':
                                {'score': 50, 'feedback':
                                    'Unable to assess correctness'},
                            'completeness':
                                {'score': 50, 'feedback':
                                    'Unable to assess completeness'},
                            'confidence':
                                {'score': 50, 'feedback':
                                    'Unable to assess confidence'}
                        }
                    else:
                        eval_data = breakdown['evaluation']
                        for metric in ['correctness',
                                       'completeness', 'confidence']:
                            if metric not in eval_data or \
                                    not isinstance(eval_data[metric], dict):
                                eval_data[metric] = {
                                    'score': 50,
                                    'feedback':
                                        f'Unable to assess {metric}'
                                }
                            else:
                                # Ensure score is valid (>= 1)
                                eval_data[metric]['score'] = \
                                    self._sanitize_score(
                                    eval_data[metric].get('score'), 50
                                )
                                # Ensure feedback exists
                                eval_data[metric]['feedback'] = \
                                    self._sanitize_string(
                                    eval_data[metric].get('feedback'),
                                    f'Assessment for {metric} unavailable'
                                )

            # Always populate backward compatibility fields
            competency_fields = \
                ['technical_competency', 'communication_skills',
                 'problem_solving', 'cultural_fit']
            for field in competency_fields:
                if field not in sanitized or \
                        not isinstance(sanitized[field], dict):
                    sanitized[field] = \
                        {'score': 50, 'feedback':
                            f"Unable to assess {field.replace('_', ' ')}"}
                else:
                    # Ensure score is valid (>= 1)
                    sanitized[field]['score'] = self._sanitize_score(
                        sanitized[field].get('score'), 50
                    )
                    # Ensure feedback is valid string
                    sanitized[field]['feedback'] = self._sanitize_string(
                        sanitized[field].get('feedback'),
                        f"Assessment for {field.replace('_', ' ')} unavailable"
                    )

            # Ensure detailed_feedback exists for backward compatibility
            if 'detailed_feedback' not in sanitized or \
                    not isinstance(sanitized['detailed_feedback'], dict):
                sanitized['detailed_feedback'] = {
                    'positive_highlights': [],
                    'improvement_suggestions': []
                }

            # Ensure next_steps exists
            if 'next_steps' not in sanitized or \
                    not isinstance(sanitized['next_steps'], list):
                sanitized['next_steps'] = []

            # Ensure interview_grade exists
            if 'interview_grade' not in sanitized:
                sanitized['interview_grade'] = 'B-'

            # Ensure strengths exists
            if 'strengths' not in sanitized or \
                    not isinstance(sanitized['strengths'], list):
                sanitized['strengths'] = []

            # Ensure areas_for_improvement exists
            if 'areas_for_improvement' not in sanitized or \
                    not isinstance(sanitized['areas_for_improvement'], list):
                sanitized['areas_for_improvement'] = []

            return sanitized

        except Exception as e:
            logger.error(f"Error sanitizing evaluation data: {e}")
            return evaluation

    def _sanitize_assessment(self, assessment: Dict[str, Any],
                             index: int) -> Dict[str, Any]:
        """Sanitize individual answer assessment to ensure valid values."""
        try:
            sanitized = assessment.copy()

            # Ensure question_number is valid
            if 'question_number' not in sanitized or not \
                    isinstance(sanitized['question_number'], int):
                sanitized['question_number'] = index + 1

            # Ensure question is a valid string
            sanitized['question'] = self._sanitize_string(
                sanitized.get('question'), f"Interview question {index + 1}"
            )

            # Ensure user_answer is a valid string
            sanitized['user_answer'] = self._sanitize_string(
                sanitized.get('user_answer'), "No answer provided"
            )

            # Ensure reference_answer is a valid string
            sanitized['reference_answer'] = self._sanitize_string(
                sanitized.get('reference_answer'),
                "No reference answer available"
            )

            # Sanitize assessment dimensions
            for dimension in ['accurateness', 'confidence', 'completeness']:
                if dimension not in sanitized or not \
                        isinstance(sanitized[dimension], dict):
                    sanitized[dimension] = \
                        {'score': 50, 'feedback':
                            f"Unable to assess {dimension}"}
                else:
                    # Ensure score is valid (>= 1)
                    sanitized[dimension]['score'] = self._sanitize_score(
                        sanitized[dimension].get('score'), 50
                    )
                    # Ensure feedback is valid string
                    sanitized[dimension]['feedback'] = self._sanitize_string(
                        sanitized[dimension].get('feedback'),
                        f"Assessment for {dimension} unavailable"
                    )

            # Ensure overall_answer_score is valid (>= 1)
            sanitized['overall_answer_score'] = self._sanitize_score(
                sanitized.get('overall_answer_score'), 50
            )

            return sanitized

        except Exception as e:
            logger.error(f"Error sanitizing assessment {index}: {e}")
            # Return a fallback assessment
            return {
                'question_number': index + 1,
                'question': f"Interview question {index + 1}",
                'user_answer': "Unable to parse answer",
                'reference_answer': "No reference available",
                'accurateness': {'score': 50, 'feedback':
                                 'Unable to assess accuracy'},
                'confidence': {'score': 50, 'feedback':
                               'Unable to assess confidence'},
                'completeness': {'score': 50, 'feedback':
                                 'Unable to assess completeness'},
                'overall_answer_score': 50
            }

    def _create_fallback_evaluation(self,
                                    response_text: str
                                    ) -> Dict[str, Any]:
        """Create a fallback evaluation if parsing fails."""
        return {
            "final_score": 70,
            "overall_feedback": ("The evaluation could not be fully "
                                 "processed, but the candidate showed "
                                 "engagement throughout the interview."),
            "skill_performance_summary": {
                "General Skills": {
                    "score": 70,
                    "feedback":
                        "Unable to assess specific \
                            skills due to parsing issues"
                }
            },
            "detailed_breakdown": [
                {
                    "question_number": 1,
                    "question": "General interview question",
                    "user_answer": "Candidate provided responses",
                    "evaluation": {
                        "correctness": {
                            "score": 70,
                            "feedback": "Unable to assess correctness due to "
                                        "parsing issues"
                        },
                        "completeness": {
                            "score": 70,
                            "feedback": "Unable to fully assess completeness"
                        },
                        "confidence": {
                            "score": 75,
                            "feedback":
                                "Candidate appeared confident in responses"
                        }
                    }
                }
            ],
            "strengths": [
                "Participated actively in the interview",
                "Showed willingness to learn",
                "Maintained professional communication"
            ],
            "areas_for_improvement": [
                "Technical depth could be enhanced",
                "More specific examples would strengthen responses",
                "Consider practicing common interview questions"
            ],
            # Maintain backward compatibility
            "overall_score": 70,
            "performance_summary": ("The evaluation could not be fully "
                                    "processed, but the candidate showed "
                                    "engagement throughout the interview."),
            "technical_competency": {
                "score": 70,
                "feedback": "Technical skills assessment needs more detailed "
                            "evaluation."
            },
            "communication_skills": {
                "score": 75,
                "feedback": "Communication was clear and professional."
            },
            "problem_solving": {
                "score": 70,
                "feedback":
                "Problem-solving approach could be more structured."
            },
            "cultural_fit": {
                "score": 80,
                "feedback": "Showed positive attitude and willingness to "
                            "collaborate."
            },
            "detailed_feedback": {
                "positive_highlights": [
                    "Maintained professional demeanor throughout",
                    "Asked clarifying questions when needed"
                ],
                "improvement_suggestions": [
                    "Practice articulating technical concepts more clearly",
                    "Prepare specific examples from past experience",
                    "Work on structuring responses using the STAR method"
                ]
            },
            "next_steps": [
                "Review technical concepts relevant to the role",
                "Practice mock interviews",
                "Gather specific examples of past achievements"
            ],
            "interview_grade": "B-",
            "reference_coverage_score": 60,
            "raw_response": response_text,
            "skills_not_assessed": [],
            "skill_level_assessment": {
                "General Skills": 3
            },
            "note": "This is a fallback evaluation due to parsing issues."
        }

    def extract_assessment_metrics(self,
                                   evaluation_result: Dict[str, Any]
                                   ) -> Dict[str, Any]:
        """
        Extract key assessment metrics for frontend display.

        Args:
            evaluation_result: The full evaluation result from
                evaluate_interview

        Returns:
            Dictionary with structured metrics for frontend consumption
        """
        if not evaluation_result.get('success', False):
            return {
                'success': False,
                'error': evaluation_result.get('error', 'Evaluation failed')
            }

        evaluation = evaluation_result.get('evaluation', {})

        # Extract individual answer metrics from new structure
        detailed_breakdown = evaluation.get('detailed_breakdown', [])
        answer_metrics = []

        for assessment in detailed_breakdown:
            eval_data = assessment.get('evaluation', {})
            answer_metrics.append({
                'question_number': assessment.get('question_number', 0),
                'question': assessment.get('question', ''),
                'correctness_score':
                    eval_data.get('correctness', {}).get('score', 0),
                'completeness_score':
                    eval_data.get('completeness', {}).get('score', 0),
                'confidence_score':
                    eval_data.get('confidence', {}).get('score', 0),
                'overall_score': (
                    eval_data.get('correctness', {}).get('score', 0) +
                    eval_data.get('completeness', {}).get('score', 0) +
                    eval_data.get('confidence', {}).get('score', 0)
                ) / 3 if eval_data else 0
            })

        # Fallback to old structure if new one is not available
        if not answer_metrics:
            individual_assessments = \
                evaluation.get('individual_answer_assessments', [])
            for assessment in individual_assessments:
                answer_metrics.append({
                    'question_number': assessment.get('question_number', 0),
                    'question': assessment.get('question', ''),
                    'correctness_score':
                        assessment.get('accurateness', {}).get('score', 0),
                    'completeness_score':
                        assessment.get('completeness', {}).get('score', 0),
                    'confidence_score':
                        assessment.get('confidence', {}).get('score', 0),
                    'overall_score': assessment.get('overall_answer_score', 0)
                })

        # Calculate average scores for each dimension
        total_assessments = len(answer_metrics)
        avg_correctness = (sum(a['correctness_score']
                               for a in answer_metrics) / total_assessments
                           if total_assessments > 0 else 0)
        avg_completeness = (sum(a['completeness_score']
                                for a in answer_metrics) / total_assessments
                            if total_assessments > 0 else 0)
        avg_confidence = (sum(a['confidence_score']
                              for a in answer_metrics) / total_assessments
                          if total_assessments > 0 else 0)

        # Get skill performance data
        skill_performance = evaluation.get('skill_performance_summary', {})

        return {
            'success': True,
            'overall_score':
                evaluation.get('final_score',
                               evaluation.get('overall_score', 0)),
            'overall_feedback':
                evaluation.get('overall_feedback',
                               evaluation.get('performance_summary', '')),
            'skill_performance_summary': skill_performance,
            'interview_grade':
                evaluation.get('interview_grade', 'N/A'),
            'reference_coverage_score':
                evaluation.get('reference_coverage_score', 0),
            'dimension_scores': {
                'technical_competency':
                    evaluation.get('technical_competency', {}).get('score', 0),
                'communication_skills':
                    evaluation.get('communication_skills', {}).get('score', 0),
                'problem_solving':
                    evaluation.get('problem_solving', {}).get('score', 0),
                'cultural_fit':
                    evaluation.get('cultural_fit', {}).get('score', 0)
                },
            'assessment_averages': {
                'correctness': round(avg_correctness, 1),
                'completeness': round(avg_completeness, 1),
                'confidence': round(avg_confidence, 1)
                },
            'individual_answers': answer_metrics,
            'strengths': evaluation.get('strengths', []),
            'areas_for_improvement':
                evaluation.get('areas_for_improvement', []),
            'next_steps': evaluation.get('next_steps', []),
            'skills_not_assessed':
                evaluation.get('skills_not_assessed', []),
            'skill_level_assessment':
                evaluation.get('skill_level_assessment', {}),
            'total_questions_assessed': total_assessments
        }

    def get_evaluation_summary(self,
                               evaluation_result: Dict[str, Any]) -> str:
        """
        Generate a brief text summary of the evaluation.

        Args:
            evaluation_result: The full evaluation result from
                evaluate_interview

        Returns:
            Human-readable summary string
        """
        if not evaluation_result.get('success', False):
            return "Evaluation could not be completed due to an error."

        evaluation = evaluation_result.get('evaluation', {})
        overall_score = evaluation.get('final_score',
                                       evaluation.get('overall_score', 0))
        grade = evaluation.get('interview_grade', 'N/A')
        reference_coverage = evaluation.get('reference_coverage_score', 0)

        # Determine performance level
        if overall_score >= 90:
            performance_level = "Excellent"
        elif overall_score >= 80:
            performance_level = "Good"
        elif overall_score >= 70:
            performance_level = "Satisfactory"
        elif overall_score >= 60:
            performance_level = "Needs Improvement"
        else:
            performance_level = "Poor"

        summary = (f"Overall Performance: {performance_level} "
                   f"(Score: {overall_score}/100, Grade: {grade}). ")
        summary += f"Reference Knowledge Coverage: {reference_coverage}%. "

        # Add key strengths and improvements
        strengths = evaluation.get('strengths', [])
        improvements = evaluation.get('areas_for_improvement', [])

        if strengths:
            summary += f"Key Strength: {strengths[0]}. "
        if improvements:
            summary += f"Priority Improvement: {improvements[0]}."

        return summary


# Create a singleton instance
evaluation_service = InterviewEvaluationService()
