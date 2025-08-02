"""
AI service for generating interview presets using Google Gemini API.
"""
import os
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)


class AIPresetService:
    """Service for AI-powered interview preset generation."""

    def __init__(self):
        """Initialize the AI Preset service."""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not \
                             found in environment variables")

        # Configure Gemini API
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

        logger.info("AI Preset service initialized")

    def generate_interview_preset(self,
                                  description: str,
                                  user_skills: Optional[List[str]] = None
                                  ) -> Dict[str, Any]:
        """
        Generate an interview preset using Gemini API based on description.

        Args:
            description: Description of the interview preset to generate
            user_skills: Optional list of user's existing skills

        Returns:
            Dictionary containing the generated preset data
        """
        try:
            # Build the prompt
            prompt = self._build_preset_prompt(description, user_skills)

            # Log the full prompt before calling Gemini API
            logger.info("=" * 80)
            logger.info("PRESET GENERATION PROMPT BEING SENT TO GEMINI API:")
            logger.info("=" * 80)
            logger.info(prompt)
            logger.info("=" * 80)

            # Generate response using Gemini
            response = self.model.generate_content(prompt)

            if response.text:
                logger.info("Gemini API Response generated successfully")

                # Log the full LLM response
                logger.info("=" * 80)
                logger.info("GEMINI API PRESET GENERATION RESPONSE:")
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
                    preset_name = response_data.get('preset_name', '')
                    description = response_data.get('description', '')
                    company = response_data.get('company', '')
                    role = response_data.get('role', '')
                    skills = response_data.get('skills', [])

                    # Ensure skills is a list
                    if isinstance(skills, str):
                        skills = [skill.strip() for skill in
                                  skills.split(',') if skill.strip()]

                    logger.info(f"Successfully parsed JSON response.\
                                 Generated preset: {preset_name}")

                    return {
                        'success': True,
                        'preset_name': preset_name,
                        'description': description,
                        'company': company,
                        'role': role,
                        'skills': skills
                    }

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON response: {e}")
                    logger.error(f"Raw response: {response.text}")

                    # Fallback response if JSON parsing fails
                    return {
                        'success': False,
                        'error': 'Failed to parse AI response',
                        'raw_response': response.text
                    }

            else:
                logger.warning("Gemini API returned no response text")
                return {
                    'success': False,
                    'error': 'No response from AI service'
                }

        except Exception as e:
            logger.error(f"Error generating interview preset: {e}")
            return {
                'success': False,
                'error': f'AI service error: {str(e)}'
            }

    def _build_preset_prompt(self,
                             description: str,
                             user_skills: Optional[List[str]] = None
                             ) -> str:
        """
        Build the prompt for Gemini API to generate interview preset.

        Args:
            description: Description of the interview preset
            user_skills: Optional list of user's existing skills

        Returns:
            Formatted prompt string
        """

        user_skills_text = ""
        if user_skills and len(user_skills) > 0:
            user_skills_text = \
                f"User's existing skills: {', '.join(user_skills)}"

        prompt = f"""
        ## Core Objective
        You are an expert interview preparation specialist. \
        Your task is to generate a comprehensive interview \
        preset based on the user's description.

        ## Task Details
        Based on the description provided, generate a \
        structured interview preset with the following components:
        1. **preset_name**: A clear, professional name for the interview preset
        2. **description**: A detailed description of what \
            this interview preset covers
        3. **company**: The company name if mentioned or a \
            relevant company suggestion
        4. **role**: The specific job role/position
        5. **skills**: A comprehensive list of technical \
            and soft skills relevant to this role

        ## Important Notes
        **You should first check if the skills are present in the \
        and then generate a comprehensive list of skills.\
        Do not duplicate skills that are already in the user's \
        existing skills e.g., if the user has React in his skills \
        then do not include additional skills like \
        React (frontend) etc.**

        ## User Input
        **Description**: {description}
        {user_skills_text}

        ## Instructions
        - **Preset Name**: Create a professional, \
            descriptive name (e.g., "Senior Frontend Developer \
            at Meta", "Full-Stack Engineer Interview")
        - **Description**: A Single Line Description \
            of the interview preset, making it more \
            comprehensive and professional
        - **Company**: If no company is mentioned, \
            suggest a relevant well-known company in the industry
        - **Role**: Extract or infer the specific role from the description
        - **Skills**: Generate a comprehensive list of \
            8-15 relevant skills including:
          - Technical skills (programming languages, frameworks, tools)
          - Soft skills (communication, problem-solving, teamwork)
          - Industry-specific knowledge
          - If the user has existing skills, prioritize \
            including those that are relevant

        ## Output Format
        Generate your response **only** in the following \
        JSON format. Do not add any text before or after \
        the JSON object.

        ```json
        {{
            "preset_name": "Professional preset name",
            "description": "Comprehensive description of the interview preset",
            "company": "Company name",
            "role": "Specific job role",
            "skills": ["skill1", "skill2", "skill3", \
            "skill4", "skill5", "skill6", "skill7", \
            "skill8"]
        }}
        ```

        ## Examples
        If user says "Frontend developer at Google":
        - preset_name: "Frontend Developer at Google"
        - description: "Comprehensive interview preparation \
        for a Frontend Developer position at Google, \
        covering React, JavaScript, system design, and \
        Google-specific technologies."
        - company: "Google"
        - role: "Frontend Developer"
        - skills: ["React", "JavaScript", "TypeScript", \
        "HTML/CSS", "Node.js", "System Design", \
        "Data Structures", "Algorithms"]

        If user says "Machine learning engineer":
        - preset_name: "Machine Learning Engineer Interview"
        - description: "Complete interview preparation \
        for Machine Learning Engineer positions, covering \
        ML algorithms, Python, data processing, and model deployment."
        - company: "Meta"
        - role: "Machine Learning Engineer"
        - skills: ["Python", "TensorFlow", "PyTorch", \
        "Machine Learning", "Data Science", "Statistics", \
        "Deep Learning", "SQL"]
        """

        return prompt
