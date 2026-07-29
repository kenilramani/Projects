
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

def check_import(module_name):
    try:
        __import__(module_name)
        print(f"✅ Import successful: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {module_name} - {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing {module_name}: {e}")
        return False

def verify_models():
    print("\n--- Verifying Models ---")
    try:
        from app.core.models import Asset, AssetSharedDetails, BotPersona, BotResponse
        print("✅ Models imported successfully")
        
        # Check fields
        bp = BotPersona(name="Test", company_name="Test", company_domain="test.com", company_description="Test", company_products=[])
        if hasattr(bp, 'assets'):
            print("✅ BotPersona has 'assets' field")
        else:
            print("❌ BotPersona missing 'assets' field")

        br = BotResponse(response="Test") 
        if hasattr(br, 'brochure_details'):
            print("✅ BotResponse has 'brochure_details' field")
        else:
            print("❌ BotResponse missing 'brochure_details' field")

    except Exception as e:
        print(f"❌ Model verification failed: {e}")

def verify_agents():
    print("\n--- Verifying Agents ---")
    modules = [
        "app.agents.brochure",
        "app.agents.brochure.agent",
        "app.agents.definitions",
        "app.agents.factory",
    ]
    for m in modules:
        check_import(m)

    try:
        from app.agents.factory import AgentFactory
        factory = AgentFactory()
        if hasattr(factory, 'get_asset_sharing_agent'):
            print("✅ AgentFactory has 'get_asset_sharing_agent'")
        else:
            print("❌ AgentFactory missing 'get_asset_sharing_agent'")
    except Exception as e:
        print(f"❌ Factory verification failed (might need mock dependencies): {e}")

def verify_prompts():
    print("\n--- Verifying Prompts ---")
    try:
        from app.prompts.instruction import main_prompt
        # Mock state for prompt generation (might be complex to mock fully, just checking import for now)
        print("✅ app.prompts.instruction imported successfully")
    except Exception as e:
        print(f"❌ Prompt verification failed: {e}")

def verify_streamlit():
    print("\n--- Verifying Streamlit UI ---")
    try:
        # Streamlit might be hard to run in script, but check import
        import streamlit_ui.persona
        print("✅ streamlit_ui.persona imported successfully")
    except Exception as e:
        # Streamlit commands might fail without streamlit run, but basic syntax should pass
        print(f"⚠️ Streamlit import warning (expected if not running via streamlit): {e}")

if __name__ == "__main__":
    print("Starting Integration Verification...")
    verify_models()
    verify_agents()
    verify_prompts()
    verify_streamlit()
    print("\nVerification Complete.")
