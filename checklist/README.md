# 手動測試 Checklist

這個目錄收錄 Agent Registry 五個核心情境的手動驗收測試劇本，供測試人員按步驟操作、勾選結果。
規劃緣由與範圍取捨記錄在 [PLANNING.md](PLANNING.md)。

## 目錄結構

| 目錄 | 對應情境 |
|---|---|
| [01-authentication](01-authentication/) | 登入（帳號密碼、SSO） |
| [02-agent-management](02-agent-management/) | member 建立 agent、多個 version、設定 mcp/skill/model 依賴 |
| [03-review-workflow](03-review-workflow/) | 送審、指定 reviewer、reviewer 審核 |
| [04-admin](04-admin/) | admin 設定使用者角色（把 member 變成 reviewer）與使用者管理 |
| [05-browse](05-browse/) | Browse 畫面：member 看得到 public agent 與自己建立的 agent |

每個檔案內的測試案例格式固定：

```
### TC-x.y 案例標題
前置條件：...
步驟：
1. ...
2. ...
預期結果：...
- [ ] Pass / Fail（測試人員填寫）
備註：
```

`- [ ]` 是給測試人員實際勾選/記錄結果用的欄位，不代表案例本身還沒定義完整。

## 測試環境準備

以下步驟只需做一次，讓所有情境共用同一份跑起來的環境。

```bash
cp .env.example .env
docker compose up -d db minio pgadmin

cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

另開一個終端機跑前端（需要 Node.js >= 20.19，`frontend/.nvmrc` 已釘版本）：

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

打開 `http://localhost:5173`。

### Bootstrap admin 帳號

後端第一次啟動、資料庫沒有任何 admin 時，會依 `.env` 的 `BOOTSTRAP_ADMIN_EMAIL` /
`BOOTSTRAP_ADMIN_PASSWORD` 自動建立第一個 admin（預設 `admin@example.com` /
`change-me-admin`）。所有情境的 admin 操作都用這個帳號登入即可，不需要另外建立。

### 測試帳號規劃

完整跑完五個情境，建議在開始前（或依 [04-admin](04-admin/manage-reviewers-and-users.md) 的步驟）
準備下列帳號，全部透過 admin 帳號在 **Admin > Users** 頁面建立：

| 帳號代稱 | 系統角色 | 用途 |
|---|---|---|
| Admin | admin | Bootstrap 帳號，管理使用者/角色，做為 oversight reviewer |
| Alice | member（測試中途升級為 reviewer） | agent owner，02、03 情境的主角 |
| Bob | member | 被邀請的共同編輯者（editor），也用來驗證「看不到別人的 private agent」 |
| Carol | reviewer | 專職 reviewer，03 情境的審核者 |

每個測試案例的「前置條件」會標明實際要用到哪些帳號，不是每個案例都要用滿以上四個。

### SSO 測試（選用）

[01-authentication/sso-login.md](01-authentication/sso-login.md) 需要一組可用的 OIDC 提供者
（例如 GitLab.com 的 Application），並在後端 `.env` 填入 `OIDC_ISSUER` / `OIDC_CLIENT_ID` /
`OIDC_CLIENT_SECRET`，且該 OIDC 應用程式的 callback URL 必須註冊成
`http://localhost:8000/api/v1/auth/sso/callback`。沒有配置 SSO 也不影響其他情境——帳號密碼登入
永遠可用。

## 已知範圍限制

- `04-admin` 只涵蓋「設定 reviewer 角色」與基本使用者管理，不含 Admin 選單下的
  Review Summary / Agent Summary / Stats / Agent Templates / SkillHub Registry 等統計與同步頁面。
- `02-agent-management` 的依賴設定目前只能選 **skill** 或 **mcp**，Registry > Model
  頁面建立的模型目前不能被選為 agent version 的依賴（前端 `DependencyType` 只有
  `"skill" | "mcp"` 兩種）。詳見 PLANNING.md 的說明。
