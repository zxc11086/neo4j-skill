# Neo4j CRUD Skill for Claude Code

连接本地 Neo4j 图数据库，在 Claude Code 中通过自然语言直接执行增删改查（CRUD）操作。

## 功能概述

- 执行任意 Cypher 查询
- 创建/查询/更新/删除节点
- 创建/查询/删除关系
- 查看数据库信息与 Schema
- 支持中文属性和返回值
- 自动处理 Windows 终端 UTF-8 编码

## 环境要求

- **Neo4j 数据库** >= 5.0（本地运行）
- **Python** >= 3.8
- **Python 包**: `neo4j`（`pip install neo4j`）

## 安装

### 1. 安装 Skill

将本仓库的 `skills/neo4j-crud/` 目录复制到 Claude Code 的 skills 目录：

```bash
cp -r skills/neo4j-crud ~/.claude/skills/neo4j-crud
```

或者在 Windows 下：

```powershell
xcopy /E /I skills\neo4j-crud %USERPROFILE%\.claude\skills\neo4j-crud
```

### 2. 安装 Python 依赖

```bash
pip install neo4j
```

### 3. 配置数据库连接

编辑 `~/.claude/skills/neo4j-crud/scripts/neo4j_config.json`：

```json
{
  "uri": "bolt://localhost:7687",
  "user": "neo4j",
  "password": "你的密码",
  "database": "neo4j"
}
```

也可以使用命令行配置：

```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py config bolt://localhost:7687 neo4j 你的密码 neo4j
```

### 4. 启动 Neo4j

确保本地 Neo4j 数据库正在运行。可以通过 Neo4j Desktop 或命令行启动：

```bash
neo4j start
```

## 使用方式

安装后，在 Claude Code 中直接使用自然语言操作数据库即可，Skill 会自动触发。例如：

- "帮我连接 Neo4j，看看数据库里有什么"
- "创建一个 Person 节点，name=张三, age=28"
- "查询所有 Person 节点"
- "创建 Alice 和 Bob 之间的 KNOWS 关系"
- "更新这个节点的 city 为上海"
- "删除这个节点"
- "执行 Cypher：MATCH (n)-[r]->(m) RETURN n.name, type(r), m"

### 触发词

以下关键词会自动触发此 Skill：`连接 Neo4j`、`建个节点`、`创建节点`、`创建测试数据`、`查询节点`、`更新数据`、`删除数据`、`Cypher 查询`、`创建关系`、`数据库里有什么`、`清空数据库`、`展示 schema`、`跑个查询` 等。

## 命令行直接使用

你也可以在终端直接调用脚本（不通过 Claude Code）：

```bash
# 查看数据库信息
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py info

# 创建节点
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py create Person '{"name": "Alice", "age": 30}'

# 查询所有节点
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py all Person

# 按属性查询
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py get Person name Alice

# 更新节点
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py update <node_id> '{"age": 31}'

# 删除节点
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py delete <node_id>

# 执行 Cypher 查询
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py query "MATCH (n) RETURN n LIMIT 10"
```

## 文件结构

```
~/.claude/skills/neo4j-crud/
├── SKILL.md                    # Skill 定义文件（名称、触发条件等）
├── scripts/
│   ├── neo4j_utils.py          # 核心脚本（Neo4jClient 类 + CLI 入口）
│   └── neo4j_config.json       # 数据库连接配置
└── evals/
    └── evals.json              # 评估用例
```

## 常见问题

**Q: 报错 `Unable to retrieve routing information`？**

A: 确认 Neo4j 数据库已启动，且 `neo4j_config.json` 中的 URI 和密码正确。

**Q: 中文显示乱码？**

A: 脚本已处理 Windows 终端 UTF-8 编码问题。如仍有问题，确保终端支持 UTF-8。

**Q: 如何修改默认数据库？**

A: 编辑 `neo4j_config.json` 中的 `database` 字段，默认为 `"neo4j"`。

## 安全提醒

- `delete` 命令使用 `DETACH DELETE`，会同时删除节点的所有关系
- 清空数据库操作不可逆，执行前会有确认提示
- 配置文件中的密码以明文存储，请注意文件权限
