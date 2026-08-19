# 修改紀錄

每一次比較大的 commit，這裡都會有一篇對應的摘要：改了什麼、為什麼改。目的是讓之後回來看的人（包含
未來的自己）不用回去翻 commit diff 或聊天記錄，就知道每個階段的決策脈絡。細節設計文件在
[docs/](../) 底下的其他頁面，這裡只放「這次改動」層級的摘要，會隨時間增加。

| # | Commit | 日期 | 摘要 |
|---|---|---|---|
| 0001 | [`40c82ca`](0001-initial-backend-scaffold.md) | 2026-08-05 | 後端從零建置（FastAPI + PostgreSQL + MinIO） |
| 0002 | [`c03b0cf`](0002-add-pgadmin.md) | 2026-08-05 | docker-compose 加入 pgAdmin |
| 0003 | [`238219c`](0003-rework-role-model.md) | 2026-08-05 | 角色模型改版：per-agent owner/editor + 送審時指定審核者 |
| 0004 | [`4de2f45`](0004-add-sso-login.md) | 2026-08-05 | 加入通用 OIDC SSO 登入 |
| 0005 | [`49bce26`](0005-split-docs-from-readme.md) | 2026-08-05 | 把設計文件從 README 拆到 docs/ |
| 0006 | [`5661116`](0006-agent-card-erd-sync.md) | 2026-08-05 | ERD 圖同步角色改版後的欄位命名 |
| 0007 | [`4df2258`](0007-add-frontend.md) | 2026-08-05 | 前端從零建置（React + Vite + Ant Design） |
| 0008 | [`f3a1179`](0008-close-permission-gaps.md) | 2026-08-06 | 補齊使用者/agent 權限落差：軟刪除、agent 編輯、送審 fallback、打包路徑、角色調整 UI |
| 0009 | [`0f71324`](0009-erd-sync-with-live-schema.md) | 2026-08-10 | idea.drawio 的 ERD 同步成目前 PostgreSQL 的實際 schema |
| 0010 | [`9445703`](0010-registry-sync.md) | 2026-08-10 | 新增 Registry 分類（Skill/MCP/Model）+ 同步機制，agent version 依賴選單改為只列可用項目 |
| 0011 | [`244d2fd`](0011-fab-scoped-dependency-validation.md) | 2026-08-17 | Agent version 依賴的同廠區（fab）強制驗證：新增依賴/變更部署廠區都要通過覆蓋檢查 |
| 0012 | [`da65993`](0012-fab-scoped-agent-dependencies.md) | 2026-08-18 | Agent Dependency 的 fab 級別分流：同一個 version 能對不同 fab 用不同 skill/mcp |
| 0013 | [`尚未 commit`](0013-remove-active-version-cap.md) | 2026-08-19 | 拿掉「同一 agent 最多 2 個 active 版本」的上限 |
| 0014 | [`尚未 commit`](0014-per-fab-tabs-in-version-detail.md) | 2026-08-19 | Version Detail 頁面：部署 URL／依賴／Agent Card 改成 per-fab tabs |
