from autogen import ConversableAgent
from src.config.settings import LLM_CONFIG
import json

def test_llm():
    """Test if LLM is working with current configuration."""
    print("\n=== Testing LLM Configuration ===")
    print(f"LLM Config: {json.dumps(LLM_CONFIG, indent=2)}")
    
    # Create a simple test agent
    test_agent = ConversableAgent(
        name="Test_Agent",
        llm_config=LLM_CONFIG,
        system_message="You are a helpful assistant that responds with short, clear answers.",
        human_input_mode="NEVER"
    )
    
    # Test message
    test_message = "What is 2+2? Answer in one word."
    
    print(f"\nSending test message: {test_message}")
    
    try:
        # Get response
        response = test_agent.generate_reply(
            messages=[{
                "role": "user",
                "content": test_message
            }]
        )
        
        print("\n=== LLM Response ===")
        print(f"Response: {response}")
        print("\nLLM is working correctly!")
        
    except Exception as e:
        print("\n=== Error ===")
        print(f"Error testing LLM: {str(e)}")
        print("\nLLM configuration may need to be checked.")

if __name__ == "__main__":
    test_llm() 