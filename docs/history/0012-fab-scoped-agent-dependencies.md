# 0012 — Agent Dependency 的 Fab 級別分流

**Commit**: `da65993` · 2026-08-18

## 做了什麼

Claude.md「FAB 與版本的關係」段落的情境2：一個 version 部署到 F12、F15 兩個廠，如果 F15 的
skill/mcp 出問題需要換掉，0011 的設計（`agent_dependencies` 掛在 version 底下、套用到它部署的
所有 fab）沒辦法只影響 F15。討論過三條路（流程調整退回 draft／開新版本搬 fab／幫
`agent_dependencies` 加 `fab_id`），確認只有加 `fab_id` 能在不分裂版本號、不影響其他 fab 服務的
前提下做到真正的 per-fab 依賴分流。

**後端**：

- `AgentDependency` 新增 `fab_id`（nullable，FK `fabs.id`）。NULL 只有一種意思——這筆依賴沒有
  fab 維度：`type=model`／`source=registry` 永遠 NULL（跟 0011 既有的 fab-agnostic 例外一致），
  `type in (skill, mcp) and source=legacy` 則只在 version 目前沒有部署任何 fab 時允許 NULL，一旦
  部署了 1 個以上的 fab，`fab_id` 就變成必填，且必須是該 version 目前部署的其中一個 fab。
  `uq_agent_dependency` 加入 `fab_id`，並在應用層（`crud/agent_dependency.get_existing`）補上
  重複列檢查——Postgres 的 UNIQUE 對 NULL 一律視為互不相等，DB 層擋不住兩筆 `fab_id=NULL` 的
  重複列。
- `app/services/fab_scope.py` 從「多 fab 集合覆蓋檢查」縮小成「單一 fab_id 合法性檢查」
  （`resolve_dependency_fab_id`）：檢查 fab_id 是不是 version 已部署的 fab、以及該依賴本身是否
  在那個 fab 可用（`skill_fabs`/`mcp_fabs`，MCP 一樣看 per-fab `status`）。原本的
  `uncovered_fabs_for_new_dependency`／`dependencies_uncovered_by` 都移除。
- `PUT /versions/{slug}/fabs`（`set_version_fabs`）拿掉「新 fab 缺依賴要擋」的檢查——依賴既然是
  per-fab 的，部署到一個新 fab 本來就會從「這個 fab 目前沒有任何依賴」開始，跟剛建立一個全新
  version 時依賴是空的一樣正常。這連帶讓情境1（多部署一個 F18）更直接：先加 fab，之後再對它
  個別加依賴即可，不會被舊依賴擋下。
- `services/packaging.py`：同一個邏輯上的依賴現在可能因為分別部署在多個 fab 而變成好幾筆
  `agent_dependency` 列，打包（一個 version 一個 zip，不是 per-fab）前先按
  `(type, source, dependency_id)` 去重，避免 `install.yaml`/zip 內的 skill 檔案重複。
- Alembic migration（`9e0528b844c5`）：加欄位/constraint 之外，把既有的 `type in (skill, mcp)`
  依賴列按它所屬 version 當時部署的 fab 展開（沒部署維持 NULL、部署 1 個直接設、部署多個複製成
  多列），行為不因這次改動而倒退。

**前端**：

- `VersionDetail.tsx` 的新增依賴表單：version 有部署 fab 時多一個必填的「Fab」選單，skill/mcp
  候選清單改成「在目前選定的那一個 fab 可用」（單一 fab 檢查，取代原本的「覆蓋所有部署 fab」子
  集合檢查）；registry 來源的 skill 沒有 fab 維度，不受這個限制。依賴清單顯示每一列所屬的 fab
  名稱。

**範圍確認**：這次**沒有**放寬 `ensure_version_editable`——依賴變更依然只能在 draft/rejected
狀態做，active 版本要換依賴一樣得走完整送審流程。只解決「同一個 version 內部能不能按 fab 分
流」，不解決「active 版本能不能局部 hotfix」（跟使用者確認過，維持現狀）。

## 為什麼

0011 讓「一個 version 部署到哪些 fab」跟「這個 version 依賴哪些 skill/mcp」變成兩個獨立維度，
但依賴本身還是 version 級別的單一份清單——這代表兩個 fab 只要共用同一個 version，就永遠得共用
同一組 skill/mcp，沒有「只換其中一個 fab 的依賴」這個可能。討論過的另外兩條路都有明顯代價：退回
draft 原地改會讓這個 version 服務的所有 fab 一起斷線，且改完後全部 fab 一起吃新依賴；開新版本搬
fab 雖然現有 API 就能做，但會佔用「最多兩個 active 版本」裡的一個名額，且讓 version 歷史依 fab
分岔。把 fab 維度下推到 `agent_dependencies` 本身，讓一個 version 能同時對不同 fab 呈現不同的依賴
組合，不用分裂版本號、不用讓沒問題的 fab 陪著斷線。

## 驗證

`uv run pytest`：`test_fab_scoped_dependencies.py` 整份改寫，11 個案例涵蓋——沒部署 fab 時
新增依賴不用/不能帶 `fab_id`；部署 fab 後新增依賴必須帶且必須是已部署的 fab（帶錯 fab 400、
不帶 400）；帶的 fab_id 要在該 skill/mcp 的可用 fab 內才成功（MCP 一樣驗 per-fab `status`）；
同一個 skill 對兩個不同 fab 各自獨立新增都成功；同一組合重複新增回 409；model 依賴永遠沒有 fab
維度（同時是 `ai_model_crud` 那個既有 bug 的 regression test）；部署到一個目前沒有任何依賴覆蓋的
新 fab 現在直接成功。全專案 104 個測試中 102 個通過，另外 2 個失敗（`test_sso.py`）延續 0011 記錄
過的既有環境干擾（本機 `.env` 的 `FRONTEND_SSO_REDIRECT_URL`），跟這次改動無關，未處理。前端
`tsc --noEmit` 通過，無型別錯誤。`idea.drawio` 補上 `Agent_Dependency.fab_id` 到 `Fab` 表的關聯線
（使用者先前已手動加上這個欄位）。
