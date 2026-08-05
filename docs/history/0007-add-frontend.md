# 0007 — 前端從零建置

**Commit**: 見本次 push 的最新 commit · 2026-08-05

## 做了什麼

在 `frontend/` 建置 React + TypeScript + Vite + Ant Design v6 前端，對接既有的後端 API：

- 認證：密碼登入 + SSO 登入（導頁）並存，`AuthContext` 管理登入狀態，`GET /auth/me` 換使用者資料
- RBAC 只在 UI 層做「不該看到的就不顯示」（例如 Admin 選單只有 `role=admin` 看得到），真正的權限
  判斷永遠以後端回應為準——中途特意測過一次「reviewer 點了不該他按的『啟用』按鈕」，後端正確擋
  掉（403），前端沒有因此壞掉
- 頁面：Login、SSO callback、Browse（首頁，公開/可見 agent 瀏覽）、My Agents（自己建立的
  agent）、Agent 詳情（版本清單 + 成員管理）、版本詳情（參數表單、依賴管理、送審指定審核者、
  activate/deactivate、下載安裝包、審核紀錄）、Reviews（待審佇列）、Skills & MCP、Admin 使用者
  管理
- RWD：桌面用固定 Sider，行動裝置（`lg` 以下）改用漢堡選單觸發的 `Drawer` 覆蓋式導覽（一開始
  用 AntD `Sider` 的 `collapsedWidth=0` 做，會把內容往右推擠導致標題文字被擠成逐字換行，改用
  `Drawer` 才是正確的覆蓋式行為）；版本詳情頁的兩欄 grid 在小螢幕會收成單欄

## 為什麼

Claude.md 新增了「前端開發」章節，明確要求密碼+SSO 同時提供登入、注意 RWD、首頁瀏覽已核准
agent、My Agents 列表、agent 詳情頁點版本看細節。這次建置照著這些要求走，UI 風格延續先前確認的
Ant Design。

## 驗證

沒有用 mock 資料——整個開發過程都是對著真的跑起來的後端（`docker compose up -d db minio` +
`uv run uvicorn`）用瀏覽器工具實際操作：建帳號、建 agent、建版本、指定審核者送審、核准、確認
自動打包、真的下載了 zip 檔、啟用版本、換角色登入驗證權限邊界、切到手機尺寸驗證 RWD。過程中
抓到並修掉的真實問題：

- 後端沒有 CORS middleware（前端打不通，補上 `CORSMiddleware` + `CORS_ALLOW_ORIGINS` 設定）
- Sider 推擠式收合在窄螢幕造成標題文字逐字換行（換成 Drawer 覆蓋式導覽）
- 版本詳情頁兩欄 grid 用行內 style 沒有響應式斷點（改用 `Grid.useBreakpoint()` 動態切換）
- 幾個 AntD v6 API 用法過時的警告（`message` 靜態方法、`Space direction`、`Tag bordered`、
  `Drawer width`）

## 細節

技術選型、路由/畫面對應、認證流程見 [docs/frontend-plan.md](../frontend-plan.md)（已更新為
實際建置後的狀態，不再只是規劃）。
