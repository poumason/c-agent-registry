# Agent Registry

一個讓使用者建立、審核、打包 agent 的內部平台。目前只完成**後端**（FastAPI + PostgreSQL + MinIO）；前端（React + Ant Design）尚未開始。

需求與 ERD 詳見 [Claude.md](Claude.md) 與 [idea.drawio](idea.drawio)。

## 架構

- `backend/` — FastAPI + SQLAlchemy(async) + Alembic + MinIO
- `docker-compose.yml` — 本機開發用的 Postgres + MinIO（+ 可選的 backend 容器）

## 快速開始

```bash
cp .env.example .env
docker compose up -d db minio

cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

打開 `http://localhost:8000/docs` 查看互動式 API 文件。

第一次啟動時，若資料庫沒有任何 admin，系統會依 `.env` 的
`BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` 自動建立第一個管理者帳號
（預設 `admin@example.com` / `change-me-admin`，正式環境請務必更改）。

## 主要流程（走一遍）

1. 以 admin 登入 → `POST /api/v1/users` 建立 owner / member 帳號
2. member 登入 → `POST /api/v1/agents` 建立 agent（建立者自動取得該 agent 的 `admin` 權限）
3. `POST /api/v1/agents/{slug}/versions` 建立草稿版本
4. （可選）`POST /api/v1/skills`、`POST /api/v1/mcps` 建立可重用的 skill / mcp，再用
   `POST /api/v1/versions/{version_slug}/dependencies` 掛到版本上
5. `POST /api/v1/versions/{version_slug}/submit` 提交審核 —
   系統會依「系統角色為 owner/admin」與「該 agent 的 admin/reviewer 成員」名單寫入 `reviews`
6. 審核者以 `GET /api/v1/reviews/mine` 查看待審、`POST /api/v1/reviews/{review_id}/decision` 核准或退回
7. 核准後系統自動打包 `agent_card.json` + `install.yaml` + `skills/` 為 zip 上傳到 MinIO，
   `GET /api/v1/versions/{version_slug}/download` 取得預簽名下載連結
8. `POST /api/v1/versions/{version_slug}/activate` 啟用版本（同一 agent 最多 2 個 active 版本）

## 測試

```bash
cd backend
uv run pytest
```

測試會直接對 `docker compose up -d db minio` 啟動的 Postgres / MinIO 執行（每個測試前後會清空資料表），
涵蓋：登入與 RBAC、agent 可見性、版本生命週期與 2-active 上限、審核流程與權限、
skill/mcp 依賴的多型驗證、以及打包 zip 內容的正確性。

## 已知的、刻意偏離原始 ERD 的地方

詳見 `backend/app/models/`：主要是補上原圖沒畫的
`created_at`/`updated_at`、`Agent.slug`、`AgentVersion.package_path`，以及把 `Review.priorital`
視為打字錯誤改成 `priority`。
