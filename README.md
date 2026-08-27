# Ulanzi Renderer

Home Assistant custom component，用单写者 Renderer 统一管理 Ulanzi 像素时钟显示。

## P0 能力

- `dict[slot_id, DisplaySlot] + heapq` 优先级队列
- lazy deletion：retract 和重复 upsert 不重建堆
- 每秒 tick，数字越小优先级越高
- TTL 自动过期
- 稳定 JSON hash 去重
- Phase 0 shadow mode：默认只更新诊断 state，不发送 MQTT

## 安装

将 `custom_components/ulanzi_renderer` 复制到 Home Assistant 的 `/config/custom_components/`，重启 HA 后在“设置 → 设备与服务”添加 **Ulanzi Renderer**。

默认配置：

- Broker：`192.168.31.111:1883`
- Prefix：`ulanzi_aa68`
- Topic：`ulanzi_aa68/custom/test`

组件通过 Home Assistant 已配置的 MQTT 集成发布消息。P0 中 broker host/port 作为配置元数据保留。

## 服务接口

### `ulanzi_renderer.publish`

| 字段 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `slot_id` | 是 | string | 槽位 ID |
| `priority` | 是 | integer | 数字越小优先级越高 |
| `payload` | 是 | mapping | Ulanzi custom topic JSON payload |
| `ttl_seconds` | 否 | number | 生存时间；不填则持续有效 |

```yaml
action: ulanzi_renderer.publish
data:
  slot_id: welcome
  priority: 1
  ttl_seconds: 15
  payload:
    text:
      textString: "欢迎回家"
```

### `ulanzi_renderer.retract`

```yaml
action: ulanzi_renderer.retract
data:
  slot_id: welcome
```

删除操作幂等；不存在的槽位也会成功返回。

## Shadow / Active

`input_boolean.ulanzi_renderer_enabled` 不是组件自动创建的实体：

- 不存在或为 `off`：shadow，只更新 `sensor.ulanzi_renderer_status` 与 `sensor.ulanzi_renderer_shadow_head`
- 为 `on`：active，当前堆顶经过去重后发布到 `<prefix>/custom/test`

Phase 0 请保持关闭，先验证影子堆顶与现有 owner lock 一致。
