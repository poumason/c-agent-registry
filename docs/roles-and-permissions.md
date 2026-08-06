# 角色與權限設計

對應 Claude.md 的使用者/角色需求。這個系統有**兩層**角色，容易搞混，先講清楚：

- **系統角色**（`User.role`）：整個系統範圍的身份，跟哪個 agent 無關。
- **Per-agent 角色**（`UserAgentRel.role`，對應 ERD 的 `User_Agent_Rel` / `Asset_Role`）：
  某個使用者「在某一個 agent 底下」的權限，跟系統角色是獨立的兩件事。

## 系統角色（`UserRole`：`admin` / `reviewer` / `member`）

> 這個列舉原本是 `admin` / `owner` / `member`（`owner` 是「可以審核任何人的 agent」的全域角色）。
> 使用者在開發過程中重新定義了規格：`owner` 不再是系統角色，變成純粹 per-agent 的概念（見下），
> 系統角色改成 `admin` / `reviewer` / `member`。這個改動連帶了一個 Postgres enum migration
> （`backend/alembic/versions/80066d16e0ee_rework_role_enums.py`），用
> rename-type / create-type / `USING CASE` 的方式做，並把既有資料安全地對應過去
> （舊的 `owner` 系統角色 → `member`）。

三個角色在「agent 內容管理」這塊權限**完全相同**——建立/修改 agent、建版本、邀請共同編輯者，
member/reviewer/admin 都可以做。差異只有：

| 功能 | member | reviewer | admin |
|---|:---:|:---:|:---:|
| 建立/修改/建版本/邀共同編輯者 | ✅ | ✅ | ✅ |
| 可被指定為審核者 | ❌ | ✅ | ✅ |
| 可以管理任何 agent（即使不是該 agent 的 owner/editor） | ❌ | ❌ | ✅ |
| 建立/啟用停用/刪除使用者、調整使用者角色 | ❌ | ❌ | ✅ |

`admin` 的「可以管理任何 agent」是唯一的系統層級 bypass（`backend/app/core/permissions.py`
`can_manage_agent`/`can_administer_agent` 裡對 `UserRole.admin` 的特殊處理）；`reviewer` 沒有這個
bypass——是 reviewer 只代表「有資格被指定為審核者」，不代表可以直接編輯別人的 agent。

**新使用者只能由 admin 建立**（`POST /api/v1/users`，需要 admin token），沒有公開註冊。SSO
自動建立的帳號固定是 `member`（見 [sso.md](sso.md)）。admin 之後也能透過 `PATCH /users/{id}`
調整任何使用者的角色（例如把 member 設成 reviewer）、狀態（active/disabled），或
`DELETE /users/{id}` 軟刪除（見下方「軟刪除」）——前端使用者管理頁三個都有對應的操作介面。

admin **不能刪除自己的帳號**（`DELETE /users/{id}` 若 `id` 是呼叫者自己會回 409）——這是防呆，
不是 Claude.md 明講的規則，避免不小心把系統唯一的 admin 鎖在外面。

## Per-agent 角色（`AssetRole`：`owner` / `editor`）

> 這個列舉原本是 `admin` / `editor` / `reviewer`（審核者是透過被邀請成這個 agent 的
> `reviewer`/`admin` 來決定審核資格）。規格重新定義後，審核資格改成**送審時由送審者明確指定**
> （見下方「送審與審核者指定」），不再跟 per-agent 角色綁在一起，所以這個列舉簡化成只剩
> `owner`/`editor` 兩種，語意也更單純：owner 是建立者，editor 是被邀請的協作者，兩者「能做的事」
> 完全一樣，差別只在能不能管理成員。

- **`owner`**：建立這個 agent 的人，`POST /api/v1/agents` 時自動寫入，每個 agent 恰好一個 owner。
  可以邀請/移除 `editor`（`POST`/`DELETE /agents/{slug}/members`），owner 本身**不能被移除**
  （沒有「轉移擁有權」的功能——這是刻意的最小實作範圍，不是規格要求排除）。
- **`editor`**：被 owner 邀請的共同編輯者。內容權限跟 owner 完全一樣（建版本、改參數、加依賴、
  送審），但不能管理成員（邀請/移除別人）。

權限判斷邏輯集中在 `backend/app/core/permissions.py`：

```python
def can_manage_agent(user, membership):      # 建版本/改參數/加依賴/送審/修改 agent 基本資料
    return user.role == UserRole.admin or membership is not None   # owner 或 editor 都算

def can_administer_agent(user, membership):   # 邀請/移除成員、刪除整個 agent
    return user.role == UserRole.admin or (membership and membership.role == AssetRole.owner)
```

`PATCH /agents/{slug}`（改 name/description/provider/visibility，不含 slug）用
`can_manage_agent`——owner/editor 都能改。`DELETE /agents/{slug}` 用 `can_administer_agent`——
只有 owner（或系統 admin）能刪，跟管理成員的權限層級一致，避免任何一個 editor 就能把整個 agent
連同其他人的版本一起刪掉。

## 送審與審核者指定

Claude.md 規格經過兩輪釐清：先是用例子確認「送審時由送審者指定審核者」（不是自動 fan-out 給
所有夠格的人，也不是要先被邀請成這個 agent 的審核者才能審）：

> 1. userA can create a agent, and default owner is userA
> 2. userA can invite other user to maintain the agent
> 3. when userA submit the agent from draft to staging, must assign a reviewer

後來 Claude.md 又補了一句，把「指定」改成可選、沒指定時要有 fallback：「agent 被 submit 時需要
指定擁有 reviewer 權限的使用者來進行審核（**如果沒有指定就是按 agent 可被審核的人數清單來寫入
reviews**）」。

目前實作是這兩輪的合併：**指定是可選的**。

流程：`GET /api/v1/reviewers` 列出所有系統角色 `reviewer`/`admin` 的使用者供選擇 → `POST
/versions/{slug}/submit` 帶 `{"reviewer_ids": [...]}`：
- **有給** `reviewer_ids`：後端驗證每個 id 都存在、是 active、系統角色是 `reviewer`/`admin`、
  而且不是自己，全部通過才建立對應的 `Review`（`pending`）。
- **不給**（空陣列/不帶這個欄位）：後端呼叫跟 `/reviewers` 同一個 `list_reviewer_candidates()`
  （`backend/app/services/reviewers.py`），排除送審者自己，替**所有**系統角色
  `reviewer`/`admin` 的使用者各建一筆 `Review`。

兩種情況都是「清單是空的」就回 409（沒有可審核的人）。任一 reviewer 核准 → 版本變 `approved`
並觸發打包；任一 reviewer 退回 → 版本變 `rejected`（其他還沒決定的 review 就不處理了，這是目前
最簡單的「誰先決定就算數」策略，之後如果要改成「需要全部核准」或「多數決」，改動點在
`backend/app/api/v1/endpoints/reviews.py` 的 `decide_review`）。

## 軟刪除

Agent 跟 User 都是軟刪除——`deleted_at` 給個時間戳記，資料列不會真的消失（避免要處理外鍵
cascade：agent 建立當下就會有一筆 owner 的 `UserAgentRel`，user 也常常已經是某些 agent/skill/
review 的 `created_by`/`reviewer_id`，硬刪除會直接撞外鍵約束失敗）。

所有讀取路徑（`crud/agent.py`、`crud/user.py` 的 `get_by_*`/`list_*`）預設都會過濤掉
`deleted_at IS NOT NULL` 的資料列，所以被刪除的 agent/使用者是「整個消失」，不是「列表隱藏但
直接連結還能開」——被刪除的 agent 直接連結會 404（包含它底下的 version 路由），被刪除的使用者
密碼登入會回帳密錯誤、既有 token 也會失效（`get_current_user` 走同一個過濾過的查詢）。
