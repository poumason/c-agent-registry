# Agent Registry

一個讓使用者建立、審核、打包 agent 的內部平台。目前只完成**後端**（FastAPI + PostgreSQL +
MinIO）；前端（React + Ant Design）尚未開始。

- 規格與需求：[Claude.md](Claude.md)、[idea.drawio](idea.drawio)
- 設計細節與決策紀錄：[docs/](docs/)

這份文件只講怎麼把 repo 跑起來。

## 快速開始

```bash
cp .env.example .env
docker compose up -d db minio pgadmin

cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

打開 `http://localhost:8000/docs` 查看互動式 API 文件。

第一次啟動時，若資料庫沒有任何 admin，系統會依 `.env` 的
`BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` 自動建立第一個管理者帳號
（預設 `admin@example.com` / `change-me-admin`，正式環境請務必更改）。

SSO 是選用的，`.env.example` 裡的 `OIDC_*` 留空就停用；要開的話見
[docs/sso.md](docs/sso.md)。

## pgAdmin（檢查資料庫用）

打開 `http://localhost:5050` 直接進入（本機用途，設定成不需登入），左側會有預先建好的
**agent-registry (docker)** 連線，點進去用 `.env` 裡的 `POSTGRES_PASSWORD` 連線即可直接檢查
資料表內容。

## 測試

```bash
cd backend
uv run pytest
```

測試會直接對 `docker compose up -d db minio` 啟動的 Postgres / MinIO 執行（每個測試前後會清空
資料表）。SSO 測試把實際打 IdP 的部分 mock 掉，因為真的走一次 IdP 登入流程沒辦法在 CI 裡穩定
重現。

## Docker Compose 建置完整 stack

```bash
docker compose up -d
```

`backend` 容器會自動跑 `alembic upgrade head` 再啟動（見 `docker-compose.yml`）。
