# MCP 工具定义

## 工具列表

### 1) get_employee_profile
- description: 根据员工姓名查询部门、职级与邮箱。
- input schema:
```json
{
  "name": "张三"
}
```
- output schema:
```json
{
  "found": true,
  "name": "张三",
  "department": "工艺工程部",
  "level": "P4",
  "email": "zhangsan@example.com"
}
```

### 2) get_reimbursement_summary
- description: 查询员工某月的报销总额与明细。
- input schema:
```json
{
  "name": "张三",
  "month": "2025-03"
}
```
- output schema:
```json
{
  "name": "张三",
  "month": "2025-03",
  "total": 1860.0,
  "items": [
    {"category": "交通", "amount": 420.0, "note": "高铁票"}
  ]
}
```

### 3) get_project_status
- description: 查询指定项目的进度与风险说明。
- input schema:
```json
{
  "project": "铝加工知识智能问答系统"
}
```
- output schema:
```json
{
  "found": true,
  "project": "铝加工知识智能问答系统",
  "phase": "知识库构建",
  "progress": 0.8,
  "risk": "行业术语词表需补充",
  "owner": "李杨"
}
```

### 4) create_ticket
- description: 创建工单记录，返回工单编号。
- input schema:
```json
{
  "title": "报销资料补充",
  "description": "请补充 2025-03 出差住宿发票",
  "requester": "王五",
  "priority": "P1"
}
```
- output schema:
```json
{
  "created": true,
  "ticket": {
    "id": "T-20250620153000",
    "title": "报销资料补充",
    "requester": "王五",
    "priority": "P1"
  }
}
```

## MCP 结构图
```text
Client (Agent) ↔ MCP Server ↔ SQLite/JSON
```
