# Interview Evaluation Skill Level Integration

## Overview
This feature integrates user skill levels from the database with the interview evaluation process. The system now:

1. Fetches the user's current skill levels from the `user_skills` table
2. Includes these levels in the evaluation prompt for context
3. Gets conservative skill level assessments (1-5 scale) from the LLM
4. Updates the database with new skill levels based on interview performance

## Database Schema
The `user_skills` table stores user skill information:
- `email`: User's email (foreign key)
- `skill`: Name of the skill (e.g., "Python", "JavaScript")
- `proficiency`: Skill level as string ("1" to "5")

## Skill Level Scale
- **Level 1**: Beginner - Basic understanding, needs significant guidance
- **Level 2**: Novice - Some knowledge, requires supervision  
- **Level 3**: Intermediate - Solid foundation, can work independently on basic tasks
- **Level 4**: Advanced - Strong proficiency, can handle complex tasks
- **Level 5**: Expert - Deep expertise, can mentor others and solve complex problems

## Implementation Details

### New Database Functions
- `get_user_skills(email: str)` - Retrieves current user skills
- `update_user_skills_from_evaluation(email: str, skill_evaluations: Dict[str, int])` - Updates/inserts skill levels

### Enhanced Evaluation Service
- `get_user_current_skills(user_email: str)` - Gets user's current skill levels
- Modified `evaluate_interview()` to accept `user_email` parameter
- Updated prompt to include current skill levels as context
- Added conservative skill level assessment to JSON output

### API Changes
All evaluation endpoints now automatically:
1. Fetch user's current skill levels
2. Include them in the evaluation prompt
3. Update skill levels based on interview performance

### JSON Response Format
The evaluation response now includes:
```json
{
  "skill_level_assessment": {
    "Python": 4,
    "JavaScript": 3,
    "SQL": 2
  }
}
```

## Usage
The integration is automatic when calling evaluation endpoints. The system will:
1. Look up the authenticated user's current skills
2. Use them as context for more accurate evaluation
3. Update skill levels conservatively based on interview performance

## Testing
Use the enhanced test suite to verify functionality:
```bash
python -m tests.test_enhanced_evaluation
```

The test includes skill level update verification.
