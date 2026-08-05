# 設計文件

這裡放的是「規格怎麼落地成現在的系統」的設計細節與決策紀錄。規格本身（需求、角色、ERD）維持在
[Claude.md](../Claude.md)；怎麼把這個 repo 跑起來見根目錄的 [README.md](../README.md)。

- [architecture.md](architecture.md) — 技術選型、目錄結構、資料模型與原始 ERD 的差異
- [roles-and-permissions.md](roles-and-permissions.md) — 系統角色 vs per-agent 角色、權限矩陣
- [agent-lifecycle.md](agent-lifecycle.md) — Agent/Version 狀態機、送審與審核者指定、打包流程
- [sso.md](sso.md) — SSO（OIDC）登入設計
