import streamlit as st


def render_sidebar_disclaimer():
    """在侧边栏渲染免责声明，默认关闭"""

    with st.sidebar:
        with st.expander("⚠️ 重要免责声明", expanded=False):
            st.markdown(
                """
                **仅供演示目的**
                
                本应用程序仅用于教育和演示目的。
                本系统生成的饮食计划、营养建议和训练推荐**不构成医疗或专业健康建议**。
                
                **在开始任何新的饮食或锻炼计划之前，请咨询合格的医疗专业人士、注册营养师
                或认证健身教练。** 个人结果可能有所不同，本工具不应取代专业医疗指导。
                """,
                help="本免责声明适用于本应用生成的所有内容。",
            )
