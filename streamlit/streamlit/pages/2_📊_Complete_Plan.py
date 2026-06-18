import streamlit as st
from utils.api_client import FitnessAPI, init_session_state
from utils.footer import render_footer
from utils.sidebar import render_sidebar_disclaimer

# 配置页面
st.set_page_config(
    page_title="完整计划 - AI健身规划师", page_icon="📊", layout="wide"
)

# 初始化会话状态和侧边栏
init_session_state()

# 在侧边栏添加免责声明
render_sidebar_disclaimer()

# 在侧边栏添加饮食计划天数选择器
with st.sidebar:
    st.subheader("🍽️ 饮食计划设置")
    meal_plan_days = st.selectbox(
        "饮食计划天数",
        options=[1, 2, 3, 4, 5, 6, 7],
        index=0,  # 默认1天
        help="选择要生成的饮食计划天数。天数越少，生成速度越快。",
    )

st.header("📊 完整健身计划")

if not st.session_state.get("current_profile") and not FitnessAPI.get_profile(
    st.session_state.user_id
):
    st.warning("⚠️ 请先创建您的个人资料！")
    if st.button("👤 前往资料设置"):
        st.switch_page("pages/1_👤_Profile_Setup.py")
    st.stop()

st.markdown(
    "使用我们先进的LangGraph工作流生成您完整的个性化健身计划，包括饮食和训练计划！"
)

# 计划配置
col1, col2 = st.columns(2)

with col1:
    st.subheader("🍽️ 饮食计划设置")
    st.info(
        f"将为您生成 {meal_plan_days} 天的饮食计划"
    )

with col2:
    st.subheader("💪 训练设置")

    # 获取当前资料显示训练频率
    current_profile = st.session_state.get("current_profile") or FitnessAPI.get_profile(
        st.session_state.user_id
    )
    if current_profile and current_profile.get("workout_frequency"):
        workout_freq = current_profile["workout_frequency"]
        st.info(f"训练频率: {workout_freq} 天/周")
    else:
        st.info("训练频率在您的资料设置中配置")

# AI模型设置
st.sidebar.subheader("🤖 AI模型设置")
use_o3_mini = st.sidebar.checkbox(
    "使用高级推理模型（速度较慢，效果更好）", value=True
)

use_full_database = False
# 数据库可用性检查（如果启用完整数据库）
if use_full_database:
    try:
        db_status = FitnessAPI.check_database_availability()
        if not db_status.get("full_database", {}).get("available", False):
            st.error(
                "❌ 完整USDA数据库不可用。仅可用采样数据。"
                "请先导入完整数据库或取消选择'使用完整USDA数据库'。"
            )
            use_full_database = False
    except Exception as e:
        st.warning(f"⚠️ 无法检查数据库可用性: {str(e)}")
        use_full_database = False

# 生成按钮
if st.button("🚀 生成完整计划", use_container_width=True, type="primary"):
    with st.spinner("🤖 LangGraph工作流正在编排您的计划..."):
        # 显示进度步骤
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("🔄 初始化工作流...")
        progress_bar.progress(20)

        result = FitnessAPI.generate_langgraph_plan(
            st.session_state.user_id, use_o3_mini, use_full_database, meal_plan_days
        )

        if result:
            status_text.text("✅ 工作流完成！")
            progress_bar.progress(100)

    if result:
        st.success("✅ 您的完整健身计划已准备好！")

        # 显示工作流执行步骤
        if result.get("execution_steps"):
            with st.expander("🔍 工作流执行步骤", expanded=False):
                for i, step in enumerate(result["execution_steps"], 1):
                    st.write(f"{i}. {step}")

        # 显示任何错误
        if result.get("errors"):
            st.warning("⚠️ 生成过程中出现一些问题:")
            for error in result["errors"]:
                st.write(f"- {error}")

        # 显示总结
        if result.get("summary"):
            st.subheader("🎯 您的个性化计划总结")
            st.markdown(result["summary"])

        # 饮食计划部分
        if result.get("meal_plan"):
            st.subheader("🍽️ 饮食计划")
            meal_plan = result["meal_plan"]

            # 显示计划名称和概述
            if meal_plan.get("plan_name"):
                st.markdown(f"**{meal_plan['plan_name']}**")

            if meal_plan.get("target_macros"):
                st.markdown("**每日目标:**")

                col1, col2, col3, col4 = st.columns(4)

                macros = meal_plan["target_macros"]
                with col1:
                    st.metric("热量", f"{macros.get('calories', 0):,.0f}")
                with col2:
                    st.metric("蛋白质", f"{macros.get('protein_g', 0):.0f}克")
                with col3:
                    st.metric("碳水", f"{macros.get('carbs_g', 0):.0f}克")
                with col4:
                    st.metric("脂肪", f"{macros.get('fat_g', 0):.0f}克")

            # 以结构化格式显示每日饮食计划
            if meal_plan.get("daily_plans"):
                plan_days = len(meal_plan["daily_plans"])
                with st.expander(
                    f"📋 {plan_days}天详细饮食计划", expanded=True
                ):
                    for day_plan in meal_plan["daily_plans"]:
                        day_name = (
                            day_plan.get("day_name")
                            or f"第{day_plan.get('day', '?')}天"
                        )
                        st.markdown(f"### {day_name}")

                        # 显示当天的餐食
                        for meal in day_plan.get("meals", []):
                            st.markdown(f"**{meal.get('meal_name', '餐食')}**")

                            # 显示餐食中的食物
                            for food in meal.get("foods", []):
                                st.write(
                                    f"• {food.get('food_name', '食物')} - {food.get('portion', 'N/A')} "
                                    f"({food.get('calories', 0):.0f} 卡, "
                                    f"{food.get('protein_g', 0):.1f}克蛋白质)"
                                )

                            # 显示餐食总计
                            meal_macros = meal.get("total_macros", {})
                            if meal_macros:
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.caption(
                                        f"🔥 {meal_macros.get('calories', 0):.0f} 卡"
                                    )
                                with col2:
                                    st.caption(
                                        f"🥩 {meal_macros.get('protein_g', 0):.1f}克"
                                    )
                                with col3:
                                    st.caption(
                                        f"🍞 {meal_macros.get('carbs_g', 0):.1f}克"
                                    )
                                with col4:
                                    st.caption(f"🥑 {meal_macros.get('fat_g', 0):.1f}克")

                            # 准备说明
                            if meal.get("preparation_notes"):
                                st.caption(f"📝 {meal['preparation_notes']}")

                            st.markdown("---")

                        # 每日总计
                        daily_totals = day_plan.get("daily_totals", {})
                        if daily_totals:
                            st.markdown("**每日总计:**")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric(
                                    "热量", f"{daily_totals.get('calories', 0):.0f}"
                                )
                            with col2:
                                st.metric(
                                    "蛋白质",
                                    f"{daily_totals.get('protein_g', 0):.1f}克",
                                )
                            with col3:
                                st.metric(
                                    "碳水", f"{daily_totals.get('carbs_g', 0):.1f}克"
                                )
                            with col4:
                                st.metric("脂肪", f"{daily_totals.get('fat_g', 0):.1f}克")

                        st.markdown("---")

            # 显示关键原则和购物建议
            col1, col2 = st.columns(2)

            with col1:
                if meal_plan.get("key_principles"):
                    st.markdown("**🎯 关键原则:**")
                    for principle in meal_plan["key_principles"]:
                        st.write(f"• {principle}")

            with col2:
                if meal_plan.get("shopping_tips"):
                    st.markdown("**🛒 购物建议:**")
                    for tip in meal_plan["shopping_tips"]:
                        st.write(f"• {tip}")

            # 显示元数据
            if meal_plan.get("available_foods_count"):
                st.caption(
                    f"📊 计划使用数据库中的 {meal_plan['available_foods_count']} 种可用食品创建"
                )

        # 训练计划部分
        if result.get("workout_plan"):
            st.subheader("💪 训练计划")
            workout_plan = result["workout_plan"]

            # 显示计划名称和概述
            if workout_plan.get("plan_name"):
                st.markdown(f"**{workout_plan['plan_name']}**")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("训练风格", workout_plan.get("training_style", "N/A"))
            with col2:
                st.metric("分化类型", workout_plan.get("split_type", "N/A"))
            with col3:
                st.metric("每周天数", workout_plan.get("days_per_week", "N/A"))
            with col4:
                duration = workout_plan.get("duration_minutes", "N/A")
                st.metric("时长", f"{duration} 分钟" if duration != "N/A" else "N/A")

            # 以结构化格式显示周训练计划
            if workout_plan.get("weekly_schedule"):
                with st.expander("🏋️‍♂️ 周训练计划", expanded=True):
                    for workout_day in workout_plan["weekly_schedule"]:
                        day_name = (
                            workout_day.get("day_name")
                            or f"第{workout_day.get('day', '?')}天"
                        )
                        st.markdown(
                            f"### {day_name} - {workout_day.get('focus', '训练')}"
                        )

                        # 热身
                        if workout_day.get("warm_up"):
                            st.markdown("**🔥 热身:**")
                            for warmup in workout_day["warm_up"]:
                                st.write(f"• {warmup}")

                        # 主要训练动作
                        if workout_day.get("exercises"):
                            st.markdown("**💪 训练动作:**")

                            # 创建类似表格的显示
                            ex_col1, ex_col2, ex_col3, ex_col4 = st.columns(
                                [3, 1, 1, 2]
                            )

                            with ex_col1:
                                st.write("**动作**")
                            with ex_col2:
                                st.write("**组数**")
                            with ex_col3:
                                st.write("**次数**")
                            with ex_col4:
                                st.write("**休息**")

                            st.markdown("---")

                            for exercise in workout_day["exercises"]:
                                ex_col1, ex_col2, ex_col3, ex_col4 = st.columns(
                                    [3, 1, 1, 2]
                                )

                                with ex_col1:
                                    st.write(exercise.get("exercise_name", "动作"))
                                    if exercise.get("notes"):
                                        st.caption(f"💡 {exercise['notes']}")
                                with ex_col2:
                                    st.write(str(exercise.get("sets", "N/A")))
                                with ex_col3:
                                    st.write(str(exercise.get("reps", "N/A")))
                                with ex_col4:
                                    rest_time = exercise.get("rest_seconds", 0)
                                    if rest_time >= 60:
                                        st.write(
                                            f"{rest_time // 60}分 {rest_time % 60}秒"
                                        )
                                    else:
                                        st.write(f"{rest_time}秒")

                        # 放松
                        if workout_day.get("cool_down"):
                            st.markdown("**🧘 放松:**")
                            for cooldown in workout_day["cool_down"]:
                                st.write(f"• {cooldown}")

                        # 预计时长
                        if workout_day.get("estimated_duration"):
                            st.caption(
                                f"⏱️ 预计时长: {workout_day['estimated_duration']} 分钟"
                            )

                        st.markdown("---")

            # 显示额外的训练计划信息
            col1, col2 = st.columns(2)

            with col1:
                if workout_plan.get("key_principles"):
                    st.markdown("**🎯 训练原则:**")
                    for principle in workout_plan["key_principles"]:
                        st.write(f"• {principle}")

                if workout_plan.get("progression_strategy"):
                    st.markdown("**📈 进阶策略:**")
                    st.write(workout_plan["progression_strategy"])

            with col2:
                if workout_plan.get("equipment_needed"):
                    st.markdown("**🛠️ 所需设备:**")
                    for equipment in workout_plan["equipment_needed"]:
                        st.write(f"• {equipment}")

        # 计划元数据
        if result.get("generated_at"):
            st.caption(f"计划生成时间: {result['generated_at']}")

        st.balloons()

# 页脚
render_footer()
