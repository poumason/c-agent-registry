# 架構設計

> 規格與需求見 [Claude.md](../Claude.md)、原始 ERD 見 [idea.drawio](../idea.drawio)。這份文件記錄
> 「規格怎麼落地成現在的系統」——技術選型、目錄結構、資料模型，以及與原始 ERD 之間刻意的差異。

## 技術選型

| 項目 | 選擇 | 原因 |
|---|---|---|
| Web framework | FastAPI + Uvicorn | async、自動產生 OpenAPI（`/docs`） |
| ORM | SQLAlchemy 2.0（async）+ asyncpg | 型別安全、async session |
| Migration | Alembic | 搭配 SQLAlchemy models 自動產生 |
| 資料驗證 | Pydantic v2 / pydantic-settings | 與 FastAPI 原生整合 |
| 認證 | JWT（python-jose）+ bcrypt（passlib） | 無狀態、多種登入方式（密碼／SSO）共用同一張票 |
| 物件儲存 | MinIO（`minio` SDK） | S3 相容、可本機 docker-compose 起 |
| 套件管理 | `uv` | 已安裝在開發機上，比 pip/poetry 快 |
| 測試 | pytest + pytest-asyncio + httpx `ASGITransport` | 直接對 docker-compose 起的 Postgres/MinIO 跑，不 mock DB |

## 目錄結構（`backend/`）

```
app/
  core/       # 設定(config.py)、JWT/密碼(security.py)、權限判斷(permissions.py)、
              # FastAPI 依賴注入(deps.py)、agent 存取共用邏輯(agent_access.py)
  db/         # SQLAlchemy Base、async engine/session
  models/     # ORM models，一個檔案一張表 + enums.py 集中放所有列舉
  schemas/    # Pydantic Create/Update/Read schema，一個檔案對一個 model
  crud/       # 純資料庫存取函式，一個檔案對一個 model
  services/   # 跨 model 的商業邏輯：storage.py(MinIO)、packaging.py(打包 zip)、
              # reviewers.py(誰可以當審核者)、sso.py(OIDC)
  api/v1/endpoints/  # FastAPI router，一個檔案對一個資源
alembic/      # migrations
tests/        # pytest，對應 endpoints 的功能分組（不是逐檔案對應）
```

分層規則：`endpoints` 只做「取資料 → 檢查權限 → 呼叫 crud/services → 回傳」，商業邏輯（誰能審核、
何時打包、最多幾個 active 版本）都收斂在 `core/permissions.py`、`core/agent_access.py`、
`services/*.py`，方便之後前端或其他 client 需要同樣邏輯時直接重用。

## 前端（`frontend/`）

React + TypeScript + Vite + Ant Design v6，透過 `VITE_API_BASE_URL` 打後端的 `/api/v1` REST
API（純前端 SPA，不是後端渲染）。技術選型細節、目錄結構、路由對應、RWD 設計見
[frontend-plan.md](frontend-plan.md)。

## Docker Compose 服務

- `db` — Postgres 16
- `minio` — 物件儲存（skills 原始檔 + packages 打包後的 zip 兩個 bucket，啟動時自動建立）
- `pgadmin` — 本機用途，desktop mode（免登入），預先建好連線設定
- `backend` — 開發用容器（`--reload`），本機開發也可以不進容器直接 `uv run uvicorn`

前端目前是純本機開發（`npm run dev`），還沒有加進 docker-compose。

## 資料模型與原始 ERD 的差異

`idea.drawio` 的 ERD 是這個系統的起點，但有些欄位/型別是圖上沒畫、實作時必須補上的：

- **所有 PK 用 UUID**，除了 `Agent_Version.slug`（字串 PK，格式 `{agent.slug}-v{version}`，例如
  `image-classifier-v3`）—— ERD 上這張表的 PK 本來就標示 `slug` 而不是 `id`。
- `Agent.slug`：ERD 只有 `id`，但需要一個 URL-safe 的唯一識別碼，所以加了 `slug`（unique）。
- `created_at` / `updated_at`：補在 ERD 上沒畫出時間戳記的表（`User`、`Agent`、`User_Agent_Rel`、
  `Agent_Dependency`）——這是標準的稽核欄位，不算規格變更。
- `Agent_Version.package_path`（nullable）：審核通過後產生的 zip 在 MinIO 裡的 object key。ERD
  沒有對應欄位，但「產生 zip 檔案」這個規格需要有地方記錄它存在哪，所以加在這裡而不是另開一張表。
- `Review.priorital` → 實作成 `priority: int`（型別是整數優先度）。判斷是原 ERD 的打字錯誤
  （"priorital" 不是英文字），直接照 "priority" 的意思實作。
- Enum 都用 Postgres native enum（`SQLAlchemy Enum`），完整列表見
  [roles-and-permissions.md](roles-and-permissions.md) 與 `backend/app/models/enums.py`。

## Agent_Dependency 的多型設計

ERD 上 `Agent_Dependency` 有 `dependency_id` + `type` 兩個欄位，同時有邊分別連到 `Skill.id` 和
`MCP.id`——代表這是一張多型（polymorphic）關聯表：`type` 是 `skill` 或 `mcp`，`dependency_id`
依 `type` 指向 `skills.id` 或 `mcps.id`。因為指向的表不固定，資料庫層沒有外鍵約束，改在
`POST /versions/{version_slug}/dependencies` 這一層用程式驗證 `dependency_id` 真的存在於對應的表
（`backend/app/api/v1/endpoints/dependencies.py`）。
