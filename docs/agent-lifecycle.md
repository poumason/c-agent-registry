# Agent / Version 生命週期與打包

## 狀態機（`AgentVersion.status`）

```
draft --submit--> in_review --approve--> approved --activate--> active
                       |                                            |
                       +--reject--> rejected                    deactivate
                                                                      |
                                                                      v
                                                                  approved
```

- 一個 `Agent` 可以有多個 `Agent_Version`（版本），版本的 PK 是字串 `slug`
  （`{agent.slug}-v{version}`），`version` 是遞增整數（`backend/app/crud/agent_version.py`
  `next_version_number`）。
- **同一個 agent 最多 2 個 `active` 版本**（Claude.md 規格），在
  `POST /versions/{slug}/activate` 裡用 `count_active()` 檔在資料庫層之前擋掉
  （`backend/app/api/v1/endpoints/agent_versions.py`，常數 `MAX_ACTIVE_VERSIONS_PER_AGENT = 2`）。
- 只有 `draft` 狀態的版本能改參數（`PATCH /versions/{slug}`）跟改依賴
  （`POST`/`DELETE /versions/{slug}/dependencies`）——送審之後就鎖住，避免審核中途改東西。

## Skill / MCP 依賴

`Skill`、`MCP` 是兩張獨立、可重複使用的登錄表（跟哪個 agent 無關），各自有自己的
`POST`/`GET` endpoint。`Agent_Dependency` 是多型的關聯表（見
[architecture.md](architecture.md#agent_dependency-的多型設計)），在建立版本、還是
`draft` 狀態時掛上去：`POST /versions/{slug}/dependencies { "dependency_id": ..., "type": "skill"|"mcp" }`。

`Skill` 上傳時是 multipart（`POST /skills`，帶檔案），檔案直接存進 MinIO 的 `skills` bucket，
`bucket_path` 記錄 object key；`MCP` 沒有檔案，只是記錄 host/version 等中繼資料
（`POST /mcps`，純 JSON）。

## 打包（審核通過後）

審核通過（`POST /reviews/{id}/decision` 傳 `approved`）的當下，
`backend/app/services/packaging.py` 的 `generate_package_for_version` 會同步執行：

1. 查這個版本掛的所有 `Agent_Dependency`
2. 組 `agent_card.json`——`Agent` 的中繼資料（name/description/provider）+ 這個版本的參數
   （`url`/`streaming`/`default_input_modes`/`default_output_modes`），欄位命名對齊
   A2A（Agent2Agent）協定的 AgentCard 格式
3. 組 `install.yaml`——列出 `skills`（含 name/version/category）跟 `mcp`（含 name/version/host）
4. 把每個 skill 依賴的檔案從 MinIO `skills` bucket 抓下來，放進 zip 的 `skills/<skill 名稱>/` 底下
5. 全部打包成 zip，上傳到 MinIO 的 `packages` bucket，object key 存回
   `AgentVersion.package_path`

下載走 `GET /versions/{slug}/download`，回傳的是 MinIO 預簽名 URL（1 小時有效），不是直接把檔案
串流過我們的 API——沒 approve 過（`package_path` 是 `null`）會回 409。

## 為什麼審核通過就馬上打包，而不是等 activate

Claude.md 只說「在 agent 被 review 通過後，會產生 zip 檔案」，沒有提到要等 activate。這樣設計的
好處是 `approved` 但還沒 `active` 的版本也能先下載下來檢查內容——`activate` 純粹是「這個版本現在
是不是對外服務中」的開關，跟「這個版本有沒有產出可用的安裝包」是兩件事。
