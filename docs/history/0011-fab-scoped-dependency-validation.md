# 0011 — Agent Version 依賴的同廠區（Fab）強制驗證

**Commit**: `244d2fd` · 2026-08-17

## 做了什麼

延續 0009/schema spec（`docs/superpowers/specs/2026-08-12-fab-scoped-schema-design.md`）已經
建好的 `fabs`/`agent_fabs`/`mcp_fabs`/`skill_fabs` junction tables，這次補上這幾張表存在的
真正原因——使用者的規則：**一個 agent version 部署在哪些廠區，它的每個 skill/mcp 依賴就必須在
「所有」那些廠區都可用，否則拒絕**（跟使用者確認過是嚴格擋下，不是允許但示警）。在這之前，
`agent_fabs`/`skill_fabs`/`mcp_fabs` 的 CRUD 端點（`efbcbae`、`64b4f61`）已經存在，但送審依賴
新增（`POST /versions/{slug}/dependencies`）跟部署廠區變更（`PUT /versions/{slug}/fabs`）
兩個端點完全不知道彼此的存在，沒有任何交叉驗證。

**後端**：

- 新增 `app/services/fab_scope.py`：集中放兩個方向的覆蓋檢查——
  `uncovered_fabs_for_new_dependency`（新增依賴時，這個候選項目在 version 目前部署的哪些廠
  不可用）跟 `dependencies_uncovered_by`（變更部署廠區時，現有依賴在新的廠區組合下少了哪些
  覆蓋）。AI Model 依賴跟 registry 來源（SkillHub Registry）的 skill 沒有 fab 維度，一律視為
  永遠覆蓋（沒有 `model_fabs` 表，這是 spec 裡原本就講清楚的既有決定，不是這次新增的例外）。
- `POST /versions/{slug}/dependencies`：新增依賴前呼叫 `uncovered_fabs_for_new_dependency`，
  有缺漏就回 409，訊息帶出缺哪些廠（用廠名 `fab` 字串而非 UUID，方便閱讀）。
- `PUT /versions/{slug}/fabs`：套用新的廠區組合前呼叫 `dependencies_uncovered_by`，任何既有
  依賴會因此變成覆蓋不到就整批拒絕，訊息列出是哪個依賴、缺哪個廠。
- 順手修掉一個檢查過程中發現、跟這次改動無關但就在同一個函式裡的既有 bug：
  `add_dependency` 對 `type=model` 的存在性檢查原本錯誤地查 `mcp_crud` 而不是
  `ai_model_crud`，導致任何 model 依賴都會回 404、`model` 這個依賴型別實際上完全不能用。

**前端**：

- `VersionDetail.tsx` 的依賴選單過濾邏輯從「至少在 version 部署的某一個廠可用」（`.some(...)`）
  改成「在 version 部署的每一個廠都可用」（`coversDeployedFabs`，子集合檢查），跟後端的
  嚴格規則對齊。Version 還沒設定任何部署廠區時維持不限制（空集合的子集合關係永遠成立）。

## 為什麼

Schema 層的 junction table 設計本身已經是對的（多對多關係的必然結果，詳見設計討論），但光有
`agent_fabs`/`skill_fabs`/`mcp_fabs` 三張表，沒有東西真的去讀它們做交叉驗證，「同 fab 依賴」
這條規則就只是資料庫裡存在著沒人用的資訊。這次補的是規則本身，不是加新表——`agent_dependencies`
維持 fab-agnostic（一個依賴邏輯上還是「這個 version 依賴這個 skill」，不會因為 version 部署兩個
廠就變成兩筆重複紀錄），驗證改成查詢期的集合運算，兩個方向都要顧到：只擋新增依賴不夠，因為使用者
也可能反過來先加依賴、再把 version 部署到一個依賴不支援的新廠。

## 驗證

`uv run pytest`：新增 `test_fab_scoped_dependencies.py`，7 個案例涵蓋——未部署任何廠區時不受
限制、新增依賴時缺廠會被擋下（訊息帶廠名）、依賴覆蓋所有部署廠區時允許、MCP 依賴看的是
per-fab `status`（模擬 sync 後變成 unavailable，即使有指派到該廠也視為不可用）、model 依賴
不受 fab 限制且確認走 `ai_model_crud`（順帶驗證 bug 已修好）、部署到新廠時若依賴缺漏會被擋下、
依賴覆蓋新廠時允許。全專案 101 個測試中 99 個通過，另外 2 個失敗（`test_sso.py`）是這個 session
稍早測試 SSO 登入時，本機 `.env` 留下 `FRONTEND_SSO_REDIRECT_URL` 設定值造成的既有環境干擾，
跟這次改動無關，未處理。前端 `tsc --noEmit` 通過，無型別錯誤。
