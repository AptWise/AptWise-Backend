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

    def evaluate_interview(self,
                           interview_data: Dict[str, Any],
                           conversation_history: List[Dict[str, str]]
                           ) -> Dict[str, Any]:
        """
        Evaluate an interview using Gemini AI with vector database reference
        context.

        Args:
            interview_data: Dictionary containing interview metadata
            conversation_history: List of conversation messages

        Returns:
            Dictionary containing evaluation results
        """
        try:
            # Get reference context from vector database
            skills = interview_data.get('skills', [])
            reference_context = \
                self.get_reference_context(skills,
                                           conversation_history)

            # Build the evaluation prompt with reference context
            prompt = self._build_evaluation_prompt_with_context(
                interview_data,
                conversation_history,
                reference_context
            )

            # Get evaluation from Gemini
            response = self.model.generate_content(prompt)

            # Parse the response
            evaluation_result = self._parse_evaluation_response(response.text)

            return {
                "success": True,
                "evaluation": evaluation_result,
                "evaluated_at": datetime.now().isoformat(),
                "reference_context_used": len(reference_context.get(
                    'questions_with_references', []))
            }

        except Exception as e:
            logger.error(f"Error in interview evaluation: {e}")
            return {
                "success": False,
                "error": str(e),
                "evaluation": None
            }

    def _build_evaluation_prompt_with_context(self,
                                              interview_data: Dict[str, Any],
                                              conversation_history: List[
                                                  Dict[str, str]],
                                              reference_context: Dict[str, Any]
                                              ) -> str:
        """Build the evaluation prompt with vector database reference
        context."""

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

        prompt = f"""
You are an expert technical interviewer and \
career coach. Please evaluate the following \
interview performance comprehensively using the \
reference answers from our knowledge base.

**INTERVIEW CONTEXT:**
- Company: {company}
- Position: {role}
- Candidate: {user_name}
- Skills Assessed: {skills_text}

**CONVERSATION TRANSCRIPT:**
{conversation_text}

{reference_text}

**EVALUATION INSTRUCTIONS:**
Please provide a detailed evaluation comparing the \
candidate's answers to the reference answers. For each answer, assess based on:

1. **Accurateness (40%)**: \
    How closely the answer matches the expected/reference \
    answer in terms of technical correctness and completeness
2. **Confidence (30%)**: \
    How assertive, structured, and clear \
    the delivery is - assess communication style and conviction
3. **Completeness (30%)**: \
    Whether the candidate covers all \
    essential points mentioned in the reference answer

Please provide your evaluation in the following JSON format:

{{
    "overall_score": <number between 1-100>,
    "performance_summary": \
        "<2-3 sentence overall assessment \
        comparing to reference answers>",
    "individual_answer_assessments": [
        {{
            "question_number": <number>,
            "question": "<the interview question>",
            "user_answer": "<candidate's answer>",
            "reference_answer": "<expected answer from knowledge base>",
            "accurateness": {{
                "score": <number between 1-100>,
                "feedback": \
                    "<specific assessment of technical accuracy vs reference>"
            }},
            "confidence": {{
                "score": <number between 1-100>,
                "feedback": "<assessment of delivery style and conviction>"
            }},
            "completeness": {{
                "score": <number between 1-100>,
                "feedback": "<assessment of coverage vs reference points>"
            }},
            "overall_answer_score": <number between 1-100>
        }}
    ],
    "strengths": [
        "<specific strength 1 with reference to expected answers>",
        "<specific strength 2>",
        "<specific strength 3>"
    ],
    "areas_for_improvement": [
        "<specific area 1 with reference to gaps vs expected answers>",
        "<specific area 2>",
        "<specific area 3>"
    ],
    "technical_competency": {{
        "score": <number between 1-100>,
        "feedback": \
            "<detailed technical assessment comparing to reference knowledge>"
    }},
    "communication_skills": {{
        "score": <number between 1-100>,
        "feedback": \
            "<assessment of communication clarity, articulation, confidence>"
    }},
    "problem_solving": {{
        "score": <number between 1-100>,
        "feedback": \
            "<assessment of analytical thinking \
            and approach vs expected methodology>"
    }},
    "cultural_fit": {{
        "score": <number between 1-100>,
        "feedback": \
            "<assessment of enthusiasm, collaboration, values alignment>"
    }},
    "detailed_feedback": {{
        "positive_highlights": [
            "<specific positive moment 1 comparing to reference standards>",
            "<specific positive moment 2>"
        ],
        "improvement_suggestions": [
            "<actionable suggestion 1 based on reference answer gaps>",
            "<actionable suggestion 2>",
            "<actionable suggestion 3>"
        ]
    }},
    "next_steps": [
        "<recommendation 1 based on knowledge gaps identified>",
        "<recommendation 2>",
        "<recommendation 3>"
    ],
    "interview_grade": "<letter grade: A+, A, A-, B+, B, B-, C+, C, C-, D, F>",
    "reference_coverage_score": \
        <number between 1-100, how well answers covered reference knowledge>
}}

**EVALUATION CRITERIA:**
1. **Technical Competency (30%)**: \
    Knowledge depth, accuracy vs reference answers, problem-solving approach
2. **Communication Skills (25%)**: \
    Clarity, articulation, confidence in delivery
3. **Problem Solving (25%)**: \
    Analytical thinking, approach to \
    challenges, methodology vs expected approach
4. **Cultural Fit (20%)**: \
    Enthusiasm, collaboration, growth mindset, values alignment

**SPECIFIC ASSESSMENT GUIDELINES:**
- **Accurateness**: \
    Compare technical content directly to reference answers. \
    High scores for matching key concepts, low scores for factual errors
- **Confidence**: Assess speech patterns, hesitation, structure. \
    Look for assertive language, clear explanations, logical flow
- **Completeness**: \
    Check if all major points from reference answer were covered. \
    Partial coverage gets medium scores

**GUIDELINES:**
- Be specific with examples from both the candidate's \
    responses and reference answers
- Highlight where the candidate exceeded or fell short of reference standards
- Provide actionable feedback based on knowledge gaps identified
- Consider the role and company context
- Be encouraging while being honest about \
    areas needing improvement relative to expected knowledge
- Focus on both technical accuracy and delivery confidence

Return ONLY the JSON response, no additional text.
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
You are an expert technical interviewer and career coach. \
    Please evaluate the following interview performance comprehensively.

**INTERVIEW CONTEXT:**
- Company: {company}
- Position: {role}
- Candidate: {user_name}
- Skills Assessed: {skills_text}

**CONVERSATION TRANSCRIPT:**
{conversation_text}

**EVALUATION INSTRUCTIONS:**
Please provide a detailed evaluation in the following JSON format. \
    Be constructive, specific, and professional in your feedback.

{{
    "overall_score": <number between 1-100>,
    "performance_summary": "<2-3 sentence overall assessment>",
    "strengths": [
        "<specific strength 1>",
        "<specific strength 2>",
        "<specific strength 3>"
    ],
    "areas_for_improvement": [
        "<specific area 1>",
        "<specific area 2>",
        "<specific area 3>"
    ],
    "technical_competency": {{
        "score": <number between 1-100>,
        "feedback": "<detailed technical assessment>"
    }},
    "communication_skills": {{
        "score": <number between 1-100>,
        "feedback": "<assessment of communication clarity, articulation>"
    }},
    "problem_solving": {{
        "score": <number between 1-100>,
        "feedback": "<assessment of analytical thinking and approach>"
    }},
    "cultural_fit": {{
        "score": <number between 1-100>,
        "feedback": \
            "<assessment of enthusiasm, collaboration, values alignment>"
    }},
    "detailed_feedback": {{
        "positive_highlights": [
            "<specific positive moment 1>",
            "<specific positive moment 2>"
        ],
        "improvement_suggestions": [
            "<actionable suggestion 1>",
            "<actionable suggestion 2>",
            "<actionable suggestion 3>"
        ]
    }},
    "next_steps": [
        "<recommendation 1>",
        "<recommendation 2>",
        "<recommendation 3>"
    ],
    "interview_grade": "<letter grade: A+, A, A-, B+, B, B-, C+, C, C-, D, F>"
}}

**EVALUATION CRITERIA:**
1. **Technical Competency (30%)**: \
    Knowledge depth, accuracy, problem-solving approach
2. **Communication Skills (25%)**: \
    Clarity, articulation, listening, asking questions
3. **Problem Solving (25%)**: \
    Analytical thinking, approach to challenges, creativity
4. **Cultural Fit (20%)**: \
    Enthusiasm, collaboration, growth mindset, values alignment

**GUIDELINES:**
- Be specific with examples from the conversation
- Provide actionable feedback for improvement
- Consider the role and company context
- Be encouraging while being honest about areas for growth
- Focus on both technical and soft skills
- Provide constructive criticism with suggestions

Return ONLY the JSON response, no additional text.
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
                'overall_score', 'performance_summary', 'strengths',
                'areas_for_improvement', 'technical_competency',
                'communication_skills', 'problem_solving', 'cultural_fit',
                'detailed_feedback', 'next_steps', 'interview_grade'
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

    def _sanitize_evaluation_data(self, evaluation:
                                  Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize evaluation data to
            ensure all scores meet minimum requirements."""
        try:
            sanitized = evaluation.copy()

            # Ensure overall_score is valid (>= 1)
            if 'overall_score' not in sanitized or \
                    sanitized['overall_score'] is None or \
                    sanitized['overall_score'] < 1:
                sanitized['overall_score'] = 50

            # Sanitize competency scores
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
                    if 'score' not in sanitized[field] or \
                            sanitized[field]['score'] is None or \
                            sanitized[field]['score'] < 1:
                        sanitized[field]['score'] = 50
                    # Ensure feedback is valid string
                    if 'feedback' not in sanitized[field] or \
                            sanitized[field]['feedback'] is None:
                        sanitized[field]['feedback'] = \
                            f"Assessment for {field.replace('_', ' ')} \
                                unavailable"

            # Ensure reference_coverage_score is valid if present
            if 'reference_coverage_score' in sanitized:
                if sanitized['reference_coverage_score'] is None or \
                        sanitized['reference_coverage_score'] < 1:
                    sanitized['reference_coverage_score'] = 50

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
            if 'question' not in sanitized or sanitized['question'] is None:
                sanitized['question'] = f"Interview question {index + 1}"

            # Ensure user_answer is a valid string
            if 'user_answer' not in sanitized or \
                    sanitized['user_answer'] is None:
                sanitized['user_answer'] = "No answer provided"

            # Ensure reference_answer is a valid string
            if 'reference_answer' not in sanitized or \
                    sanitized['reference_answer'] is None:
                sanitized['reference_answer'] = \
                    "No reference answer available"

            # Sanitize assessment dimensions
            for dimension in ['accurateness', 'confidence', 'completeness']:
                if dimension not in sanitized or not \
                        isinstance(sanitized[dimension], dict):
                    sanitized[dimension] = \
                        {'score': 50, 'feedback':
                            f"Unable to assess {dimension}"}
                else:
                    # Ensure score is valid (>= 1)
                    if 'score' not in sanitized[dimension] or \
                        sanitized[dimension]['score'] is None or \
                            sanitized[dimension]['score'] < 1:
                        sanitized[dimension]['score'] = 50
                    # Ensure feedback is valid string
                    if 'feedback' not in sanitized[dimension] or \
                            sanitized[dimension]['feedback'] is None:
                        sanitized[dimension]['feedback'] = \
                            f"Assessment for {dimension} unavailable"

            # Ensure overall_answer_score is valid (>= 1)
            if 'overall_answer_score' not in sanitized or \
                sanitized['overall_answer_score'] is None or \
                    sanitized['overall_answer_score'] < 1:
                sanitized['overall_answer_score'] = 50

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
            "overall_score": 70,
            "performance_summary": ("The evaluation could not be fully "
                                    "processed, but the candidate showed "
                                    "engagement throughout the interview."),
            "individual_answer_assessments": [
                {
                    "question_number": 1,
                    "question": "General interview question",
                    "user_answer": "Candidate provided responses",
                    "reference_answer": "No reference available",
                    "accurateness": {
                        "score": 70,
                        "feedback": "Unable to assess accuracy due to "
                                    "parsing issues"
                    },
                    "confidence": {
                        "score": 75,
                        "feedback": "Candidate appeared confident in responses"
                    },
                    "completeness": {
                        "score": 70,
                        "feedback": "Unable to fully assess completeness"
                    },
                    "overall_answer_score": 70
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

        # Extract individual answer metrics
        individual_assessments = evaluation.get(
            'individual_answer_assessments', [])
        answer_metrics = []

        for assessment in individual_assessments:
            answer_metrics.append({
                'question_number': assessment.get('question_number', 0),
                'question': assessment.get('question', ''),
                'accurateness_score': assessment.get('accurateness', {}).get(
                    'score', 0),
                'confidence_score': assessment.get('confidence', {}).get(
                    'score', 0),
                'completeness_score': assessment.get('completeness', {}).get(
                    'score', 0),
                'overall_score': assessment.get('overall_answer_score', 0)
            })

        # Calculate average scores for each dimension
        total_assessments = len(answer_metrics)
        avg_accurateness = (sum(a['accurateness_score']
                                for a in answer_metrics) / total_assessments
                            if total_assessments > 0 else 0)
        avg_confidence = (sum(a['confidence_score']
                              for a in answer_metrics) / total_assessments
                          if total_assessments > 0 else 0)
        avg_completeness = (sum(a['completeness_score']
                                for a in answer_metrics) / total_assessments
                            if total_assessments > 0 else 0)

        return {
            'success': True,
            'overall_score': evaluation.get('overall_score', 0),
            'interview_grade': evaluation.get('interview_grade', 'N/A'),
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
                'accurateness': round(avg_accurateness, 1),
                'confidence': round(avg_confidence, 1),
                'completeness': round(avg_completeness, 1)
            },
            'individual_answers': answer_metrics,
            'strengths': evaluation.get('strengths', []),
            'areas_for_improvement':
                evaluation.get('areas_for_improvement', []),
            'next_steps': evaluation.get('next_steps', []),
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
        overall_score = evaluation.get('overall_score', 0)
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
