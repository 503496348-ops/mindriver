"""
MindRiver Web API — RESTful接口
基于Flask提供上下文检索和记忆管理API
"""
from flask import Flask, request, jsonify
import sqlite3
import json
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path.home() / ".mindriver" / "mindriver.db"


def get_db():
    """获取SQLite连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/v1/search", methods=["POST"])
def search():
    """搜索上下文"""
    data = request.json
    query = data.get("query", "")
    limit = data.get("limit", 10)
    
    db = get_db()
    results = db.execute(
        "SELECT * FROM nodes WHERE content LIKE ? LIMIT ?",
        (f"%{query}%", limit)
    ).fetchall()
    
    return jsonify({"results": [dict(r) for r in results], "count": len(results)})


@app.route("/api/v1/nodes", methods=["GET"])
def list_nodes():
    """列出所有节点"""
    db = get_db()
    nodes = db.execute("SELECT * FROM nodes ORDER BY path").fetchall()
    return jsonify({"nodes": [dict(n) for n in nodes]})


@app.route("/api/v1/nodes", methods=["POST"])
def create_node():
    """创建新节点"""
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO nodes (path, content, layer, tags) VALUES (?, ?, ?, ?)",
        (data["path"], data["content"], data.get("layer", "L0"), json.dumps(data.get("tags", [])))
    )
    db.commit()
    return jsonify({"status": "created"}), 201


@app.route("/api/v1/predict/relevance", methods=["POST"])
def predict_relevance():
    """预测节点与查询的相关性（基于TF-IDF模型）"""
    data = request.json
    query = data.get("query", "")
    node_id = data.get("node_id")
    
    # 简单TF-IDF相关性预测
    db = get_db()
    node = db.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
    
    if not node:
        return jsonify({"error": "Node not found"}), 404
    
    query_terms = set(query.lower().split())
    content_terms = set(node["content"].lower().split())
    overlap = len(query_terms & content_terms)
    relevance = overlap / max(len(query_terms), 1)
    
    return jsonify({"node_id": node_id, "relevance": relevance, "matching_terms": list(query_terms & content_terms)})


@app.route("/health")
def health():
    """健康检查"""
    return jsonify({"status": "ok", "service": "mindriver-api"})


def run_server(host="0.0.0.0", port=8080):
    """启动API服务"""
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
