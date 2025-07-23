"""
Interview evaluation service using Gemini AI.
"""
import os
import json
from typing import Dict, List, Any
import google.generativeai as genai
from datetime import datetime


class InterviewEvaluationService:
    """Service for evaluating interview performance using Gemini AI."""

    def __init__(self):
        """Initialize the Gemini AI client."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def evaluate_interview(self,
                           interview_data: Dict[str, Any],
                           conversation_history: List[Dict[str, str]]
                           ) -> Dict[str, Any]:
        """
        Evaluate an interview using Gemini AI.

        Args:
            interview_data: Dictionary containing interview metadata
            conversation_history: List of conversation messages

        Returns:
            Dictionary containing evaluation results
        """
        try:
            # Build the evaluation prompt
            prompt = self._build_evaluation_prompt(interview_data,
                                                   conversation_history)

            # Get evaluation from Gemini
            response = self.model.generate_content(prompt)

            # Parse the response
            evaluation_result = self._parse_evaluation_response(response.text)

            return {
                "success": True,
                "evaluation": evaluation_result,
                "evaluated_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error in interview evaluation: {e}")
            return {
                "success": False,
                "error": str(e),
                "evaluation": None
            }

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
            role_label = "Interviewer" \
                if message['role'] == 'assistant' \
                else "Candidate"
            conversation_text += f"{role_label}: {message['content']}\n\n"

        skills_text = ", ".join(skills) \
            if skills else "General interview skills"

        prompt = f"""
You are an expert technical interviewer \
and career coach. Please evaluate \
the following interview performance \
comprehensively.

**INTERVIEW CONTEXT:**
- Company: {company}
- Position: {role}
- Candidate: {user_name}
- Skills Assessed: {skills_text}

**CONVERSATION TRANSCRIPT:**
{conversation_text}

**EVALUATION INSTRUCTIONS:**
Please provide a detailed evaluation in the \
    following JSON format. Be constructive, \
    specific, and professional in your feedback.

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
        "feedback": "<assessment of enthusiasm, \
            collaboration, values alignment>"
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
1. **Technical Competency (30%)**: Knowledge depth, accuracy,\
      problem-solving approach
2. **Communication Skills (25%)**: Clarity, articulation, \
    listening, asking questions
3. **Problem Solving (25%)**: Analytical thinking, \
    approach to challenges, creativity
4. **Cultural Fit (20%)**: Enthusiasm, collaboration, \
    growth mindset, values alignment

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
        """Parse the evaluation response from Gemini AI."""
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

            # Validate required fields
            required_fields = [
                'overall_score', 'performance_summary', 'strengths',
                'areas_for_improvement', 'technical_competency',
                'communication_skills', 'problem_solving', 'cultural_fit',
                'detailed_feedback', 'next_steps', 'interview_grade'
            ]

            for field in required_fields:
                if field not in evaluation:
                    raise ValueError(f"Missing required field: {field}")

            return evaluation

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            # Return a fallback evaluation
            return self._create_fallback_evaluation(response_text)
        except Exception as e:
            print(f"Error parsing evaluation response: {e}")
            return self._create_fallback_evaluation(response_text)

    def _create_fallback_evaluation(self,
                                    response_text: str
                                    ) -> Dict[str, Any]:
        """Create a fallback evaluation if parsing fails."""
        return {
            "overall_score": 70,
            "performance_summary": "The evaluation \
                could not be fully processed, but the \
                candidate showed engagement throughout \
                the interview.",
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
                "feedback": "Technical skills \
                    assessment needs more detailed \
                    evaluation."
            },
            "communication_skills": {
                "score": 75,
                "feedback": "Communication was \
                    clear and professional."
            },
            "problem_solving": {
                "score": 70,
                "feedback": "Problem-solving approach \
                    could be more structured."
            },
            "cultural_fit": {
                "score": 80,
                "feedback": "Showed positive attitude \
                    and willingness to collaborate."
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
            "raw_response": response_text,
            "note": "This is a fallback evaluation due to parsing issues."
        }


# Create a singleton instance
evaluation_service = InterviewEvaluationService()
