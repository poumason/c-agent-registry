# 0013 — 拿掉 Active 版本數量上限

**Commit**: `696c60d` · 2026-08-19

## 做了什麼

Claude.md「FAB 與版本的關係」的 2026/08/19 新規範：拿掉「同一個 agent 最多 2 個 active 版本」
的限制；一個 version 可以設定多個 fab，等同於每個 fab 可能會有多個版本同時服務。

- `POST /versions/{slug}/activate`（`backend/app/api/v1/endpoints/agent_versions.py`）拿掉
  `active_count >= MAX_ACTIVE_VERSIONS_PER_AGENT` 檢查跟該常數，只保留「來源版本要是
  approved」這條規則。
- `crud/agent_version.count_active` 隨之移除（唯一呼叫端已拿掉）。
- 「一個 fab 可能對應多個 active 版本」不需要新的 schema 或邏輯——`agent_fabs`
  （`(fab_id, agent_version_slug)` 為 PK）跟 0012 的 `agent_dependencies.fab_id` 本來就是
  per-version 的多對多／fab-scoped 設計，天生就支援不同 active 版本各自服務同一個 fab。真正卡住
  這件事的只有規則1的人為上限——拿掉之後，規則2就直接可用，不用額外改程式碼。
- `test_agents.py::test_max_two_active_versions_per_agent`（驗證第 3 次 activate 會 409）改寫成
  `test_no_limit_on_active_versions_per_agent`（驗證 3 個版本都能同時 active）。
- `docs/agent-lifecycle.md`、`idea.drawio`（Agent Version Lifecycle 分頁的 active 狀態框註解）、
  `Claude.md`（Agent 段落第 1 點跟新規範互相矛盾的舊敘述）三處提到「最多 2 個」的文字一併更新。

## 為什麼

「最多 2 個 active 版本」原本是 idea.drawio ERD 的既有規格，但隨著 fab-scoped 部署（0011/0012）
成熟，這個人為上限變成一個不必要的瓶頸——`agent_fabs`/`agent_dependencies` 都已經是 per-version、
per-fab 獨立記錄，沒有任何資料模型層的理由要求同時只能有 2 個版本在跑。拿掉上限後，同一個 fab
理論上可以同時被多個 active 版本服務（例如漸進式 rollout、不同 fab 各自停留在不同版本），這是
[docs/history/0012](0012-fab-scoped-agent-dependencies.md) 的 fab-scoped 依賴設計本來就已經預留
的能力。

## 範圍note

Claude.md 這次一併補上了三條新規則（擴充 fab 時要檢查 skill/mcp 版本一致、畫面顯示每版本的
active fab、version 可 deactivate 或軟刪除）——這次改動**只處理**拿掉 2 個上限這一項，其餘三條
還沒實作，留待下次確認範圍後再處理。

## 驗證

`uv run pytest`：104 個測試中 102 通過，另外 2 個失敗（`test_sso.py`）延續 0011/0012 記錄過的既有
環境干擾，跟這次改動無關。前端 `tsc --noEmit` 通過，無型別錯誤。
