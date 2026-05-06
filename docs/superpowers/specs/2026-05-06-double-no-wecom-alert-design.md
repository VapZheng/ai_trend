# 均线 NO 企业微信告警设计

## 背景

当前项目会在后端刷新流程中生成多均线视图数据，核心趋势结果存放在 `dataset.views` 中，其中 `ma5` 与 `ma20` 视图分别包含每个指数的最新 `status`。前端仅负责展示 `/api/dashboard` 返回的数据，尚未具备通知链路。

本次需求是在后端新增一条显式告警路径：当某个指数从“5 日与 20 日均为 YES”或“仅另一条均线为 NO”切换到“任一均线为 NO”时，通过企业微信机器人发送一条汇总消息，并在消息中明确说明命中的是 `ma5`、`ma20`，还是两者同时命中。

## 目标

- 仅在指数“新进入至少一条均线为 NO”时触发告警。
- 同一次刷新内，所有新进入告警态的指数合并为一条企业微信消息。
- 指数持续处于告警态时不重复发送。
- 指数退出告警态后，若后续再次进入，允许再次发送。
- 通知消息明确展示命中的均线类型：`ma5`、`ma20` 或 `ma5 + ma20`。
- 通知失败必须显式暴露，不引入静默降级或假成功路径。

## 非目标

- 不增加邮件通知。
- 不实现通用规则引擎。
- 不回扫历史数据补发通知。
- 不改动前端展示逻辑。

## 触发规则

以一次 `refresh_dataset()` 成功生成的最新 `dataset` 为准：

1. 读取 `dataset.views.ma5` 与 `dataset.views.ma20`。
2. 以指数 `code` 为键合并两个视图中的 `items`。
3. 若某个指数满足以下任一条件，则该指数命中“均线 NO”规则：
   - `ma5.status == "NO"`
   - `ma20.status == "NO"`
4. 对命中的指数，记录本次命中的均线集合：
   - 仅 `ma5` 为 `NO`，则命中类型为 `ma5`
   - 仅 `ma20` 为 `NO`，则命中类型为 `ma20`
   - `ma5` 与 `ma20` 都为 `NO`，则命中类型为 `ma5 + ma20`
5. 仅当该指数本次命中，且持久化状态中此前不是激活态时，认定为“新进入告警态”。
6. 同一次刷新中的全部“新进入告警态”指数合并成一条企业微信消息。

若 `ma5` 或 `ma20` 视图缺失，直接抛错，不做静默跳过。

## 数据设计

新增表：`trend_alert_states`

字段：

- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `rule_key TEXT NOT NULL`
- `code TEXT NOT NULL`
- `is_active INTEGER NOT NULL`
- `active_windows TEXT NOT NULL`
- `last_entered_at TEXT`
- `last_notified_at TEXT`
- `updated_at TEXT NOT NULL`

约束：

- `UNIQUE(rule_key, code)`

固定规则键：

- `any_ma_no`

字段语义：

- `is_active = 1`：该指数当前至少一条均线为 NO。
- `is_active = 0`：该指数当前两条均线都不是 NO。
- `active_windows`：当前命中的均线列表，使用稳定字符串持久化，初版建议为 `ma5`、`ma20`、`ma5,ma20` 或空字符串。
- `last_entered_at`：最近一次从非告警态切到告警态的时间。
- `last_notified_at`：最近一次告警发送成功的时间。
- `updated_at`：该行最近一次被刷新流程更新的时间。

## 模块设计

### 1. Alert Repository

在现有 `SQLiteTrendRepository` 中新增告警状态读写能力，避免再引入新的 sqlite 连接实现。

建议方法：

- `list_alert_states(rule_key: str) -> dict[str, TrendAlertState]`
- `upsert_alert_state(state: TrendAlertState) -> None`

仓储职责仅限持久化，不负责规则判定与消息发送。

### 2. Alert Rule Service

新增 `backend/alert_service.py`，负责：

- 从 `dataset.views.ma5` 与 `dataset.views.ma20` 提取最新状态。
- 对比 `trend_alert_states`，找出“新进入告警态”的指数。
- 为每个命中指数计算 `active_windows`。
- 将退出告警态的指数状态重置为 `is_active = 0`，并清空 `active_windows`。
- 返回本次待通知的指数列表。

建议输出结构包含：

- `triggered_items`：本次新进入告警态的指数列表。
- `entered_codes`：本次进入告警态的代码集合。
- `exited_codes`：本次退出告警态的代码集合。

`triggered_items` 中每个元素建议额外带上：

- `activeWindows`：命中的均线列表
- `activeWindowLabel`：`ma5`、`ma20` 或 `ma5 + ma20`

### 3. WeCom Notifier

新增 `backend/notifiers/wecom.py`，职责单一：

- 从环境变量 `TREND_WECOM_WEBHOOK` 读取机器人 webhook。
- 接收已格式化好的汇总消息内容。
- 调用企业微信机器人 webhook 发送请求。
- 对非成功响应直接抛错。

通知器不参与规则判定，也不负责构造市场数据。

### 4. Service Integration

在 `TrendDashboardService.refresh_dataset()` 的成功路径中：

1. 生成并保存最新 `dataset`。
2. 执行“任一均线 NO”规则判定，更新 `trend_alert_states`。
3. 若存在 `triggered_items`，发送一条企业微信汇总消息。
4. 发送成功后，更新这些指数的 `last_notified_at`。
5. 之后记录本次 `refresh_run` 为成功。

若消息发送失败：

- 异常直接抛出。
- 本次刷新流程记录失败状态与错误信息。
- `dataset` 保持已保存状态。
- `is_active` 与 `active_windows` 等市场状态保持已更新状态。
- `last_notified_at` 不更新。

## 消息格式

初版使用企业微信 `markdown` 消息。

标题：

- `趋势告警：新增均线 NO 指数`

内容字段：

- 刷新时间
- 命中数量
- 指数明细列表

每条明细建议包含：

- `名称(code)`
- `最新价`
- `命中均线`
- `状态开始日`

示例：

```markdown
## 趋势告警：新增均线 NO 指数
> 时间：2026-05-06 15:10:00
> 数量：3

- 上证指数(000001) | 最新价 3120.55 | 命中 ma5 | 状态开始 2026-05-06
- 创业板指(399006) | 最新价 1888.22 | 命中 ma20 | 状态开始 2026-05-05
- 恒生指数(HSI) | 最新价 18456.30 | 命中 ma5 + ma20 | 状态开始 2026-05-06
```

`状态开始日` 取本次命中均线对应的 `statusChangedAt` 中最晚的日期：

- 仅命中 `ma5` 时，取 `ma5.statusChangedAt`
- 仅命中 `ma20` 时，取 `ma20.statusChangedAt`
- 同时命中时，取两者中较晚的日期

这样可以避免把较早出现的单均线 NO 时间误当作当前告警态的开始时间。

## 边界处理

- 若本次没有任何新进入告警态的指数，则不发送消息。
- 若指数持续处于告警态，则不重复告警。
- 若指数退出告警态，则重置为非激活态并清空命中均线。
- 若指数先退出、后再次进入告警态，则允许再次告警。
- 若 webhook 未配置，直接抛错，不做跳过。
- 若企业微信返回业务错误码，直接抛错，不吞掉错误。

## 测试策略

重点覆盖以下场景：

1. 首次进入 `ma5=NO`，生成一条汇总通知，并标记命中 `ma5`。
2. 首次进入 `ma20=NO`，生成一条汇总通知，并标记命中 `ma20`。
3. 首次同时进入 `ma5=NO` 与 `ma20=NO`，生成一条汇总通知，并标记命中 `ma5 + ma20`。
4. 指数持续处于告警态，多次刷新不重复通知。
5. 指数退出告警态，状态被正确重置。
6. 指数退出后再次进入告警态，能够再次通知。
7. 同次刷新多个指数进入告警态，只发送一条汇总消息。
8. `ma5` 或 `ma20` 视图缺失时，流程显式失败。
9. 企业微信发送失败时，`last_notified_at` 不更新，且刷新记录写入失败信息。

## 实施顺序

1. 扩展 sqlite schema，增加 `trend_alert_states` 表。
2. 在 repository 中补充告警状态模型与读写方法。
3. 新增“任一均线 NO”规则服务，实现命中判定和状态迁移。
4. 新增企业微信通知器，实现 webhook 发送。
5. 将告警流程接入 `TrendDashboardService.refresh_dataset()`。
6. 补充针对判定逻辑、通知流程和失败路径的自动化测试。
