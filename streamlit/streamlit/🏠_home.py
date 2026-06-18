import streamlit as st
from utils.api_client import init_session_state
from utils.footer import render_footer
from utils.sidebar import render_sidebar_disclaimer

# 配置Streamlit页面
st.set_page_config(
    page_title="AI健身规划师",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化会话状态和侧边栏
init_session_state()

# 在侧边栏添加免责声明
render_sidebar_disclaimer()

# 主内容
st.title("🏋️‍♂️ AI健身规划师")
st.markdown("### 基于LangChain智能体的个性化饮食与健身计划")

st.markdown(
    """
本应用使用**LangChain智能体**为您量身定制个性化的健身和营养计划。

### 🤖 工作原理：

1. **个人资料管理智能体** - 分析您的目标、身体指标和偏好
2. **饮食规划智能体** - 使用USDA食品数据库创建详细的营养计划
3. **健身规划智能体** - 设计全面的训练计划，包含结构化练习
4. **总结智能体** - 将所有内容整合为可操作的指导和激励性见解

### 🎯 功能特点：
- **个性化宏量营养素计算** - 根据您的目标（减脂/增肌/维持）
- **智能食品推荐** - 从精选USDA品牌食品中进行向量搜索
- **结构化饮食计划** - 详细的食物、份量和每日宏量营养素追踪
- **完整健身方案** - 包含训练动作、组数、次数和进阶策略
- **实时计划生成** - 使用阿里云通义千问驱动的智能体进行结构化输出

### 🚀 开始使用：
1. 使用侧边栏导航设置您的个人资料
2. 生成完整的健身计划
3. 跟随个性化建议开始您的健康之旅

---
**技术支持：** FastAPI + MongoDB + LangChain + Streamlit
"""
)

# 数据库快速统计
st.subheader("📈 平台统计")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("可用食品", "5000+", "演示数据集")

with col2:
    st.metric("向量搜索", "✅", "已启用")

with col3:
    st.metric("饮食偏好", "6+", "素食、纯素食、生酮等")

with col4:
    st.metric(
        "健身设备选项", "6+", "哑铃、杠铃、徒手训练等"
    )

with col5:
    st.metric("AI智能体", "4个", "结构化输出")

# 页脚
render_footer()
