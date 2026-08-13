# 廠區（Fab）維度 schema 擴充 — 設計文件

Status: approved by user (design phase), 2026-08-12.

## 目標

這次只動 **schema**（SQLAlchemy models + 一支 Alembic migration），不動 API / CRUD / 前端 —
邏輯留到下一個 commit。目的是讓 schema 能表達：

- Agent 的展示/驗證用中繼資料（icon、category、hello_msg、example_questions、audience、
  doc_url）。
- 同一隻 agent 的不同 version 會部署在不同廠區（fab），每個 (version, fab) 組合有自己的
  k8s service URL。
- MCP／Skill 也有廠區維度：MCP 的 host 是每廠各自的網路端點；Skill 是存在 MinIO 的檔案，
  廠區維度只是「這個 skill 在哪些廠可用」的可用性標記。
- `agent_dependencies` 之後除了 skill/mcp，還要能表示對 AI Model 的依賴（`type=model`）。

## 背景 / 現況

現有 schema（`backend/app/models/`）：`Agent`（UUID PK, slug/name/description/provider/
visibility）、`AgentVersion`（slug 當 PK，帶 `url` 欄位存 agent 對外服務位址）、`MCP` /
`Skill`（各自的 `host`/`bucket_path`、`status`、`last_synced_at`，全域一份、不分廠）、
`AgentDependency`（`dependency_id` 是 String，靠 `(type, source)` 決定要去哪張表解析，
docstring 已載明「no DB-level FK, since it can point into any of several tables/stores
depending on (type, source)」）。目前完全沒有廠區（fab）概念。

## 一、新增/異動的表

### 1. `agents` — 新增 5 欄

| 欄位 | 型別 | Nullable | Default |
|---|---|---|---|
| `icon_path` | `String(1024)` | Y | — |
| `category` | `ARRAY(String)` | N | `['tool']` |
| `hello_msg` | `Text` | Y | — |
| `example_questions` | `ARRAY(String)` | N | `[]` |
| `audience` | `String(500)` | Y | — |
| `doc_url` | `String(2048)` | Y | — |

`icon_path` 是 MinIO object key（比照 `Skill.bucket_path`），null 時前端套內建預設圖 —
上傳 API、bucket 設定、預設圖規則都是下一個 commit 的邏輯範圍。`category` / `tags` 同款：
`ARRAY(String)` 自由字串，不做 enum 限制。`audience` 先當單一字串欄位（PAT 驗證值），
之後如果要支援多值再改 `ARRAY(String)`。

### 2. `agent_versions`

- **移除** `url`（搬到 `agent_fabs.url`，因為 url 現在是「這個 version 在這個廠」的屬性，
  不再是 version 自身的屬性）。
- **新增** `skills`：`JSONB`，`nullable=False, default=[]`。存的是使用者在 create agent
  時填寫、組出來的 agent card skills 資料。命名沿用需求原文的 `skills`，但會在欄位旁加註解
  跟 `Skill` model／`agent_dependencies` 的 skill 依賴區分，避免之後讀 code 混淆成同一件事。

### 3. 新表 `fabs`

| 欄位 | 型別 |
|---|---|
| `id`（PK） | `UUID`，比照全專案 `UUIDPKMixin` |
| `fab` | `String`，UNIQUE, NOT NULL |

只有 `id`/`fab` 兩欄，沒有 `created_at`/`updated_at`（這張表變動頻率極低，新開廠才會
insert 一筆）。

### 4. 新表 `agent_fabs`

| 欄位 | 型別 |
|---|---|
| `fab_id`（PK, FK→`fabs.id`） | `UUID` |
| `agent_version_slug`（PK, FK→`agent_versions.slug`） | `String(255)` |
| `created_at` / `updated_at` | timestamp |
| `url` | `String(2048)`, nullable |

命名確認：欄位是 `agent_version_slug`（不是 `agent_slug`），FK 指向 `agent_versions.slug`
——因為部署的最小單位是「某個 version」，一個 version 可以對應多筆不同廠區的部署記錄。

### 5. 新表 `mcp_fabs`

| 欄位 | 型別 |
|---|---|
| `mcp_id`（PK, FK→`mcps.id`） | `UUID` |
| `fab_id`（PK, FK→`fabs.id`） | `UUID` |
| `host` | `String(1024)`, NOT NULL |
| `status` | `AvailabilityStatus` enum |
| `last_synced_at` | timestamp, nullable |
| `created_at` / `updated_at` | timestamp |

對應地，`mcps` 表**移除** `host`、`status`、`last_synced_at` 三欄（改成每廠各自一份）。

⚠️ **既有 API 會暫時壞掉**：`POST /mcps/sync`、`app/api/v1/endpoints/mcps.py`、
`app/schemas/mcp.py` 的 `MCPRead` 都直接讀這三個欄位。這次 commit 合併後到下一個邏輯
commit 之前，MCP 相關 API 會因為 ORM 欄位消失而打不動。**使用者已確認接受這段過渡期。**

⚠️ **既有資料遷移**：目前 `mcps` 表裡任何既有 row 的 `host`/`status`/`last_synced_at`
在欄位搬遷後沒有 `fab_id` 可掛（`fabs` 表是全新的，沒有「這筆 host 屬於哪個廠」的歷史資訊）。
這次 migration **直接捨棄這三欄的既有資料**（欄位跟著資料一起被 drop，不做搬遷 insert），
不建立任何 placeholder fab row。這是本地/開發階段資料，接受這個處理方式；如果之後發現正式
環境已經有需要保留的 MCP host 資料，migration 要在套用前重新評估。

### 6. 新表 `skill_fabs`（純 junction）

| 欄位 | 型別 |
|---|---|
| `skill_id`（PK, FK→`skills.id`） | `UUID` |
| `fab_id`（PK, FK→`fabs.id`） | `UUID` |
| `created_at` | timestamp |

`skills` 表本身不變（skill 內容存在 MinIO，全域共用，廠區維度只是可用性標記，沒有
`updated_at`——沒有可變狀態需要追蹤異動時間）。

### 7. `agent_dependencies` / `DependencyType` enum

- **不新增欄位**。`dependency_id` 維持 `String`，仍然「靠 `type` 決定去哪張表解析」，不做
  DB 層 FK（一個欄位不可能同時是三張表的 FK constraint）。
- `DependencyType` enum 新增一個值：`model`（`skill` / `mcp` / `model`）。Migration 用
  `ALTER TYPE dependency_type ADD VALUE 'model'`，跟現有 `f64afce7bce0`（把
  `DependencySource` 一次建好兩個值）不同模式，因為 `dependency_type` 這個 enum 型別已經
  存在於 DB 裡，只能用 `ADD VALUE` 追加。
- 更新 `app/models/enums.py` 裡 `DependencySource` docstring 的過期敘述——目前寫「Agent
  Templates and Model aren't dependency types at all」，「Model」的部分要拿掉（Agent
  Templates 仍然不是）。
- **這次不做 `model_fab`**：AI Model 走中心化 provider API（例如統一打同一個 Anthropic/
  OpenAI endpoint），不像 MCP 是每廠 k8s 各自部署，沒有分廠的必要（使用者已確認）。

## 二、命名慣例調整

使用者原話裡的表名是 `fab`（單數）、`mcp_fab`、`skill_fab`（單數）。這份 spec 統一改成
**複數**：`fabs`、`mcp_fabs`、`skill_fabs`，理由是這個專案裡所有既有表名都是複數
（`agents`、`agent_versions`、`mcps`、`skills`、`ai_models`、`agent_dependencies`、
`reviews`、`users`），沒有例外。`agent_fabs` 使用者原話就是複數，維持不變。**這是本次唯一
一處沒有照字面採用使用者原始命名的地方，需要使用者在 review 這份 spec 時特別確認是否同意。**

## 三、明確排除在這次 commit 之外（下一個邏輯 commit 處理）

- Icon 上傳 API、MinIO bucket 設定（新 bucket 或沿用既有 bucket 的哪個 prefix）。
- `audience` 欄位的實際驗證邏輯、是否要改成多值。
- `agent_versions.skills` JSON 的欄位結構（哪些子欄位、怎麼從表單組出來）。
- `mcps.py` API／`MCPRead` schema／`POST /mcps/sync` 改寫成讀 `mcp_fabs`。
- `agent_dependencies` 對 `dependency_id` 的既有 `String` 欄位是否要在未來棄用，這次不動。
- Fab 管理 CRUD API（新增/刪除廠區）、Agent_Fabs／MCP_Fabs／Skill_Fabs 的管理 API 與前端
  畫面。

## 四、Migration 技術備忘

- `DependencyType` 用 `ALTER TYPE ... ADD VALUE`，在 Postgres 12+ 可以跟其他 DDL 在同一次
  `alembic upgrade` 內執行，只要**不在同一支 migration 裡緊接著用到這個新值**（例如寫一筆
  `type='model'` 的資料）就不會撞到「新值不能在同一個 transaction 裡被使用」的限制——這次
  migration 只加值，不寫資料，安全。
- `mcp_fabs` / `skill_fabs` / `agent_fabs` 都是複合 PK（兩欄位一起當 PK），不用
  `UUIDPKMixin`，比照 `AgentDependency` 現有的 `UniqueConstraint` 寫法但這次是真的複合
  PK，不是加在 UUID PK 之外的 unique constraint。
- `fabs` 表要先建、且要有至少 15 筆 seed 資料（F01–F15 之類）才有意義，但**這次 migration
  不做 data seed**——seed 屬於邏輯/運維範疇，留給使用者或下一個 commit 自行決定怎麼建。
