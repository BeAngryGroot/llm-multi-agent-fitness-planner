# Contribution Guide - AI Fitness Planner

感谢你对本项目的贡献兴趣！本项目展示了基于 LangGraph 工作流的生产级 GenAI 模式。

## 🚀 快速设置

### 前置条件
- Docker 和 Docker Compose
- Git
- 阿里云 API key（用于 AI 功能）

### 开始使用
```bash
# 克隆并设置
git clone https://github.com/BeAngryGroot/llm-multi-agent-fitness-planner.git
cd llm-multi-agent-fitness-planner
cp .env.example .env

# 将你的 阿里云 API key 添加到 .env 文件
# 启动应用
make setup-demo
```

## 🎯 贡献方式

### **新 AI Agents**（最有价值）
添加专业的 agents 来增强工作流：

```python
@traceable(name="your_new_agent")
def your_new_agent(state: FitnessWorkflowState):
    """你的 agent 描述"""
    # 你的逻辑代码
    return {"new_data": result}
```

**想法：**
- **Supplement Advisor（补剂顾问）**: 基于证据的建议
- **Progress Tracker（进度追踪器）**: 监控结果并调整计划
- **Recovery Optimizer（恢复优化器）**: 睡眠和休息日规划

### **性能改进**
- 优化膳食规划（目前占执行时间的 83%）
- 改进向量搜索缓存
- 数据库查询优化

### **文档和示例**
- 教程笔记本
- 新用例示例
- 性能优化指南

## 📝 贡献流程

### 简单修改
对于小修复、文档或示例：
1. Fork 仓库
2. 进行修改
3. 提交 pull request

### 新功能
对于新 agents 或重大修改：
1. 先打开 issue 进行讨论
2. Fork 并创建 feature branch
3. 如果添加代码，请添加基本测试
4. 更新文档
5. 提交 pull request

## 🧪 测试

```bash
# 运行测试（可选但推荐）
make test

# 检查代码是否正常工作
make up
# 在 http://localhost:8526 测试你的修改
```

## 📋 代码标准

### 简单指南
- 对新 agents 使用 `@traceable` 装饰器
- 为新函数添加 docstrings
- 遵循现有代码模式
- 手动测试你的修改

### Commit 消息格式
```bash
feat: add supplement advisor agent
fix: resolve meal planning timeout
docs: add custom agent example
```

## 🤝 获取帮助

- **问题**: 打开 GitHub issue
- **想法**: 发起 GitHub discussion
- **Bug**: 创建 issue 并提供复现步骤

## 📊 当前性能（来自 LangSmith）
- **0% 错误率**（66 次运行）
- **~3 分钟**平均计划生成时间
- **$0.07**平均每次计划成本
- **膳食规划瓶颈**: 83% 的执行时间

特别欢迎能改进这些指标的贡献！

## 📄 许可证

通过贡献，您同意您的贡献将根据 MIT License 进行许可。

---

**感谢帮助改进这个项目！** 🎉

*本项目既是一个可用的健身规划器，也是 LangGraph 模式的教育示例。*