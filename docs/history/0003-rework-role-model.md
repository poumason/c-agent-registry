# 0003 — 角色模型改版

**Commit**: `238219c` · 2026-08-05

## 做了什麼

使用者在 Claude.md 重新定義了角色與 agent 的關係，這次改動讓後端跟上：

- 系統角色從 `admin/owner/member` 改成 `admin/reviewer/member`——`owner` 不再是系統角色。
- Per-agent 角色（`User_Agent_Rel`）從 `admin/editor/reviewer` 簡化成 `owner/editor`：建立 agent
  的人是 owner（唯一），被邀請的人是 editor，兩者內容權限相同。
- 送審流程改成由送審者在送審當下明確指定審核者（`POST /versions/{slug}/submit` 帶
  `reviewer_ids`），對象限定系統角色為 `reviewer`/`admin` 的人，取代原本「所有 owner/admin
  自動變成審核者」的做法。
- 寫了一個 Postgres enum migration（rename-type / create-type / `USING CASE`），把既有的
  `owner` 系統角色資料安全地轉成 `member`。

## 為什麼

原本的角色設計（`owner` 當作全域審核權限）跟使用者實際想要的模型不符。使用者用三個步驟的例子
釐清了正確流程：

> 1. userA can create a agent, and default owner is userA
> 2. userA can invite other user to maintain the agent
> 3. when userA submit the agent from draft to staging, must assign a reviewer

## 細節

完整權限矩陣與設計理由見 [docs/roles-and-permissions.md](../roles-and-permissions.md)。
