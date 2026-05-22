---
name: neo4j-crud
description: >-
  连接本地 Neo4j 图数据库，支持增删改查（CRUD）操作。当用户提到需要操作 Neo4j 数据库、执行 Cypher 查询、创建/查询/更新/删除图数据节点或关系时，务必使用此 skill。
  具体触发场景包括但不限于：用户说"连接 Neo4j"、"查一下数据库里的数据"、"建个节点"、"创建几个测试数据"、"帮我查一下某个标签的节点"、
  "更新数据"、"删除数据"、"跑个 Cypher 查询"、"看看数据库里有什么"、"清空数据库"、"创建关系"、"展示 schema"等。
  使用此 skill 可以通过直接调用 Python 脚本来快速执行对本地 Neo4j 数据库的各种操作。
compatibility:
  - python
  - neo4j>=5.0
---

# Neo4j CRUD Skill

本 skill 提供对**本地 Neo4j 图数据库**的增删改查（CRUD）操作能力。通过 Python 驱动 (`neo4j` 包) 连接数据库，执行 Cypher 查询并对节点和关系进行各种操作。

## 前置条件

- Python 环境中已安装 `neo4j` 包（已安装）
- 本地 Neo4j 数据库正在运行（默认 `bolt://localhost:7687`）

## 工具脚本路径

所有操作都通过以下 Python 脚本来执行：

```
~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py
```

使用方式：
```bash
# 命令行模式
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py <command> [args...]

# 或在 Python 中导入使用
python -c "
from neo4j_utils import Neo4jClient
import json, sys
sys.path.insert(0, '~/.claude/skills/neo4j-crud/scripts')
"
```

## 连接配置

默认连接参数已在配置文件中设定

## 支持的命令

### 1. 执行任意 Cypher 查询: `query`

```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py query "MATCH (n:Person) RETURN n LIMIT 10"
```

带参数：
```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py query "MATCH (n:Person) WHERE n.name = \$name RETURN n" '{"name": "Alice"}'
```

**注意**: Cypher 查询中的参数变量需要用 `\$` 转义，参数通过 JSON 传入。

### 2. 创建节点: `create`

```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py create Person '{"name": "Alice", "age": 30}'
```

### 3. 查询节点: `get`

根据属性值查询节点：
```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py get Person name Alice
```

### 4. 查询所有节点: `all`

查询指定标签的所有节点（默认限制 100 条）：
```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py all Person
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py all Person 50
```

### 5. 更新节点: `update`

```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py update <node_id> '{"name": "Alice Smith", "age": 31}'
```

### 6. 删除节点: `delete`

```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py delete <node_id>
```

### 7. 创建关系

使用 Python 脚本方式创建关系（因为需要两个 node_id）：

```bash
python -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/neo4j-crud/scripts'))
from neo4j_utils import Neo4jClient
import json
client = Neo4jClient()
result = client.create_relationship('<from_node_id>', '<to_node_id>', 'KNOWS', {'since': 2020})
print(json.dumps(result, ensure_ascii=False, indent=2))
client.close()
"
```

### 8. 查询节点关系

```bash
python -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/neo4j-crud/scripts'))
from neo4j_utils import Neo4jClient
import json
client = Neo4jClient()
result = client.get_node_relationships('<node_id>')
print(json.dumps(result, ensure_ascii=False, indent=2))
client.close()
"
```

### 9. 删除关系

```bash
python -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/neo4j-crud/scripts'))
from neo4j_utils import Neo4jClient
import json
client = Neo4jClient()
result = client.delete_relationship('<rel_id>')
print(json.dumps(result, ensure_ascii=False, indent=2))
client.close()
"
```

### 10. 查看数据库信息: `info`

```bash
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py info
```

这会显示：连接状态、节点总数、关系总数、所有标签、所有关系类型。

### 11. 查看数据库 Schema

```bash
python -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/neo4j-crud/scripts'))
from neo4j_utils import Neo4jClient
import json
client = Neo4jClient()
result = client.show_schema()
print(json.dumps(result, ensure_ascii=False, indent=2))
client.close()
"
```

## CRUD 操作指南

### 创建 (Create)

创建节点时需要指定标签（Label）和属性（JSON 格式的字典）：

```bash
# 创建 Person 节点
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py create Person '{"name": "Bob", "age": 25, "city": "北京"}'

# 创建 Movie 节点
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py create Movie '{"title": "盗梦空间", "year": 2010}'
```

创建关系（连接两个已有的节点）：

```bash
python -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/neo4j-crud/scripts'))
from neo4j_utils import Neo4jClient
import json
client = Neo4jClient()
# 先找到两个节点
alice = client.get_node('Person', 'name', 'Alice')
bob = client.get_node('Person', 'name', 'Bob')
if alice['success'] and bob['success'] and alice['records'] and bob['records']:
    alice_id = alice['records'][0]['node_id']
    bob_id = bob['records'][0]['node_id']
    result = client.create_relationship(alice_id, bob_id, 'KNOWS', {'since': 2020})
    print(json.dumps(result, ensure_ascii=False, indent=2))
client.close()
"
```

### 读取 (Read)

```bash
# 查询所有 Person
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py all Person

# 按名称查询
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py get Person name Alice

# 自定义 Cypher 查询
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py query "MATCH (n:Person)-[r]->(m) RETURN n.name, type(r), m.title"
```

### 更新 (Update)

```bash
# 先查询找到 node_id
# 然后更新节点属性（可同时更新多个属性）
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py update <node_id> '{"age": 31, "city": "上海"}'
```

### 删除 (Delete)

```bash
# 删除指定节点（会同时删除其所有关系）
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py delete <node_id>

# 执行自定义删除（比如按条件删除）
python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py query "MATCH (n:Person) WHERE n.age > \$age DETACH DELETE n" '{"age": 100}'

# 删除关系
python -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/neo4j-crud/scripts'))
from neo4j_utils import Neo4jClient
import json
client = Neo4jClient()
result = client.delete_relationship('<rel_id>')
print(json.dumps(result, ensure_ascii=False, indent=2))
client.close()
"
```

### 清空数据库（谨慎！）

```bash
python -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/skills/neo4j-crud/scripts'))
from neo4j_utils import Neo4jClient
client = Neo4jClient()
result = client.execute_query('MATCH (n) DETACH DELETE n')
print(result)
client.close()
"
```

## 常见使用场景

| 场景 | 命令 |
|------|------|
| 查看数据库状态 | `python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py info` |
| 查看所有标签 | 查看 `info` 返回的 `labels` 字段 |
| 查询某标签所有节点 | `python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py all <Label>` |
| 创建测试数据 | `create` 命令 + `create_relationship` |
| 按条件查找 | 使用 `query` 写自定义 Cypher |
| 更新属性 | 先 `get` 找到 node_id，再 `update` |
| 删除数据 | 先查找到 node_id，再 `delete` |

## 注意事项

1. **脚本路径**: 使用 `os.path.expanduser('~')` 自动展开用户目录，跨平台兼容。如遇问题，可直接运行脚本文件 `python ~/.claude/skills/neo4j-crud/scripts/neo4j_utils.py <command>`
2. **参数转义**: 在 Cypher 查询中使用参数时，用 `\$` 代替 `$`（因为 bash 中 `$` 有特殊含义），参数值通过 JSON 字符串传入
3. **安全删除**: `delete` 使用 `DETACH DELETE`，会同时删除节点的所有关系
4. **重要操作确认**: 清空数据库等危险操作应使用 `MATCH (n) DETACH DELETE n` 显式执行，并在执行前告知用户
5. **结果格式**: 返回结果为 JSON 格式，包含 `success`（是否成功）、`records`（数据记录）、`count`（记录数）等字段
