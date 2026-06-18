import streamlit as st
from datetime import datetime

def render_footer():
    """渲染应用程序页脚"""
    
    # 添加间距
    st.markdown("---")
    
    # 页脚部分
    st.markdown(
        """
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 10px;">
            <hr style="margin: 20px 0; border-color: #dee2e6;">
            <div style="text-align: center;">
                <p style="color: #495057; margin-bottom: 10px; font-size: 16px;">
                    🚀 <strong>AI健身规划师</strong> 
                </p>
                <p style="color: #6c757d; font-size: 14px; margin-bottom: 10px;">
                    基于LangChain智能体的个性化健身与营养规划系统
                </p>
                <p style="color: #6c757d; font-size: 12px; margin-bottom: 0;">
                    技术支持: FastAPI • MongoDB • LangChain • 阿里云通义千问 • Streamlit<br>
                    © {year} AI Fitness Planner. 演示应用 - 非商业用途。
                </p>
            </div>
        </div>
        """.format(year=datetime.now().year),
        unsafe_allow_html=True,
    )