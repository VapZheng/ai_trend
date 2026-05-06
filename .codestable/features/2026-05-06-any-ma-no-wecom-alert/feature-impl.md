# 均线 NO 企业微信告警 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在趋势刷新成功后，识别“任一均线为 NO”的新进入告警态指数，并通过企业微信机器人发送一条汇总通知。

**Architecture:** 在现有 `SQLiteTrendRepository` 上扩展告警状态持久化，在新的 `alert_service` 中完成 `ma5/ma20` 聚合与状态迁移，在 `wecom` 通知器中处理 webhook 发送，最后把告警流程接入 `TrendDashboardService.refresh_dataset()`。整个过程按 TDD 执行，先验证规则与失败路径，再接入真实服务。

**Tech Stack:** Python 3.12、sqlite3、httpx、unittest

---

## File Map

- Modify: `backend/models.py` - 增加告警状态与通知相关类型。
- Modify: `backend/config.py` - 增加企业微信 webhook 配置。
- Modify: `backend/repository.py` - 增加 `trend_alert_states` 表与读写方法。
- Modify: `backend/service.py` - 在刷新流程中接入告警判定与通知。
- Modify: `backend/app.py` - 装配告警服务与企业微信通知器。
- Create: `backend/alert_service.py` - 负责均线 NO 判定、状态迁移、消息格式化。
- Create: `backend/notifiers/__init__.py` - 通知器包入口。
- Create: `backend/notifiers/wecom.py` - 企业微信机器人发送器。
- Test: `backend/tests/test_alert_service.py` - 规则判定、状态开始日、缺视图错误。
- Test: `backend/tests/test_repository.py` - 告警状态表初始化与读写。
- Test: `backend/tests/test_service.py` - 刷新流程接入、汇总发送、发送失败路径。

### Task 1: 告警规则与仓储测试

**Files:**
- Create: `backend/tests/test_alert_service.py`
- Create: `backend/tests/test_repository.py`
- Modify: `backend/models.py`
- Modify: `backend/repository.py`

- [ ] **Step 1: 写告警规则失败测试**

```python
class EvaluateAnyMaNoAlertTests(unittest.TestCase):
    def test_marks_newly_entered_item_and_labels_active_window(self) -> None:
        dataset = build_dataset_with_statuses(
            ma5_status='NO',
            ma20_status='YES',
            ma5_changed_at='2026-05-06',
            ma20_changed_at='2026-05-01',
        )

        result = evaluate_any_ma_no_alerts(
            dataset=dataset,
            existing_states={},
            refreshed_at='2026-05-06 10:00:00',
        )

        self.assertEqual(['000001'], result.entered_codes)
        self.assertEqual('ma5', result.triggered_items[0].active_window_label)
        self.assertEqual('2026-05-06', result.triggered_items[0].status_started_at)
```

- [ ] **Step 2: 运行规则测试确认失败**

Run: `python3 -m unittest backend.tests.test_alert_service -v`
Expected: FAIL，提示 `evaluate_any_ma_no_alerts` 或辅助类型尚未定义。

- [ ] **Step 3: 写仓储失败测试**

```python
class SQLiteTrendRepositoryAlertStateTests(unittest.TestCase):
    def test_persists_and_reads_alert_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = SQLiteTrendRepository(
                database_path=Path(temp_dir) / 'trends.db',
                now_provider=lambda: datetime(2026, 5, 6, 10, 0, 0),
            )
            repository.initialize()

            repository.upsert_alert_state(
                TrendAlertState(
                    rule_key=ALERT_RULE_ANY_MA_NO,
                    code='000001',
                    is_active=True,
                    active_windows=('ma5',),
                    last_entered_at='2026-05-06 10:00:00',
                    last_notified_at=None,
                    updated_at='2026-05-06 10:00:00',
                )
            )

            states = repository.list_alert_states(ALERT_RULE_ANY_MA_NO)

            self.assertTrue(states['000001'].is_active)
            self.assertEqual(('ma5',), states['000001'].active_windows)
```

- [ ] **Step 4: 运行仓储测试确认失败**

Run: `python3 -m unittest backend.tests.test_repository -v`
Expected: FAIL，提示告警模型或 repository 方法不存在。

- [ ] **Step 5: 写最小实现让两组测试变绿**

```python
@dataclass(frozen=True)
class TrendAlertState:
    rule_key: str
    code: str
    is_active: bool
    active_windows: tuple[str, ...]
    last_entered_at: str | None
    last_notified_at: str | None
    updated_at: str
```

```python
CREATE TABLE IF NOT EXISTS trend_alert_states (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_key TEXT NOT NULL,
  code TEXT NOT NULL,
  is_active INTEGER NOT NULL,
  active_windows TEXT NOT NULL,
  last_entered_at TEXT,
  last_notified_at TEXT,
  updated_at TEXT NOT NULL,
  UNIQUE(rule_key, code)
)
```

- [ ] **Step 6: 运行测试确认通过**

Run: `python3 -m unittest backend.tests.test_alert_service backend.tests.test_repository -v`
Expected: PASS，规则与仓储测试全部通过。

### Task 2: 告警服务实现

**Files:**
- Create: `backend/alert_service.py`
- Modify: `backend/models.py`
- Test: `backend/tests/test_alert_service.py`

- [ ] **Step 1: 补“持续告警不重复发”和“退出后再进入可重发”的失败测试**

```python
def test_keeps_active_item_without_retriggering(self) -> None:
    state = build_alert_state(is_active=True, active_windows=('ma20',))
    dataset = build_dataset_with_statuses(ma5_status='YES', ma20_status='NO')

    result = evaluate_any_ma_no_alerts(
        dataset=dataset,
        existing_states={'000001': state},
        refreshed_at='2026-05-06 10:10:00',
    )

    self.assertEqual([], result.entered_codes)
    self.assertEqual([], result.triggered_items)
```

- [ ] **Step 2: 运行规则测试确认失败**

Run: `python3 -m unittest backend.tests.test_alert_service -v`
Expected: FAIL，说明当前规则实现未覆盖状态迁移。

- [ ] **Step 3: 写最小告警服务实现**

```python
def evaluate_any_ma_no_alerts(dataset, existing_states, refreshed_at):
    ma5_items = index_items_by_code(require_view(dataset, 'ma5'))
    ma20_items = index_items_by_code(require_view(dataset, 'ma20'))
    return build_alert_evaluation(ma5_items, ma20_items, existing_states, refreshed_at)
```

```python
def build_active_windows(ma5_item, ma20_item):
    windows = []
    if ma5_item['status'] == 'NO':
        windows.append('ma5')
    if ma20_item['status'] == 'NO':
        windows.append('ma20')
    return tuple(windows)
```

- [ ] **Step 4: 运行规则测试确认通过**

Run: `python3 -m unittest backend.tests.test_alert_service -v`
Expected: PASS，规则测试全部通过。

### Task 3: 企业微信通知器测试与实现

**Files:**
- Create: `backend/notifiers/__init__.py`
- Create: `backend/notifiers/wecom.py`
- Modify: `backend/config.py`
- Test: `backend/tests/test_service.py`

- [ ] **Step 1: 写通知器配置与发送失败测试**

```python
def test_send_markdown_raises_when_webhook_missing(self) -> None:
    notifier = WeComNotifier(webhook_url='')

    with self.assertRaises(ValueError):
        notifier.send_markdown('hello')
```

```python
def test_send_markdown_posts_expected_payload(self) -> None:
    transport = MockTransport(assert_request)
    notifier = WeComNotifier(
        webhook_url='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test',
        client_factory=lambda: httpx.Client(transport=transport),
    )

    notifier.send_markdown('hello')
```

- [ ] **Step 2: 运行通知器测试确认失败**

Run: `python3 -m unittest backend.tests.test_service -v`
Expected: FAIL，提示 `WeComNotifier` 尚未定义。

- [ ] **Step 3: 写最小通知器实现**

```python
class WeComNotifier:
    def send_markdown(self, content: str) -> None:
        if self._webhook_url == '':
            raise ValueError('TREND_WECOM_WEBHOOK 未配置')
        payload = {'msgtype': 'markdown', 'markdown': {'content': content}}
        with self._client_factory() as client:
            response = client.post(self._webhook_url, json=payload)
        response.raise_for_status()
        if response.json().get('errcode') != 0:
            raise RuntimeError(f'企业微信通知失败: {response.text}')
```

- [ ] **Step 4: 运行通知器测试确认通过**

Run: `python3 -m unittest backend.tests.test_service -v`
Expected: PASS，通知器相关测试通过。

### Task 4: 刷新流程集成

**Files:**
- Modify: `backend/service.py`
- Modify: `backend/app.py`
- Test: `backend/tests/test_service.py`

- [ ] **Step 1: 写服务集成失败测试**

```python
def test_refresh_dataset_sends_single_summary_for_triggered_items(self) -> None:
    service = TrendDashboardService(
        fetcher=StubFetcher(dataset),
        repository=repository,
        fetch_options=FetchOptions(...),
        now_provider=lambda: datetime(2026, 5, 6, 10, 0, 0),
        alert_service=alert_service,
        notifier=notifier,
    )

    service.refresh_dataset('scheduler')

    self.assertEqual(1, len(notifier.messages))
    self.assertIn('命中 ma5 + ma20', notifier.messages[0])
```

- [ ] **Step 2: 运行服务测试确认失败**

Run: `python3 -m unittest backend.tests.test_service -v`
Expected: FAIL，提示 `TrendDashboardService` 构造参数或刷新流程尚未支持告警集成。

- [ ] **Step 3: 写最小集成实现**

```python
result = self._alert_service.evaluate_and_persist(dataset, self._repository, self._format_now())
if result.triggered_items:
    message = format_any_ma_no_alert_message(result.triggered_items, dataset['updatedAt'])
    self._notifier.send_markdown(message)
    self._repository.mark_alerts_notified(ALERT_RULE_ANY_MA_NO, result.entered_codes, self._format_now())
```

- [ ] **Step 4: 运行服务测试确认通过**

Run: `python3 -m unittest backend.tests.test_service -v`
Expected: PASS，发送成功和发送失败路径都符合预期。

### Task 5: 全量验证

**Files:**
- Test: `backend/tests/test_alert_service.py`
- Test: `backend/tests/test_repository.py`
- Test: `backend/tests/test_service.py`
- Test: `backend/tests/test_scheduler.py`

- [ ] **Step 1: 运行后端测试套件**

Run: `python3 -m unittest discover -s backend/tests -p 'test_*.py'`
Expected: PASS，所有后端测试通过。

- [ ] **Step 2: 运行一次脚本级冒烟检查**

Run: `python3 -m compileall backend`
Expected: PASS，无语法错误。

- [ ] **Step 3: 提交实现**

```bash
git add backend docs/superpowers/plans/2026-05-06-any-ma-no-wecom-alert.md
git commit -m "实现均线NO企业微信告警"
```
