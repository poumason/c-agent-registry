# 前端

後端 API 見 [architecture.md](architecture.md)、[roles-and-permissions.md](roles-and-permissions.md)、
[agent-lifecycle.md](agent-lifecycle.md)、[sso.md](sso.md)。這份文件記錄前端（`frontend/`）實際的
技術選型、路由/畫面對應、認證流程——原本是先寫的規劃文件，前端建置完成後已更新為「實際長這樣」，
不再只是預定計畫。UI 風格採用 **Ant Design**，因為這個 app 本質上是 admin/表單/表格為主的後台
工具。

## 技術選型（實際安裝的版本）

| 項目 | 選擇 | 備註 |
|---|---|---|
| Framework | React 19 + TypeScript + Vite | |
| UI 元件庫 | Ant Design v6 | npm 當下的穩定版就是 v6，API 跟 v5 大同小異 |
| 路由 | react-router-dom，釘死 `7.11.0` | 7.12+ 有一個 RSC-mode 專用的 CSRF 安全公告，這個專案是
  純前端 SPA、完全沒用 RSC，公告不適用，但既然有選擇就釘在公告範圍之前的版本 |
| 資料請求/快取 | TanStack Query (React Query) | |
| API client | `axios` 實例（`frontend/src/api/client.ts`），request interceptor 帶 JWT、
  response interceptor 抓 401 清 token 導回登入 | |
| 表單 | Ant Design `Form` 內建 rules | 沒有另外引入 zod，AntD 的 rules 對這裡的表單需求已經夠用 |
| 狀態管理 | React Context（`AuthContext`，只放登入使用者）+ TanStack Query cache | |

## 目錄結構（`frontend/src/`）

```
api/            client.ts(axios instance) + types.ts + 每個 resource 一個檔案
                (agents.ts, versions.ts, reviews.ts, skills.ts, users.ts, auth.ts)
auth/           AuthContext.tsx、ProtectedRoute.tsx
components/     AppLayout.tsx（響應式外殼）、AgentsTable.tsx、tags.tsx（狀態/角色標籤）
pages/          Login, SsoCallback, Browse, MyAgents, AgentDetail, VersionDetail,
                Reviews, Skills, AdminUsers
App.tsx         路由表
main.tsx        QueryClientProvider / ConfigProvider(主色 #4338CA) / AntD App / BrowserRouter / AuthProvider
```

## 路由與畫面對應後端 API

| 路由 | 畫面 | 主要打的 API |
|---|---|---|
| `/login` | 登入（密碼 + SSO 按鈕） | `POST /auth/login`、`GET /auth/sso/login`（整頁導頁） |
| `/sso/callback` | 從 URL fragment 撈 `access_token` 存起來後導回 `/` | — |
| `/`（首頁/Browse） | 瀏覽有權限看到的 agent，預設篩 `visibility=public` | `GET /agents` |
| `/my-agents` | 自己建立的 agent（`created_by === 我`）+ 建立新 agent | `GET /agents`、`POST /agents` |
| `/agents/:slug` | Agent 詳情：版本清單 + 成員（邀請/移除） | `GET /agents/:slug`、`GET .../versions`、
  `GET .../members`、`POST`/`DELETE .../members`、`POST .../versions`（新增草稿版本） |
| `/agents/:agentSlug/versions/:versionSlug` | 版本詳情：參數表單、依賴管理、送審（指定審核者）、
  activate/deactivate、下載、審核紀錄 | `GET/PATCH /versions/:slug`、
  `GET/POST/DELETE .../dependencies`、`POST .../submit`（帶 `reviewer_ids`）、
  `POST .../activate`、`.../deactivate`、`GET .../download`、`GET .../reviews`、`GET /reviewers` |
| `/reviews` | 我的待審清單 | `GET /reviews/mine`、`POST /reviews/:id/decision` |
| `/skills` | Skills（上傳檔案）/ MCP（建立）兩個 tab | `GET/POST /skills`（multipart）、`GET/POST /mcps` |
| `/admin/users` | 使用者管理，只有 `role=admin` 看得到這條路由/選單 | `GET/POST/PATCH /users` |

路由巢狀設計成 `/agents/:agentSlug/versions/:versionSlug` 而不是扁平的 `/versions/:versionSlug`，
是因為 `AgentVersion` 本身沒有帶 agent 的 slug（只有 `agent_id`），巢狀路由讓麵包屑/返回連結不用
額外打 API 查 agent slug。

## Layout / RWD

`components/AppLayout.tsx`：

- 桌面（AntD `Grid.useBreakpoint()` 判斷 `lg` 以上）：固定寬度 224px 的 `Sider`，一直顯示。
- 行動裝置（`lg` 以下）：`Sider` 整個不 render，改成 header 左邊一顆漢堡按鈕，點開一個
  `Drawer`（覆蓋式，不擠壓內容）放同一份選單。

  這是修過一次真的壞掉的版本才定案的做法：一開始用 AntD `Sider` 內建的
  `breakpoint`/`collapsedWidth="0"` 讓它在窄螢幕自動收合、點 trigger 展開——但那個「展開」是
  **推擠版面**（inline push），不是覆蓋（overlay）。在 390px 寬的手機視窗點開選單，`Sider`
  撐到 224px，剩下不到 170px 給內容，標題文字被擠到一個字一行垂直排列。改成獨立的 `Drawer`
  才是正確的手機版導覽模式。
- 版本詳情頁的參數/依賴兩欄版面（`grid-template-columns`）也用同一個 `useBreakpoint()` 在小螢幕
  收成單欄，而不是寫死的 inline style（inline style 沒辦法帶 media query）。
- 各頁面標題列（標題 + 操作按鈕）都加了 `flexWrap: "wrap"`，避免窄螢幕把按鈕擠出畫面。

導覽選單結構對應 Claude.md 的「首頁 / 左側欄位：browse、agent management > my agents」：

```
Browse
Agent Management
  └ My Agents
Reviews
Skills & MCP
Admin（僅 role=admin 顯示）
  └ 使用者管理
```

## 認證流程

1. `/login`：密碼表單直接呼叫 `POST /auth/login`；「使用 SSO 登入」按鈕
   `window.location.href = ssoLoginUrl()`（整頁導轉，不是 fetch，因為要讓瀏覽器走完 IdP 的頁面）。
2. 後端 `.env` 的 `FRONTEND_SSO_REDIRECT_URL` 設成 `http://localhost:5173/sso/callback`；該頁面
   從 URL fragment（`#access_token=...`）撈 token 存起來，`refresh()` 換使用者資料後導回 `/`。
3. Token 存 `localStorage`（`agent_registry_token`）。之後若要上正式環境，可以評估換成
   httpOnly cookie 以降低 XSS 風險，但那需要後端配合改成 cookie-based session，目前先不做。
4. `axios` instance 的 request interceptor 自動帶 `Authorization: Bearer <token>`；response
   interceptor 抓到 401 就清掉 token、導回 `/login`。
5. App 啟動時（有 token 的話）打一次 `GET /auth/me` 換使用者資料存進 `AuthContext`；
   `ProtectedRoute` 在這個請求完成前顯示 loading，避免畫面閃一下又被導走。

後端另外補了 `CORSMiddleware`（`CORS_ALLOW_ORIGINS`，預設含 `http://localhost:5173`）——這是
接前端時才發現的缺口，之前只有後端自己測試（curl/pytest）不會踩到瀏覽器的 CORS 限制。

## 角色/權限在前端怎麼呈現

前端**不重新實作**後端的權限邏輯，只做「不該看到的操作就不要顯示」這種 UX 層級的處理，真正的
權限判斷永遠以後端回應（403）為準——這點有實際驗證過：登入一個只有 `reviewer` 系統角色、不是
任何 agent 成員的帳號，直接呼叫版本頁的「啟用」按鈕（前端沒特別擋這顆按鈕），後端正確回
403，前端沒有因此壞掉，只是操作沒有生效。

- `Admin` 選單：`user.role === 'admin'`
- 「核准/退回」：只在 `/reviews`（我的待審清單）出現，因為那份清單本來就只會回傳指派給自己、
  還在 pending 的 review

## 已知限制 / 之後可以補的

- **My Agents 只顯示 `created_by === 我`**：目前沒有一個「我是哪些 agent 的 editor」的後端
  查詢，所以「My Agents」實際上只涵蓋自己建立（owner）的 agent，被別人邀請成 editor 的 agent
  不會出現在這個列表（但還是能透過直接連結 `/agents/:slug` 存取，權限檢查沒問題，只是列表
  頁找不到入口）。要修的話，後端需要新增一個「我是成員的 agent」查詢。
- **邀請成員要手動輸入 user id（UUID）**：後端沒有「搜尋使用者」的公開 API（`GET /users`
  是 admin-only），所以 Agent 詳情頁的邀請表單只能請使用者去問 admin 要 user id 貼上去，
  不是選人下拉選單。之後可以加一個所有登入使用者都能打的、只回傳 id/name/email 的輕量使用者
  搜尋端點（模式類似 `GET /reviewers`）。
- **OpenAPI 型別自動產生**：`frontend/src/api/types.ts` 目前手動對照 `backend/app/schemas/*.py`
  維護，之後可以換成 `openapi-typescript` 讀 `/openapi.json` 自動產生，減少手動同步的維護成本。
