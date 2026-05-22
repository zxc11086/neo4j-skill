"""
Neo4j CRUD 工具模块 - 提供连接管理、增删改查和 Cypher 查询执行功能。

使用方式:
    from neo4j_utils import Neo4jClient

    # 使用默认配置连接
    client = Neo4jClient()

    # 或指定连接参数
    client = Neo4jClient(uri="bolt://localhost:7687", user="neo4j", password="your_password")

    支持 CRUD 方法:
    - execute_query(query, params) -> 执行任意 Cypher 查询
    - create_node(label, properties) -> 创建节点
    - get_node(label, property_name, property_value) -> 查询节点
    - get_all_nodes(label, limit=100) -> 查询所有节点
    - update_node(node_id, properties) -> 更新节点属性
    - delete_node(node_id) -> 删除节点
    - create_relationship(from_node_id, to_node_id, rel_type, properties) -> 创建关系
    - get_node_relationships(node_id) -> 查询节点关系
    - delete_relationship(rel_id) -> 删除关系
    - clear_database() -> 清空数据库（谨慎使用!）
"""

import io
import json
import os
import sys

# 统一 stdout/stderr 编码为 UTF-8，避免 Windows 终端中文乱码
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError


def _get_config_path():
    """获取配置文件路径"""
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(skill_dir, "scripts", "neo4j_config.json")


def load_config():
    """加载 Neo4j 连接配置"""
    config_path = _get_config_path()
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def save_config(uri, user, password, database="neo4j"):
    """保存 Neo4j 连接配置"""
    config_path = _get_config_path()
    config = {"uri": uri, "user": user, "password": password, "database": database}
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"配置已保存到: {config_path}")


def _format_value(value):
    """格式化 Neo4j 返回值为可读的 Python 对象"""
    if hasattr(value, "items"):  # dict-like (Node/Relationship)
        return dict(value)
    if hasattr(value, "element_id"):
        # 处理 Node 或 Relationship 对象
        if hasattr(value, "labels"):
            # 是 Node
            return {
                "_type": "node",
                "_id": value.element_id,
                "_labels": list(value.labels),
                **dict(value),
            }
        elif hasattr(value, "type"):
            # 是 Relationship
            return {
                "_type": "relationship",
                "_id": value.element_id,
                "_type_name": value.type,
                "_start_node_id": value.start_node.element_id if hasattr(value.start_node, "element_id") else str(value.start_node),
                "_end_node_id": value.end_node.element_id if hasattr(value.end_node, "element_id") else str(value.end_node),
                **dict(value),
            }
    if isinstance(value, (list, tuple)):
        return [_format_value(v) for v in value]
    return value


class Neo4jClient:
    """Neo4j 数据库客户端，提供连接管理和 CRUD 操作"""

    def __init__(self, uri=None, user=None, password=None, database=None):
        config = load_config()
        self.uri = uri or config.get("uri", "bolt://localhost:7687")
        self.user = user or config.get("user", "neo4j")
        self.password = password or config.get("password", "neo4j")
        self.database = database or config.get("database", "neo4j")
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self._driver

    def close(self):
        """关闭数据库连接"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def execute_query(self, query, params=None):
        """
        执行任意 Cypher 查询

        参数:
            query: Cypher 查询语句
            params: 查询参数字典 (可选)

        返回:
            查询结果列表 (每条记录为字典)
        """
        params = params or {}
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params)
                records = [_format_value(record.data()) for record in result]
                summary = result.consume()
                return {
                    "success": True,
                    "records": records,
                    "count": len(records),
                    "summary": {
                        "counters": str(summary.counters),
                    },
                }
        except Neo4jError as e:
            return {"success": False, "error": str(e), "code": e.code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========== CREATE ==========

    def create_node(self, label, properties=None):
        """
        创建节点

        参数:
            label: 节点标签 (如 "Person", "Movie")
            properties: 节点属性字典 (可选)

        返回:
            创建的节点信息
        """
        props = properties or {}
        if not props:
            # 至少需要一个属性
            props = {"name": f"sample_{label.lower()}"}

        keys = list(props.keys())
        set_clause = "SET " + ", ".join(f"n.{k} = ${k}" for k in keys)

        query = f"""
        CREATE (n:{label})
        {set_clause}
        RETURN n, elementId(n) AS node_id
        """
        return self.execute_query(query, props)

    # ========== READ ==========

    def get_node(self, label, property_name, property_value):
        """
        根据属性查询节点

        参数:
            label: 节点标签
            property_name: 属性名
            property_value: 属性值

        返回:
            匹配的节点列表
        """
        query = f"""
        MATCH (n:{label} {{{property_name}: $value}})
        RETURN n, elementId(n) AS node_id
        """
        return self.execute_query(query, {"value": property_value})

    def get_all_nodes(self, label, limit=100):
        """
        查询指定标签的所有节点

        参数:
            label: 节点标签
            limit: 返回数量限制 (默认 100)

        返回:
            节点列表
        """
        query = f"""
        MATCH (n:{label})
        RETURN n, elementId(n) AS node_id
        LIMIT $limit
        """
        return self.execute_query(query, {"limit": limit})

    def find_nodes(self, label, filters=None, limit=100):
        """
        按多个条件筛选节点

        参数:
            label: 节点标签
            filters: 筛选条件字典，如 {{"name": "Alice", "age": 30}}
            limit: 返回数量限制

        返回:
            符合条件的节点列表
        """
        filters = filters or {}
        if not filters:
            return self.get_all_nodes(label, limit)

        where_clause = " AND ".join(
            f"n.{k} = ${k}" for k in filters
        )
        query = f"""
        MATCH (n:{label})
        WHERE {where_clause}
        RETURN n, elementId(n) AS node_id
        LIMIT $limit
        """
        params = {**filters, "limit": limit}
        return self.execute_query(query, params)

    # ========== UPDATE ==========

    def update_node(self, node_id, properties):
        """
        更新节点属性

        参数:
            node_id: 节点的 elementId
            properties: 要更新的属性字典

        返回:
            更新后的节点信息
        """
        set_clause = ", ".join(f"n.{k} = ${k}" for k in properties)
        query = f"""
        MATCH (n)
        WHERE elementId(n) = $node_id
        SET {set_clause}
        RETURN n, elementId(n) AS node_id
        """
        params = {"node_id": node_id, **properties}
        return self.execute_query(query, params)

    # ========== DELETE ==========

    def delete_node(self, node_id):
        """
        删除节点及其所有关系

        参数:
            node_id: 节点的 elementId

        返回:
            操作结果
        """
        query = """
        MATCH (n)
        WHERE elementId(n) = $node_id
        DETACH DELETE n
        RETURN count(n) AS deleted_count
        """
        return self.execute_query(query, {"node_id": node_id})

    # ========== RELATIONSHIPS ==========

    def create_relationship(
        self, from_node_id, to_node_id, rel_type, properties=None
    ):
        """
        创建关系

        参数:
            from_node_id: 起始节点的 elementId
            to_node_id: 目标节点的 elementId
            rel_type: 关系类型 (如 "KNOWS", "LOVES")
            properties: 关系属性 (可选)

        返回:
            创建的关系信息
        """
        props = properties or {}
        if props:
            set_clause = "SET " + ", ".join(f"r.{k} = ${k}" for k in props)
            query = f"""
            MATCH (a), (b)
            WHERE elementId(a) = $from_node_id AND elementId(b) = $to_node_id
            CREATE (a)-[r:{rel_type}]->(b)
            {set_clause}
            RETURN r, elementId(r) AS rel_id, elementId(a) AS from_id, elementId(b) AS to_id
            """
            params = {"from_node_id": from_node_id, "to_node_id": to_node_id, **props}
        else:
            query = f"""
            MATCH (a), (b)
            WHERE elementId(a) = $from_node_id AND elementId(b) = $to_node_id
            CREATE (a)-[r:{rel_type}]->(b)
            RETURN r, elementId(r) AS rel_id, elementId(a) AS from_id, elementId(b) AS to_id
            """
            params = {"from_node_id": from_node_id, "to_node_id": to_node_id}

        return self.execute_query(query, params)

    def get_node_relationships(self, node_id, direction="both", limit=100):
        """
        查询节点的所有关系

        参数:
            node_id: 节点的 elementId
            direction: 方向 - "outgoing", "incoming", "both" (默认)
            limit: 返回数量限制

        返回:
            关系列表
        """
        if direction == "outgoing":
            pattern = "(n)-[r]->(other)"
        elif direction == "incoming":
            pattern = "(n)<-[r]-(other)"
        else:
            pattern = "(n)-[r]-(other)"

        query = f"""
        MATCH {pattern}
        WHERE elementId(n) = $node_id
        RETURN r, elementId(r) AS rel_id, elementId(n) AS from_id,
               elementId(other) AS to_id,
               labels(other) AS other_labels,
               type(r) AS rel_type
        LIMIT $limit
        """
        return self.execute_query(query, {"node_id": node_id, "limit": limit})

    def delete_relationship(self, rel_id):
        """
        删除关系

        参数:
            rel_id: 关系的 elementId

        返回:
            操作结果
        """
        query = """
        MATCH ()-[r]->()
        WHERE elementId(r) = $rel_id
        DELETE r
        RETURN count(r) AS deleted_count
        """
        return self.execute_query(query, {"rel_id": rel_id})

    # ========== UTILITY ==========

    def clear_database(self):
        """清空数据库中的所有数据（谨慎使用！）"""
        confirm = input("确认清空整个数据库？输入 'yes' 确认: ")
        if confirm.lower() != "yes":
            return {"success": False, "error": "操作已取消"}
        return self.execute_query("MATCH (n) DETACH DELETE n")

    def get_database_info(self):
        """获取数据库信息"""
        info = {}
        info["connectivity"] = self.execute_query("RETURN 1 AS test")
        info["node_count"] = self.execute_query(
            "MATCH (n) RETURN count(n) AS total_nodes"
        )
        info["rel_count"] = self.execute_query(
            "MATCH ()-->() RETURN count(*) AS total_relationships"
        )
        info["labels"] = self.execute_query(
            "CALL db.labels() YIELD label RETURN label"
        )
        info["rel_types"] = self.execute_query(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
        )
        return info

    def show_schema(self):
        """显示数据库 schema (节点标签、关系类型、属性键)"""
        labels = self.execute_query("CALL db.labels() YIELD label RETURN label")
        rel_types = self.execute_query(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
        )
        prop_keys = self.execute_query(
            "CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey"
        )
        return {
            "labels": labels,
            "relationship_types": rel_types,
            "property_keys": prop_keys,
        }


def main():
    """命令行入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python neo4j_utils.py <command> [args...]")
        print("命令:")
        print("  config <uri> <user> <password> [database]  - 配置连接信息")
        print("  query <cypher> [json_params]               - 执行 Cypher 查询")
        print("  create <label> [json_props]                - 创建节点")
        print("  get <label> <prop_name> <prop_value>       - 查询节点")
        print("  all <label> [limit]                        - 查询所有节点")
        print("  update <node_id> <json_props>              - 更新节点")
        print("  delete <node_id>                           - 删除节点")
        print("  info                                       - 获取数据库信息")
        return

    command = sys.argv[1]
    client = Neo4jClient()

    if command == "config":
        if len(sys.argv) < 5:
            print("用法: config <uri> <user> <password> [database]")
            return
        database = sys.argv[4] if len(sys.argv) > 4 else "neo4j"
        save_config(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "neo4j", database)
        print("配置已更新")

    elif command == "query":
        if len(sys.argv) < 3:
            print("用法: query <cypher> [json_params]")
            return
        params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = client.execute_query(sys.argv[2], params)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == "create":
        if len(sys.argv) < 3:
            print("用法: create <label> [json_props]")
            return
        props = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = client.create_node(sys.argv[2], props)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == "get":
        if len(sys.argv) < 5:
            print("用法: get <label> <prop_name> <prop_value>")
            return
        result = client.get_node(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == "all":
        if len(sys.argv) < 3:
            print("用法: all <label> [limit]")
            return
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        result = client.get_all_nodes(sys.argv[2], limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == "update":
        if len(sys.argv) < 4:
            print("用法: update <node_id> <json_props>")
            return
        props = json.loads(sys.argv[3])
        result = client.update_node(sys.argv[2], props)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == "delete":
        if len(sys.argv) < 3:
            print("用法: delete <node_id>")
            return
        result = client.delete_node(sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif command == "info":
        info = client.get_database_info()
        print(json.dumps(info, ensure_ascii=False, indent=2))

    else:
        print(f"未知命令: {command}")

    client.close()


if __name__ == "__main__":
    main()
