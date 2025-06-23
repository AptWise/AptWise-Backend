"""
Test script to verify LinkedIn OAuth environment variables are loaded correctly.
"""
import os
from dotenv import load_dotenv

def test_environment_variables():
    """Test if environment variables are loaded correctly."""
    print("=" * 50)
    print("🔍 LinkedIn OAuth Environment Variables Test")
    print("=" * 50)
    
    # Load .env file
    load_dotenv()
    
    # Test environment variables
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI")
    
    print(f"\n📋 Environment Variables Status:")
    print(f"LINKEDIN_CLIENT_ID: {'✅ Found' if client_id else '❌ Missing'}")
    print(f"LINKEDIN_CLIENT_SECRET: {'✅ Found' if client_secret else '❌ Missing'}")
    print(f"LINKEDIN_REDIRECT_URI: {'✅ Found' if redirect_uri else '❌ Missing'}")
    
    print(f"\n📄 Values (for debugging):")
    print(f"LINKEDIN_CLIENT_ID: {client_id}")
    print(f"LINKEDIN_CLIENT_SECRET: {'*' * len(client_secret) if client_secret else 'None'}")
    print(f"LINKEDIN_REDIRECT_URI: {redirect_uri}")
    
    # Check if .env file exists
    env_file_exists = os.path.exists('.env')
    print(f"\n📁 .env file exists: {'✅ Yes' if env_file_exists else '❌ No'}")
    
    if env_file_exists:
        with open('.env', 'r') as f:
            content = f.read()
            print(f"\n📄 .env file content:")
            print(content)
    
    # Test if all required variables are present
    all_configured = all([client_id, client_secret, redirect_uri])
    print(f"\n🎯 All LinkedIn OAuth variables configured: {'✅ Yes' if all_configured else '❌ No'}")
    
    return all_configured

if __name__ == "__main__":
    success = test_environment_variables()
    if success:
        print("\n🎉 Environment variables are properly configured!")
    else:
        print("\n💥 Some environment variables are missing!")
        print("\n🔧 Make sure your .env file contains:")
        print("LINKEDIN_CLIENT_ID=your_client_id")
        print("LINKEDIN_CLIENT_SECRET=your_client_secret")  
        print("LINKEDIN_REDIRECT_URI=http://localhost:8000/auth/linkedin/callback")
