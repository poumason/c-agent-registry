# Agent Registry

一個讓使用者建立、審核、打包 agent 的內部平台。目前只完成**後端**（FastAPI + PostgreSQL + MinIO）；前端（React + Ant Design）尚未開始。

需求與 ERD 詳見 [Claude.md](Claude.md) 與 [idea.drawio](idea.drawio)。

## 架構

- `backend/` — FastAPI + SQLAlchemy(async) + Alembic + MinIO
- `docker-compose.yml` — 本機開發用的 Postgres + MinIO（+ 可選的 backend 容器）

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

打開 `http://localhost:5050` 直接進入 pgAdmin（本機用途，設定成不需登入），左側會有
預先建好的 **agent-registry (docker)** 連線，點進去用 `.env` 裡的 `POSTGRES_PASSWORD`
連線即可直接檢查資料表內容。

第一次啟動時，若資料庫沒有任何 admin，系統會依 `.env` 的
`BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` 自動建立第一個管理者帳號
（預設 `admin@example.com` / `change-me-admin`，正式環境請務必更改）。

## 角色模型

- **系統角色**（`User.role`）：`admin`（系統管理）／`reviewer`（可被指定為審核者）／`member`（預設，
  三者在 agent 內容管理上權限相同：建立/修改 agent、建版本、邀請共同編輯者）
- **Per-agent 角色**（`UserAgentRel.role`）：`owner`（建立 agent 的人，唯一，可邀請/移除 editor）／
  `editor`（被邀請的共同編輯者，內容權限與 owner 相同，但不能管理成員）

## 登入方式

- **密碼登入**（`POST /api/v1/auth/login`，OAuth2 password form）：對所有使用者永遠可用，
  不受 SSO 設定影響——admin 建立的帳號、或 SSO 自動建立的帳號，只要 admin 有幫忙設過密碼
  都能用這個方式登入。
- **SSO 登入**（generic OIDC，`GET /api/v1/auth/sso/login`）：導去 `.env` 設定的
  `OIDC_ISSUER`，走 Authorization Code + PKCE，回來後在 `GET /api/v1/auth/sso/callback`
  完成。第一次用某個 email 登入會自動建立帳號，角色固定是 `member`（Claude.md 第 3 點），
  之後同一個 email 再登入就直接對應回同一個使用者，不會覆蓋既有角色。沒設定
  `FRONTEND_SSO_REDIRECT_URL` 時 callback 會直接回傳 JSON token（跟密碼登入格式一樣），
  方便在還沒有前端的現在測試；設定了則會 302 帶著 `#access_token=...` 導去該網址。
  IdP 那邊要註冊 `{BACKEND_BASE_URL}/api/v1/auth/sso/callback` 為允許的 redirect URI。

## 主要流程（走一遍）

1. 以 admin 登入 → `POST /api/v1/users` 建立 member / reviewer 帳號
2. member 登入 → `POST /api/v1/agents` 建立 agent（建立者自動成為該 agent 的 `owner`）
3. （可選）`POST /api/v1/agents/{slug}/members` 邀請其他 member 成為 `editor`
4. `POST /api/v1/agents/{slug}/versions` 建立草稿版本
5. （可選）`POST /api/v1/skills`、`POST /api/v1/mcps` 建立可重用的 skill / mcp，再用
   `POST /api/v1/versions/{version_slug}/dependencies` 掛到版本上
6. `GET /api/v1/reviewers` 查詢可被指定的審核者（系統角色為 `reviewer`/`admin` 的使用者），
   `POST /api/v1/versions/{version_slug}/submit` 提交審核時帶上 `{"reviewer_ids": [...]}` 指定審核者
7. 審核者以 `GET /api/v1/reviews/mine` 查看待審、`POST /api/v1/reviews/{review_id}/decision` 核准或退回
8. 核准後系統自動打包 `agent_card.json` + `install.yaml` + `skills/` 為 zip 上傳到 MinIO，
   `GET /api/v1/versions/{version_slug}/download` 取得預簽名下載連結
9. `POST /api/v1/versions/{version_slug}/activate` 啟用版本（同一 agent 最多 2 個 active 版本）

## 測試

```bash
cd backend
uv run pytest
```

測試會直接對 `docker compose up -d db minio` 啟動的 Postgres / MinIO 執行（每個測試前後會清空資料表），
涵蓋：登入與 RBAC、agent 可見性、版本生命週期與 2-active 上限、審核流程與權限、
skill/mcp 依賴的多型驗證、打包 zip 內容的正確性，以及 SSO 的 state 簽章/過期/防重放、
自動建立帳號的角色預設、既有帳號角色不被覆蓋。SSO 測試把實際打 IdP 的部分
（`app.services.sso.exchange_code`）mock 掉，因為真的走一次 IdP 登入流程沒辦法在 CI 裡穩定重現。

## 已知的、刻意偏離原始 ERD 的地方

詳見 `backend/app/models/`：主要是補上原圖沒畫的
`created_at`/`updated_at`、`Agent.slug`、`AgentVersion.package_path`，以及把 `Review.priorital`
視為打字錯誤改成 `priority`。
