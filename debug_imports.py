
import sys
try:
    import langchain
    print(f"LangChain version: {langchain.__version__}")
except Exception as e:
    print(f"Error importing langchain: {e}")

print("Attempting imports...")
try:
    from langchain.agents import AgentExecutor
    print("SUCCESS: from langchain.agents import AgentExecutor")
except ImportError as e:
    print(f"FAIL: from langchain.agents import AgentExecutor ({e})")

try:
    from langchain.agents.agent import AgentExecutor
    print("SUCCESS: from langchain.agents.agent import AgentExecutor")
except ImportError as e:
    print(f"FAIL: from langchain.agents.agent import AgentExecutor ({e})")

try:
    from langchain.agents import create_structured_chat_agent
    print("SUCCESS: from langchain.agents import create_structured_chat_agent")
except ImportError as e:
    print(f"FAIL: from langchain.agents import create_structured_chat_agent ({e})")

import langchain.agents
print(f"langchain.agents dir: {dir(langchain.agents)}")
