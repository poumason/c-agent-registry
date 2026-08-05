# 0002 — docker-compose 加入 pgAdmin

**Commit**: `c03b0cf` · 2026-08-05

## 做了什麼

在 `docker-compose.yml` 加入 `pgadmin` 服務，跑在 desktop mode（不需登入，本機用途），並預先放好
`backend/pgadmin/servers.json` 連線設定，開啟就有一條指到 compose 裡 Postgres 的連線可以直接用。

## 為什麼

使用者需要一個方便檢查資料庫內容是否正確的工具，不用另外裝 client 或手動設定連線。
