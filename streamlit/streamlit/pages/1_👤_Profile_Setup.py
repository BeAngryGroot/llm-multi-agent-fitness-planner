import streamlit as st
from datetime import datetime
from utils.api_client import FitnessAPI, init_session_state
from utils.footer import render_footer
from utils.sidebar import render_sidebar_disclaimer


# 单位转换函数
def kg_to_lbs(kg):
    """将公斤转换为磅"""
    return kg * 2.20462


def lbs_to_kg(lbs):
    """将磅转换为公斤"""
    return lbs / 2.20462


def cm_to_ft_in(cm):
    """将厘米转换为英尺和英寸"""
    total_inches = cm / 2.54
    feet = int(total_inches // 12)
    inches = total_inches % 12
    return feet, inches


def ft_in_to_cm(feet, inches):
    """将英尺和英寸转换为厘米"""
    total_inches = feet * 12 + inches
    return total_inches * 2.54


# 配置页面
st.set_page_config(
    page_title="个人资料设置 - AI健身规划师", page_icon="👤", layout="wide"
)

# 初始化会话状态和侧边栏
init_session_state()

# 在侧边栏添加免责声明
render_sidebar_disclaimer()

st.header("👤 用户资料设置")
st.markdown("让我们创建您的个性化健身档案！")

# 首先测试API连接
current_api_url = FitnessAPI.get_api_url()
connection_test = FitnessAPI.test_connection()
if not connection_test["success"]:
    st.error(f"❌ 无法连接到API服务器：{current_api_url}")
    st.write(f"**错误信息：** {connection_test.get('error', '未知错误')}")
    st.write(f"**尝试连接的URL：** {connection_test.get('url', 'N/A')}")

    st.markdown(
        """
    **故障排除：**
    1. 确保FastAPI服务器在正确的端口上运行
    2. 检查API URL是否正确（使用侧边栏中的API设置）
    3. 验证网络连接是否正常
    4. 尝试API测试页面获取更多详细信息
    """
    )

    if st.button("🔄 重新连接"):
        st.rerun()
    st.stop()
else:
    st.success(f"✅ 已成功连接到API服务器：{current_api_url}")

# 检查是否存在现有资料
with st.spinner("检查现有资料..."):
    existing_profile = FitnessAPI.get_profile(st.session_state.user_id)

if existing_profile:
    st.success("✅ 找到您的资料！您可以在下方更新它。")
    st.session_state.current_profile = existing_profile
else:
    st.info(
        "🆕 未找到现有资料。让我们创建您的第一个资料，开始个性化健身规划！"
    )

with st.form("profile_form"):
    st.subheader("基本信息")

    # 单位系统选择
    unit_system = st.selectbox(
        "单位系统",
        ["英制 (磅/英尺)", "公制 (公斤/厘米)"],
        index=0,  # 默认英制
        help="选择您偏好的输入单位系统。数据将自动转换为公制进行计算。",
    )

    is_metric = unit_system.startswith("公制")

    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input(
            "年龄", min_value=16, max_value=80, value=existing_profile.get("age", 35)
        )

        if is_metric:
            weight_input = st.number_input(
                "体重 (公斤)",
                min_value=40.0,
                max_value=200.0,
                value=existing_profile.get("weight", 70.0),
                step=0.5,
            )
            weight_kg = weight_input
        else:
            # 将现有体重从公斤转换为磅显示
            existing_weight_lbs = kg_to_lbs(existing_profile.get("weight", 80.0))
            weight_input = st.number_input(
                "体重 (磅)",
                min_value=88.0,  # ~40公斤
                max_value=440.0,  # ~200公斤
                value=existing_weight_lbs,
                step=1.0,
            )
            weight_kg = lbs_to_kg(weight_input)

        activity_level = st.selectbox(
            "活动水平",
            ["sedentary", "light", "moderate", "active", "very_active"],
            index=["sedentary", "light", "moderate", "active", "very_active"].index(
                existing_profile.get("activity_level", "moderate")
            ),
            format_func=lambda x: {
                "sedentary": "久坐",
                "light": "轻度活动",
                "moderate": "中度活动",
                "active": "高度活动",
                "very_active": "极高活动"
            }[x]
        )

    with col2:
        if is_metric:
            height_input = st.number_input(
                "身高 (厘米)",
                min_value=140.0,
                max_value=220.0,
                value=existing_profile.get("height", 182.0),
                step=0.5,
            )
            height_cm = height_input
        else:
            # 将现有身高从厘米转换为英尺和英寸显示
            existing_height_cm = existing_profile.get("height", 182.0)
            existing_feet, existing_inches = cm_to_ft_in(existing_height_cm)

            col_ft, col_in = st.columns(2)
            with col_ft:
                height_feet = st.number_input(
                    "身高 (英尺)",
                    min_value=4,
                    max_value=7,
                    value=int(existing_feet),
                    step=1,
                )
            with col_in:
                height_inches = st.number_input(
                    "身高 (英寸)",
                    min_value=0.0,
                    max_value=11.9,
                    value=existing_inches,
                    step=0.1,
                )
            height_cm = ft_in_to_cm(height_feet, height_inches)

        fitness_goal = st.selectbox(
            "主要目标",
            ["cut", "bulk", "maintenance", "recomp"],
            index=["cut", "bulk", "maintenance", "recomp"].index(
                existing_profile.get("fitness_goal", "maintenance")
            ),
            format_func=lambda x: {
                "cut": "减脂",
                "bulk": "增肌",
                "maintenance": "维持",
                "recomp": "重组"
            }[x]
        )

        # 在侧边栏添加目标说明
        with st.sidebar:
            with st.expander("ℹ️ 主要目标指南"):
                st.markdown(
                    """
                **减脂** 🔥
                - 在保留肌肉的同时减少脂肪
                - 20%的热量缺口
                - 专注于瘦蛋白摄入
                - 更快看到明显效果
                
                **增肌** 💪
                - 增加肌肉和体重
                - 20%的热量盈余
                - 强调蛋白质摄入
                - 预期会有一些脂肪增长
                
                **维持** ⚖️
                - 维持当前体重
                - 平衡的营养方法
                - 可持续的长期策略
                - 适合初学者
                
                **重组** 🎯
                - 同时增肌和减脂
                - 维持热量摄入
                - 高蛋白饮食
                - 变化较慢但质量更高
                """
                )
                st.info(
                    "💡 **提示：** 重组最适合初学者或休息后重返健身的人群！"
                )

        workout_frequency = st.number_input(
            "每周训练天数",
            min_value=1,
            max_value=7,
            value=existing_profile.get("workout_frequency", 3),
        )

    st.subheader("偏好与限制")

    allergies = st.multiselect(
        "过敏/不耐受",
        ["dairy", "gluten", "nuts", "shellfish", "eggs", "soy"],
        default=existing_profile.get("allergies", []),
        format_func=lambda x: {
            "dairy": "乳制品",
            "gluten": "麸质",
            "nuts": "坚果",
            "shellfish": "贝类",
            "eggs": "鸡蛋",
            "soy": "大豆"
        }[x]
    )

    dietary_preferences = st.multiselect(
        "饮食偏好",
        ["vegetarian", "vegan", "keto", "paleo", "mediterranean", "low_carb"],
        default=existing_profile.get("dietary_preferences", []),
        format_func=lambda x: {
            "vegetarian": "素食",
            "vegan": "纯素食",
            "keto": "生酮",
            "paleo": "原始人饮食",
            "mediterranean": "地中海饮食",
            "low_carb": "低碳水"
        }[x]
    )

    equipment_available = st.multiselect(
        "可用设备",
        [
            "bodyweight",
            "dumbbells",
            "barbell",
            "resistance_bands",
            "pull_up_bar",
            "gym_access",
        ],
        default=existing_profile.get(
            "equipment_available", ["bodyweight", "dumbbells"]
        ),
        format_func=lambda x: {
            "bodyweight": "徒手训练",
            "dumbbells": "哑铃",
            "barbell": "杠铃",
            "resistance_bands": "弹力带",
            "pull_up_bar": "单杠",
            "gym_access": "健身房"
        }[x]
    )

    # 为使用英制单位的用户显示转换信息
    if not is_metric:
        st.info(
            f"📊 将发送到API的值：体重: {weight_kg:.1f} 公斤, 身高: {height_cm:.1f} 厘米"
        )

    submitted = st.form_submit_button("💾 保存资料", use_container_width=True)

    if submitted:
        profile_data = {
            "user_id": st.session_state.user_id,
            "age": age,
            "weight": weight_kg,  # 始终发送公制单位到API
            "height": height_cm,  # 始终发送公制单位到API
            "activity_level": activity_level,
            "fitness_goal": fitness_goal,
            "workout_frequency": workout_frequency,
            "allergies": allergies,
            "dietary_preferences": dietary_preferences,
            "equipment_available": equipment_available,
            "created_at": (
                datetime.now().isoformat()
                if not existing_profile
                else existing_profile.get("created_at")
            ),
        }

        with st.spinner("保存资料并计算营养需求..."):
            result = FitnessAPI.create_profile(profile_data)

            if result:
                st.success("✅ 资料保存成功！")
                st.session_state.profile_created = True
                st.session_state.current_profile = result

                # 显示计算的宏量营养素目标
                st.subheader("🎯 您的计算目标")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("每日热量", f"{result.get('target_calories', 0):,}")

                with col2:
                    st.metric("蛋白质", f"{result.get('target_protein_g', 0)}克")

                with col3:
                    st.metric("碳水化合物", f"{result.get('target_carbs_g', 0)}克")

                with col4:
                    st.metric("脂肪", f"{result.get('target_fat_g', 0)}克")

                st.balloons()

# 页脚
render_footer()
