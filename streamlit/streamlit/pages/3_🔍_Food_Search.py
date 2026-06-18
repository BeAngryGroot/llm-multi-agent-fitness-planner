import streamlit as st
import requests
from utils.api_client import FitnessAPI, init_session_state
from utils.footer import render_footer
from utils.sidebar import render_sidebar_disclaimer

# 配置页面
st.set_page_config(
    page_title="食品搜索 - AI健身规划师", page_icon="🔍", layout="wide"
)

# 初始化会话状态和侧边栏
init_session_state()

# 在侧边栏添加免责声明
render_sidebar_disclaimer()

st.header("🔍 食品数据库搜索")
st.markdown(
    "通过高级过滤选项搜索我们全面的USDA营养数据库。"
)


def display_search_results(results):
    """显示基础搜索结果"""
    for i, food in enumerate(results):
        with st.expander(
            f"🥘 {food.get('description', '未知食品')} - {food.get('brand_owner', '未知品牌')}"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**产品信息:**")
                st.write(f"**品牌:** {food.get('brand_name', 'N/A')}")
                st.write(f"**类别:** {food.get('food_category', 'N/A')}")
                st.write(
                    f"**份量:** {food.get('serving_size', 'N/A')} {food.get('serving_size_unit', '')}"
                )

                if food.get("ingredients"):
                    st.write(
                        f"**成分:** {food['ingredients'][:200]}{'...' if len(food['ingredients']) > 200 else ''}"
                    )

            with col2:
                nutrition = food.get("nutrition_enhanced", {})
                per_100g = nutrition.get("per_100g", {})

                if per_100g:
                    st.markdown("**每100克营养:**")

                    metrics_col1, metrics_col2 = st.columns(2)
                    with metrics_col1:
                        st.metric("热量", f"{per_100g.get('energy_kcal', 0)} 千卡")
                        st.metric("蛋白质", f"{per_100g.get('protein_g', 0)} 克")
                    with metrics_col2:
                        st.metric("碳水", f"{per_100g.get('carbs_g', 0)} 克")
                        st.metric("脂肪", f"{per_100g.get('total_fat_g', 0)} 克")

                    macro_breakdown = nutrition.get("macro_breakdown", {})
                    if macro_breakdown.get("primary_macro_category"):
                        st.write(
                            f"**主要宏量营养素:** {macro_breakdown['primary_macro_category'].replace('_', ' ').title()}"
                        )
                else:
                    st.warning("营养数据不可用")


def display_semantic_results(results):
    """显示语义搜索结果及相似度分数"""
    for i, food in enumerate(results):
        similarity_score = food.get("similarity_score", 0)
        score_color = (
            "🟢" if similarity_score > 0.8 else "🟡" if similarity_score > 0.7 else "🟠"
        )

        with st.expander(
            f"{score_color} {food.get('description', '未知食品')} - {food.get('brand_owner', '未知品牌')} (匹配度: {similarity_score:.1%})"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**产品信息:**")
                st.write(f"**品牌:** {food.get('brand_name', 'N/A')}")
                st.write(f"**类别:** {food.get('food_category', 'N/A')}")
                st.write(f"**份量:** {food.get('serving_size', 0)} 克")

                # 显示匹配内容
                if food.get("matched_content"):
                    st.markdown("**📄 AI匹配上下文:**")
                    with st.container():
                        st.caption(food["matched_content"])

            with col2:
                nutrition = food.get("nutrition_per_100g", {})

                st.markdown("**每100克营养:**")

                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    st.metric("热量", f"{nutrition.get('calories', 0):.0f} 千卡")
                    st.metric("蛋白质", f"{nutrition.get('protein_g', 0):.1f} 克")
                with metrics_col2:
                    st.metric("碳水", f"{nutrition.get('carbs_g', 0):.1f} 克")
                    st.metric("脂肪", f"{nutrition.get('fat_g', 0):.1f} 克")

                # 额外信息
                primary_macro = food.get("primary_macro_category", "unknown")
                if primary_macro != "unknown":
                    st.write(
                        f"**主要宏量营养素:** {primary_macro.replace('_', ' ').title()}"
                    )

                if food.get("is_high_protein"):
                    st.info("💪 高蛋白食品")


def display_hybrid_results(results):
    """显示混合搜索结果及分数分解"""
    for i, food in enumerate(results):
        hybrid_score = food.get("hybrid_score", 0)
        semantic_score = food.get("semantic_score", 0)
        traditional_score = food.get("traditional_score", 0)

        score_icon = (
            "🥇" if hybrid_score > 0.8 else "🥈" if hybrid_score > 0.6 else "🥉"
        )

        with st.expander(
            f"{score_icon} {food.get('description', '未知食品')} - {food.get('brand_owner', '未知品牌')} (分数: {hybrid_score:.2f})"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**产品信息:**")
                st.write(f"**品牌:** {food.get('brand_name', 'N/A')}")
                st.write(f"**类别:** {food.get('food_category', 'N/A')}")
                st.write(f"**份量:** {food.get('serving_size', 0)} 克")

                # 显示分数分解
                st.markdown("**搜索分数:**")
                score_col1, score_col2 = st.columns(2)
                with score_col1:
                    st.metric("🧠 AI分数", f"{semantic_score:.2f}")
                    st.metric("📝 文本分数", f"{traditional_score:.2f}")
                with score_col2:
                    st.metric("🎯 综合分数", f"{hybrid_score:.2f}")

            with col2:
                nutrition = food.get("nutrition_per_100g", {})

                st.markdown("**每100克营养:**")

                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    st.metric("热量", f"{nutrition.get('calories', 0):.0f} 千卡")
                    st.metric("蛋白质", f"{nutrition.get('protein_g', 0):.1f} 克")
                with metrics_col2:
                    st.metric("碳水", f"{nutrition.get('carbs_g', 0):.1f} 克")
                    st.metric("脂肪", f"{nutrition.get('fat_g', 0):.1f} 克")

                # 额外信息
                primary_macro = food.get("primary_macro_category", "unknown")
                if primary_macro != "unknown":
                    st.write(
                        f"**主要宏量营养素:** {primary_macro.replace('_', ' ').title()}"
                    )

                if food.get("is_high_protein"):
                    st.info("💪 高蛋白食品")

                nutrition_density = food.get("nutrition_density_score", 0)
                if nutrition_density > 0:
                    st.metric("🎯 营养密度", f"{nutrition_density:.1f}")


use_full_database = False
# 数据库可用性检查
if use_full_database:
    try:
        db_status = FitnessAPI.check_database_availability()
        if not db_status.get("full_database", {}).get("available", False):
            st.error(
                "❌ 完整USDA数据库不可用。仅可用采样数据。"
                "请先导入完整数据库或取消选择'使用完整USDA数据库'。"
            )
            use_full_database = False
        else:
            st.success(
                f"✅ 完整数据库可用，包含 {db_status['full_database']['document_count']:,} 种食品"
            )
    except Exception as e:
        st.warning(f"⚠️ 无法检查数据库可用性: {str(e)}")
        use_full_database = False
else:
    try:
        db_status = FitnessAPI.check_database_availability()
        sample_count = db_status.get("sample_database", {}).get("document_count", 0)
        if sample_count > 0:
            st.info(f"📋 使用示例数据库，包含 {sample_count:,} 种食品")
    except:
        pass

# 搜索方法选择
search_method = st.radio(
    "搜索方法:",
    ["🔍 基础搜索", "🧠 语义搜索", "🎯 高级过滤"],
    horizontal=True,
    help="基础: 简单的名称/品牌搜索。语义: AI驱动的自然语言搜索。高级: 基于营养的过滤。",
)

if search_method == "🔍 基础搜索":
    # 基础搜索界面
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "搜索食品:",
            placeholder="例如: 鸡胸肉, 希腊酸奶, 藜麦...",
            key="basic_query",
        )

    with col2:
        search_limit = st.selectbox("结果数量", [5, 10, 20], index=1)

    if st.button("🔍 搜索食品", use_container_width=True) and search_query:
        with st.spinner("搜索营养数据库..."):
            results = FitnessAPI.search_nutrition(search_query, search_limit)

            if results and results.get("results"):
                st.success(
                    f"找到 {results['results_found']} 个结果，搜索词: '{search_query}'"
                )
                display_search_results(results["results"])
            else:
                st.warning("未找到结果。请尝试其他搜索词！")

elif search_method == "🧠 语义搜索":
    # 语义搜索界面
    st.markdown("### 🧠 AI驱动语义搜索")
    st.info(
        "使用自然语言描述您要找的食物（例如：'高蛋白早餐食品' 或 '生酮饮食的低碳水零食'）"
    )

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        semantic_query = st.text_input(
            "描述您要找的食物:",
            placeholder="例如: 高蛋白低碳水早餐, 训练后恢复食品...",
            key="semantic_query",
        )

    with col2:
        similarity_threshold = st.slider(
            "匹配质量",
            min_value=0.5,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="更高的值 = 更精确的匹配",
        )

    with col3:
        semantic_limit = st.selectbox(
            "结果数量", [5, 10, 15, 20], index=1, key="semantic_limit"
        )

    # 饮食限制
    with st.expander("🥗 饮食限制（可选）"):
        col1, col2, col3 = st.columns(3)

        with col1:
            vegan = st.checkbox("纯素食")
        with col2:
            vegetarian = st.checkbox("素食")
        with col3:
            gluten_free = st.checkbox("无麸质")

    if st.button("🧠 语义搜索", use_container_width=True) and semantic_query:
        # 构建饮食限制列表
        restrictions = []
        if vegan:
            restrictions.append("vegan")
        if vegetarian:
            restrictions.append("vegetarian")
        if gluten_free:
            restrictions.append("gluten-free")

        with st.spinner("执行AI驱动搜索..."):
            try:
                api_url = FitnessAPI.get_api_url()
                request_data = {
                    "query": semantic_query,
                    "dietary_restrictions": restrictions,
                    "macro_goals": {},
                    "limit": semantic_limit,
                    "similarity_threshold": similarity_threshold,
                    "use_full_database": use_full_database,
                }

                response = requests.post(
                    f"{api_url}/v1/nutrition_search/search_nutrition_semantic/",
                    json=request_data,
                    timeout=30,
                )

                if response.status_code == 200:
                    results = response.json()
                    st.success(
                        f"在 {results['search_time_ms']}毫秒内找到 {results['results_found']} 个语义匹配结果"
                    )
                    display_semantic_results(results["results"])
                else:
                    st.error(f"搜索失败: {response.text}")

            except Exception as e:
                st.error(f"执行语义搜索时出错: {str(e)}")

elif search_method == "🎯 高级过滤":
    # 高级营养搜索
    st.markdown("### 🎯 营养搜索")
    st.info("搜索满足特定营养标准的食品")

    col1, col2 = st.columns([2, 1])

    with col1:
        advanced_query = st.text_input(
            "食品名称或描述:",
            placeholder="例如: 蛋白粉, 鸡肉, 燕麦...",
            key="advanced_query",
        )

    with col2:
        hybrid_limit = st.selectbox(
            "结果数量", [5, 10, 15, 20], index=1, key="hybrid_limit"
        )

    # 营养过滤
    st.markdown("#### 🥇 营养目标（每100克）")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        protein_min = st.number_input(
            "最小蛋白质 (克)", min_value=0.0, max_value=100.0, value=0.0, step=1.0
        )

    with col2:
        carbs_max = st.number_input(
            "最大碳水 (克)", min_value=0.0, max_value=100.0, value=100.0, step=1.0
        )

    with col3:
        calories_max = st.number_input(
            "最大热量", min_value=0, max_value=1000, value=1000, step=10
        )

    with col4:
        semantic_weight = st.slider(
            "AI与文本匹配权重",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="0 = 纯文本搜索, 1 = 纯AI搜索",
        )

    # 高级搜索的饮食限制
    with st.expander("🥗 饮食限制（可选）"):
        restrictions_text = st.text_input(
            "饮食限制（逗号分隔）:",
            placeholder="例如: vegan, gluten-free, dairy-free",
            help="输入用逗号分隔的饮食限制",
        )

    if st.button("🎯 高级搜索", use_container_width=True) and advanced_query:
        with st.spinner("执行高级营养搜索..."):
            try:
                api_url = FitnessAPI.get_api_url()

                params = {
                    "query": advanced_query,
                    "dietary_restrictions": restrictions_text,
                    "protein_min": protein_min,
                    "carbs_max": carbs_max,
                    "calories_max": calories_max,
                    "limit": hybrid_limit,
                    "semantic_weight": semantic_weight,
                    "use_full_database": use_full_database,
                }

                response = requests.get(
                    f"{api_url}/v1/nutrition_search/search_nutrition_hybrid/",
                    params=params,
                    timeout=30,
                )

                if response.status_code == 200:
                    results = response.json()
                    st.success(
                        f"找到 {results['results_found']} 种符合条件的食品"
                    )

                    # 显示搜索权重
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "AI搜索权重", f"{results['semantic_weight']:.0%}"
                        )
                    with col2:
                        st.metric(
                            "文本搜索权重", f"{results['traditional_weight']:.0%}"
                        )

                    display_hybrid_results(results["results"])
                else:
                    st.error(f"搜索失败: {response.text}")

            except Exception as e:
                st.error(f"执行高级搜索时出错: {str(e)}")

# 添加帮助部分
with st.expander("❓ 搜索帮助"):
    st.markdown(
        """
    ### 搜索类型:
    
    **🔍 基础搜索:** 传统的名称/品牌数据库搜索
    - 最适合: 查找您知道名称的特定食品
    - 示例: "希腊酸奶", "鸡胸肉"
    
    **🧠 语义搜索:** AI驱动的自然语言搜索
    - 最适合: 描述您想要的营养特性
    - 示例: "高蛋白早餐食品", "低碳水生酮零食"
    
    **🎯 高级过滤:** 结合AI搜索和特定营养标准
    - 最适合: 找到满足精确宏量营养素目标的食品
    - 示例: "蛋白粉" 要求 >20克蛋白质, <5克碳水
    
    ### 提示:
    - 使用具体术语获得更好的结果
    - 如果找不到所需内容，请尝试不同的搜索方法
    - 语义搜索最适合描述性查询
    - 高级过滤有助于缩小大型结果集
    """
    )

# 页脚
render_footer()
