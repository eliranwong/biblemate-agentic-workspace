import asyncio
import logging
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy

# Configure basic logging to see library outputs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google.antigravity")

async def main():
    config = LocalAgentConfig(
        system_instructions="You are a helpful assistant. You have access to local bible skills in .agents/skills.",
        policies=[policy.allow_all()]
    )
    try:
        async with Agent(config) as agent:
            print("Chatting with skill execution...")
            response = await agent.chat("Retrieve Genesis 1:1 using the bible skill")
            async for chunk in response:
                print(chunk, end="", flush=True)
            print("\nDone.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
