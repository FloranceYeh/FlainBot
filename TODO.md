# FlainBot 项目规划

## 目标

构建一个基于图和节点的机器人应用框架。消息或输入数据通过可组合节点处理，LLM 只是可选处理节点之一，不是项目启动或运行的前提。

## 已完成

- 定义端口化 `Graph`、节点接口和 `GraphExecutor`。
- 支持 DAG 执行、依赖排序、端口连接和环检测。
- 实现 Web Chat 边界节点：`ChatInputNode`、`ChatOutputNode`。
- 实现 OpenAI / Anthropic provider 节点，作为可选处理节点。
- 支持从前端保存的 graph config 构建并执行运行时图。
- 实现单 HTML 前端：Planner 和 Chat 在同一个 `index.html` 内动态切换。
- 实现节点画布、端口连线、节点属性编辑、Python 示例代码生成。
- 实现 Web Chat API：`GET/POST /api/graph`、`POST /api/chat`。
- 新增跨平台启动脚本 `start.py`，启动不绑定任何 LLM provider。
- 增加单元测试覆盖图执行、provider 节点、graph config、web chat 服务和启动脚本。

## 下一步

- 增加非 LLM 示例节点，例如：
  - 指令解析节点
  - 文本过滤节点
  - 消息分段节点
  - 条件路由节点
- 前端支持从后端加载当前 graph config，避免刷新后丢失当前服务端图。
- Chat 在空图或缺少 `chat_output` 时返回前端可读的错误提示。
- 增加图配置校验，保存前提示缺失输入/输出边界、断开的必需端口和重复节点 ID。
- 增加节点类型注册机制，避免 `config.py` 中硬编码所有节点类型。

## 中期扩展

- 节点级日志和运行轨迹追踪。
- 图执行结果可视化，显示每个节点输入、输出和耗时。
- 持久化 graph config 到本地文件。
- 支持更多输入/输出适配器，例如 CLI、HTTP webhook、聊天平台。
- 支持插件式节点包。

## 暂不做

- 插件市场。
- 多用户权限系统。
- 分布式执行。
- 复杂生产部署管理。
