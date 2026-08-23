# check_models.py - Updated to load .env file
import os
import requests
from dotenv import load_dotenv

# ==================== LOAD .ENV FILE ====================
# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')

# Load the .env file
load_dotenv(env_path)

# Debug: Check if .env was loaded
print(f"📁 Looking for .env at: {env_path}")
print(f"📄 .env exists: {os.path.exists(env_path)}")

# Get API key
api_key = os.getenv('GROQ_API_KEY', '')

print(f"🔑 API Key found: {'Yes' if api_key else 'No'}")

if not api_key:
    print("="*60)
    print("❌ No API key found!")
    print("="*60)
    print("\n💡 Please check:")
    print("1. Your .env file exists in the project folder")
    print("2. It contains: GROQ_API_KEY=your-actual-key")
    print("3. No spaces around the = sign")
    print("4. No quotes around the key")
    print("\n📝 Correct .env format:")
    print("GROQ_API_KEY=gsk_abcdefghijklmnopqrstuvwxyz123456")
    exit()

print("="*60)
print("🔍 Checking available Groq models...")
print("="*60)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        models = data.get('data', [])
        
        if models:
            print("\n✅ Available Models:")
            print("-" * 40)
            for model in models:
                model_id = model.get('id', '')
                # Show all models
                print(f"  📋 {model_id}")
            print("-" * 40)
            print(f"\n📋 Total models: {len(models)}")
            
            # Find chat models
            chat_models = [m['id'] for m in models if 'instruct' in m['id'] or 'chat' in m['id'] or 'instant' in m['id']]
            
            if chat_models:
                print(f"\n💡 Suggested models to use:")
                for model in chat_models[:5]:
                    print(f"  ✅ {model}")
                print(f"\n📝 Update your ai_service_free.py with: self.model = '{chat_models[0]}'")
        else:
            print("❌ No models found in response")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("="*60)