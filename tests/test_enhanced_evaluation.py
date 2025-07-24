#!/usr/bin/env python3
"""
Test script for enhanced evaluation service with vector database integration.
"""

import os
import sys
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_evaluation_service():
    """Test the enhanced evaluation service functionality."""
    
    try:
        from aptwise.evaluation.evaluation_service import evaluation_service
        print("✓ Successfully imported evaluation service")
    except ImportError as e:
        print(f"✗ Failed to import evaluation service: {e}")
        return False
    
    # Sample interview data
    interview_data = {
        'company': 'TechCorp',
        'role': 'Python Developer',
        'userName': 'Test Candidate',
        'skills': ['Python', 'Django', 'REST APIs']
    }
    
    # Sample conversation history
    conversation_history = [
        {
            'role': 'assistant',
            'content': 'Can you explain what Python decorators are and how they work?'
        },
        {
            'role': 'user', 
            'content': 'Python decorators are functions that modify the behavior of other functions. They use the @ symbol and are applied before function definitions. They basically wrap functions to add extra functionality.'
        },
        {
            'role': 'assistant',
            'content': 'How would you handle database connections in a Django application?'
        },
        {
            'role': 'user',
            'content': 'In Django, I would use the ORM for database operations. I would configure the database in settings.py and use models to interact with the database. For connection pooling, I might use django-db-pool.'
        }
    ]
    
    print("\n=== Testing Reference Context Retrieval ===")
    try:
        skills = interview_data['skills']
        reference_context = evaluation_service.get_reference_context(skills, conversation_history)
        
        print(f"✓ Retrieved reference context for {len(skills)} skills")
        print(f"✓ Found {len(reference_context.get('questions_with_references', []))} question-answer mappings")
        
        # Display reference context summary
        for i, ref in enumerate(reference_context.get('questions_with_references', [])[:2]):
            print(f"  Question {i+1}: {ref['interview_question'][:50]}...")
            print(f"  Similarity: {ref['similarity_score']:.2f}")
            
    except Exception as e:
        print(f"✗ Reference context retrieval failed: {e}")
        return False
    
    print("\n=== Testing Enhanced Evaluation ===")
    try:
        evaluation_result = evaluation_service.evaluate_interview(
            interview_data=interview_data,
            conversation_history=conversation_history
        )
        
        if evaluation_result['success']:
            print("✓ Evaluation completed successfully")
            evaluation = evaluation_result['evaluation']
            
            print(f"  Overall Score: {evaluation.get('overall_score', 'N/A')}/100")
            print(f"  Grade: {evaluation.get('interview_grade', 'N/A')}")
            print(f"  Reference Coverage: {evaluation.get('reference_coverage_score', 'N/A')}%")
            
            # Check for individual assessments
            individual_assessments = evaluation.get('individual_answer_assessments', [])
            if individual_assessments:
                print(f"✓ Individual answer assessments: {len(individual_assessments)} questions")
                for assessment in individual_assessments[:2]:  # Show first 2
                    print(f"    Q{assessment.get('question_number', '?')}: "
                          f"Acc:{assessment.get('accurateness', {}).get('score', 'N/A')}, "
                          f"Conf:{assessment.get('confidence', {}).get('score', 'N/A')}, "
                          f"Comp:{assessment.get('completeness', {}).get('score', 'N/A')}")
            else:
                print("⚠ No individual answer assessments found")
                
        else:
            print(f"✗ Evaluation failed: {evaluation_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"✗ Enhanced evaluation failed: {e}")
        return False
    
    print("\n=== Testing Utility Methods ===")
    try:
        # Test metrics extraction
        metrics = evaluation_service.extract_assessment_metrics(evaluation_result)
        if metrics['success']:
            print("✓ Metrics extraction successful")
            print(f"  Assessment Averages: {metrics['assessment_averages']}")
            print(f"  Questions Assessed: {metrics['total_questions_assessed']}")
        else:
            print(f"✗ Metrics extraction failed: {metrics.get('error', 'Unknown error')}")
        
        # Test summary generation
        summary = evaluation_service.get_evaluation_summary(evaluation_result)
        print(f"✓ Summary generated: {summary[:100]}...")
        
    except Exception as e:
        print(f"✗ Utility methods failed: {e}")
        return False
    
    print("\n=== Test Results ===")
    print("✓ All tests passed successfully!")
    print("✓ Enhanced evaluation service is working correctly")
    print("✓ Vector database integration is functional")
    print("✓ Utility methods are operational")
    
    return True

def test_environment_setup():
    """Test if the environment is properly configured."""
    print("=== Environment Setup Check ===")
    
    # Check for required environment variables
    required_env_vars = ['GEMINI_API_KEY', 'QDRANT_URL', 'QDRANT_API_KEY']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠ Missing environment variables: {', '.join(missing_vars)}")
        print("  Some tests may fail without proper configuration")
    else:
        print("✓ All required environment variables are set")
    
    return len(missing_vars) == 0

if __name__ == "__main__":
    print("Enhanced Evaluation Service Test Suite")
    print("=" * 50)
    
    # Test environment setup
    env_ok = test_environment_setup()
    
    if not env_ok:
        print("\n⚠ Warning: Environment not fully configured")
        print("  Set GEMINI_API_KEY, QDRANT_URL, and QDRANT_API_KEY for full functionality")
    
    print("\nRunning evaluation service tests...")
    
    # Run the main tests
    if test_evaluation_service():
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
