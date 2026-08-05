# 0001 — 後端從零建置

**Commit**: `40c82ca` · 2026-08-05

## 做了什麼

從零建置整個後端：FastAPI + SQLAlchemy(async) + Alembic + PostgreSQL + MinIO，實作 Claude.md
與 idea.drawio ERD 描述的完整資料模型與 API：

- 使用者（系統角色）+ per-agent 成員關係
- Agent → Agent_Version 版本管理，同一 agent 最多 2 個 active 版本
- 送審後依可審核名單寫入 `reviews`
- 審核通過自動打包 `agent_card.json` + `install.yaml` + `skills/` 上傳到 MinIO
- Skill／MCP 登錄與 agent 版本的多型依賴關聯
- Alembic migration、docker-compose（本機 Postgres/MinIO）、pytest 測試（涵蓋 auth、RBAC、
  版本生命週期、審核流程、依賴、打包）

## 為什麼

這是專案的第一版可執行後端，把 Claude.md 的規格與 idea.drawio 的 ERD 轉成實際會動的系統。

## 細節

完整設計細節見 [docs/architecture.md](../architecture.md)（資料模型與 ERD 差異）、
[docs/agent-lifecycle.md](../agent-lifecycle.md)（版本生命週期、打包）。
