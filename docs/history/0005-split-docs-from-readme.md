# 0005 — 把設計文件從 README 拆到 docs/

**Commit**: `49bce26` · 2026-08-05

## 做了什麼

把散在 README.md 裡的設計說明（角色模型、agent 生命週期、SSO 流程、資料模型與 ERD 差異）搬到
`docs/` 底下各自獨立的頁面，並加了 `docs/README.md` 當索引。README.md 瘦身成純粹「怎麼把 repo
跑起來」。

## 為什麼

使用者希望 `Claude.md` 維持是規格與專案開發項目、`README.md` 只放怎麼執行，設計細節跟決策
過程另外放在 `docs/`，三者的角色分清楚。
