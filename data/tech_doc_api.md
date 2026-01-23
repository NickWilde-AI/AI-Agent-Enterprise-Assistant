# 设备健康监测 API 使用说明

## 概述
用于查询热轧机设备的健康状态与告警记录，面向工艺与设备工程师。

## 认证
- 采用 API Token（由运维系统发放）。
- 请求 Header：`Authorization: Bearer <token>`

## 接口列表
### 1) 查询设备健康状态
- URL: `GET /api/v1/equipment/{equipment_id}/health`
- 参数：`equipment_id`（字符串）
- 返回：
```json
{
  "equipment_id": "RZ-01",
  "health_score": 0.92,
  "risk_level": "low",
  "last_updated": "2025-06-20T10:30:00+08:00"
}
```

### 2) 查询告警记录
- URL: `GET /api/v1/equipment/{equipment_id}/alerts?days=7`
- 参数：`days`（默认 7）
- 返回：
```json
{
  "equipment_id": "RZ-01",
  "alerts": [
    {"time": "2025-06-19T09:10:00+08:00", "type": "vibration", "level": "medium"}
  ]
}
```

## 注意事项
- 单次请求 QPS 上限 20。
- 设备风险等级：low/medium/high。
