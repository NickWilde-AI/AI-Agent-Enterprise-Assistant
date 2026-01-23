from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents.structured_chat.output_parser import StructuredChatOutputParser
from langchain.agents.format_scratchpad import format_log_to_str
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
load_dotenv(ROOT / ".env")

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
llm_model = os.getenv("OPENAI_MODEL", "deepseek-chat")

llm = ChatOpenAI(
    model=llm_model,
    temperature=0.2,
    api_key=api_key,
    base_url=api_base,
)

output_parser = StructuredChatOutputParser()
prompt = ChatPromptTemplate.from_messages([
    ("system", "Test {tool_names} {tools} {format_instructions}"),
    ("human", "{input}"),
    ("assistant", "{agent_scratchpad}"),
]).partial(format_instructions=output_parser.get_format_instructions(), tool_names="test", tools="test")

print(f"LLM type: {type(llm)}")
print(f"Prompt type: {type(prompt)}")
print(f"Parser type: {type(output_parser)}")

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_log_to_str(x["intermediate_steps"]),
    }
    | prompt
    | llm
    | output_parser
)

print("Agent built successfully")
