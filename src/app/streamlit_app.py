import streamlit as st
import sys
import traceback
from pathlib import Path

# 跨平台添加项目根目录到 sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.agent.agent_workflow import build_agent
# from langchain_community.callbacks import StreamlitCallbackHandler # 暂时禁用以避免兼容性问题
import nest_asyncio
nest_asyncio.apply()

# 1. 页面配置
st.set_page_config(
    page_title="企业智能助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 侧边栏：功能与状态
with st.sidebar:
    st.title("🧰 控制面板")
    
    st.markdown("### 🌟 核心能力")
    st.markdown("""
    - **RAG 下一代智能问答**:
      能够深度理解海量复杂文档（Word, PDF, Excel），让您像聊天一样获取精准信息。
    - **数据库精准查询**:
      实时连接企业 HR 与财务系统，秒级查询人员与报销数据。
    - **Agent 自主业务办理**:
      一句指令，自动完成工单创建、邮件撰写等复杂任务。
    """)
    
    st.divider()
    
    st.markdown("### 📂 当前已加载知识库")
    try:
        data_dir = ROOT / "data"
        files = [f.name for f in data_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
        if files:
            for f in files:
                st.caption(f"📄 {f}")
        else:
            st.warning("暂无文档")
    except Exception as e:
        st.error(f"无法读取文档列表: {e}")

    st.divider()
    
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# 3. 主界面
st.title("📚 企业智能文档理解专家")
st.caption("深度解析 Word / Excel / PDF | 基于 DeepSeek-V3 驱动")

# 初始化聊天历史
# 初始化聊天历史
if "messages" not in st.session_state:
    # 动态获取文件名列表作为建议
    try:
        data_dir = ROOT / "data"
        files = [f.name for f in data_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
        if not files:
            files = ["暂无文档"]
    except Exception:
        files = ["文档读取失败"]

    # 生成建议问题列表
    suggestions = [f"- *请总结 {f} 的核心内容*" for f in files[:3]] # 取前3个作为示例
    
    suggestion_text = "\n".join(suggestions)

    initial_msg = (
        "你好！我是你的企业智能文档专家。我已经深度阅读了知识库中的所有文件。\n\n"
        "你可以让我帮你总结文档、提取数据或回答细节问题。**试着问我：**\n\n"
        f"{suggestion_text}"
    )

    st.session_state["messages"] = [
        {"role": "assistant", "content": initial_msg}
    ]

# 显示历史消息
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 4. 处理用户输入
if prompt := st.chat_input(placeholder="请输入你的业务问题..."):
    # 显示用户消息
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 执行 Agent 逻辑
    with st.chat_message("assistant"):
        with st.spinner("正在思考与查询中..."):
            try:
                # 构建 Agent (每次构建以确保状态清新)
                agent_executor = build_agent()
                
                # 转换历史消息为 LangChain 格式
                from langchain_core.messages import HumanMessage, AIMessage
                chat_history = []
                # 排除最新的这一个用户提问，因为它通过 input 参数传递
                for msg in st.session_state.messages[:-1]:
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        chat_history.append(AIMessage(content=msg["content"]))

                # 运行 Agent
                # 注意：这里我们移除了 callbacks 参数，因为 StreamlitCallbackHandler 与部分组件有冲突
                result = agent_executor.invoke({
                    "input": prompt,
                    "chat_history": chat_history
                })
                output_text = result["output"]
                
                st.write(output_text)
                
                # 保存助手回复
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                
            except Exception as e:
                st.error("发生错误，请检查日志或重试。")
                st.code(traceback.format_exc())
