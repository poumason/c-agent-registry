# 0008 — 補齊使用者權限 / Agent 編輯的落差

**Commit**: `f3a1179` · 2026-08-06

## 做了什麼

使用者要求重新比對 Claude.md 跟現有實作，找「使用者權限」與「agent 編輯」相關的落差。比對後找到
5 個具體缺漏，逐一補上：

1. **使用者刪除**：`DELETE /users/{id}`（admin only），軟刪除（`deleted_at`），擋 admin 刪除
   自己（409）。刪除後密碼登入失敗、既有 token 也失效。
2. **Agent 修改**：`PATCH /agents/{slug}`（name/description/provider/visibility，不含
   slug），owner/editor/admin 都能改。
3. **Agent 刪除**：`DELETE /agents/{slug}`，軟刪除，只有 owner/admin 能刪。刪除後這個 agent
   從列表、直接連結、子路由（版本等）全部變成 404。
4. **送審 fallback**：`reviewer_ids` 改成可選，不指定時自動 fan-out 給所有系統角色
   `reviewer`/`admin` 的使用者（排除送審者自己）。
5. **打包路徑**：從 `packages` bucket 根目錄的 `{version_slug}.zip`，改成
   `{agent_id}/{version_slug}.zip`，符合 Claude.md 明講的路徑結構。

另外使用者中途追加一條需求：admin 要能在使用者管理頁直接調整某人的系統角色（例如 member 設成
reviewer）——這個能力後端本來就有（`PATCH /users/{id}` 一直都能改 `role`），缺的只是前端沒有
UI，補了一個 Select 讓 admin 可以直接在表格裡改。這條規則也同步寫回 Claude.md（「基本功能：
建立，啟動，刪除，調整角色」）。

## 為什麼

Claude.md 的權限表明講「建立/修改/刪除 agent」三個都要打勾，使用者管理明講「建立，啟動，刪除」
三個動作，但實作只做了建立跟部分啟動/停用，這次是把落差補齊。

軟刪除是跟使用者確認過的設計決策：硬刪除在目前的資料模型下會直接撞外鍵約束（agent 建立時就有
owner 的 `UserAgentRel`，使用者也常常是別的資料列的 `created_by`），要嘛加 cascade 遷移、要嘛
軟刪除，使用者選軟刪除，改動範圍小很多。

## 驗證

`uv run pytest`：36 個測試全過（新增 5 個涵蓋這次的改動：agent 編輯、editor 不能刪但 owner
可以、刪除後 404、使用者刪除後無法登入、admin 刪除自己被擋、送審不指定審核者的 fallback、
打包路徑格式）。另外在瀏覽器對著真的跑起來的服務走了一次：建使用者→改角色→刪除、建
agent→編輯→刪除，過程中 console 全程沒有任何錯誤或警告。

## 細節

完整權限矩陣、軟刪除設計見 [roles-and-permissions.md](../roles-and-permissions.md)；打包路徑
細節見 [agent-lifecycle.md](../agent-lifecycle.md)。
