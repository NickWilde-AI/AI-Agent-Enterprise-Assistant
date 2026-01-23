import streamlit as st
import sys
import traceback
from pathlib import Path

# 跨平台添加项目根目录到 sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.agent.agent_workflow import build_agent
# from langchain_community.callbacks import StreamlitCallbackHandler # 暂时禁用以避免兼容性问题

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
    - **RAG 知识检索**: 查阅内部文档/制度/排期表
    - **数据库查询**: 查询员工信息、报销记录
    - **业务操作**: 创建工单、撰写邮件
    """)
    
    st.divider()
    
    st.markdown("### 📊 系统状态")
    st.success("知识库索引: 在线")
    st.success("MCP 服务: 已连接")
    st.success("DeepSeek 模型: 就绪")
    
    st.divider()
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# 3. 主界面
st.title("🤖 企业智能知识助理")
st.caption("基于 DeepSeek-V3 + RAG + MCP 工具链驱动")

# 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "你好！我是你的企业智能助理。我可以帮你查询报销、项目进度，或者回答关于公司制度的问题。\n\n**试着问我：**\n- *戴飞翔负责什么任务？*\n- *张三上个月报销了多少钱？*\n- *请假制度是怎样的？*"}
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
                
                # 运行 Agent
                # 注意：这里我们移除了 callbacks 参数，因为 StreamlitCallbackHandler 与部分组件有冲突
                result = agent_executor.invoke({"input": prompt})
                output_text = result["output"]
                
                st.write(output_text)
                
                # 保存助手回复
                st.session_state.messages.append({"role": "assistant", "content": output_text})
                
            except Exception as e:
                st.error("发生错误，请检查日志或重试。")
                st.code(traceback.format_exc())
