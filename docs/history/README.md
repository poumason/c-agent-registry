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
