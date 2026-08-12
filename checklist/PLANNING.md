# Checklist 規劃紀錄

## 使用者原始需求

> 我需要撰寫測試劇情，讓我可以請人按照測試的步驟驗證以下功能：
> 1. 登入（SSO 登入與藉由帳號密碼登入）
> 2. member 可以建立 agent，多個 agent version，設定需要用到的 mcp, skill 與 models
> 3. 建立好的 agent version 可以設定 reviewer 來審核
> 4. admin 可以設定誰變成 reviewer
> 5. browse 的畫面，member 可以看到被設定為 public 與自己建立的 agent
>
> 請幫我看照這幾個重點，寫成對應的測試 markdown，存在 `./checklist` 目錄下，可以按測試範圍不同
> 分不同的目錄與檔案。然後把規劃的內容也紀錄下來。

## 撰寫前的確認方式

沒有直接照著 Claude.md 的規格描述寫測試，而是先讀了目前的實作（backend endpoints、
`core/agent_access.py`/`permissions.py` 的權限判斷邏輯、`docs/roles-and-permissions.md`、
frontend 的 `Login.tsx`/`AgentDetail.tsx`/`VersionDetail.tsx`/`ReviewQueue.tsx`/
`ReviewDetail.tsx`/`AdminUsers.tsx`/`Browse.tsx`），確保每個測試案例的「預期結果」跟現在
真正跑起來的行為一致，而不是規格文件當初設想、後來又被使用者澄清調整過的版本（例如審核者
指定方式、per-agent 角色簡化成 owner/editor 兩種，都是開發過程中跟規格文件不同步的地方，
`docs/roles-and-permissions.md` 裡有記錄這些調整的來龍去脈）。

## 目錄與檔案切分方式

使用者要求「可以按測試範圍不同分不同的目錄與檔案」，因此直接按五個重點分成五個目錄，
其中內容較多的情境（agent 管理、review 流程）各自再拆成兩個檔案，避免單一檔案過長：

```
checklist/
  README.md                                    索引 + 環境準備 + 測試帳號規劃
  PLANNING.md                                  本檔案
  01-authentication/
    password-login.md                          帳密登入的成功/失敗/停用帳號情境
    sso-login.md                                SSO 登入、自動建立 users 資料列、重複登入不重建
  02-agent-management/
    create-agent-and-editors.md                 建立/編輯/刪除 agent、邀請共同編輯者、權限邊界
    agent-versions-and-dependencies.md          多版本、送審前的編輯限制、依賴（skill/mcp）設定
  03-review-workflow/
    submit-for-review.md                        送審、指定/不指定 reviewer 的兩種路徑
    reviewer-decision.md                        reviewer 在 Review Queue / Review Detail 核准或退回
  04-admin/
    manage-reviewers-and-users.md               admin 建立使用者、調整角色（member→reviewer）、停用
  05-browse/
    visibility-and-search.md                    public/internal/private 在 Browse 兩個 tab 下的可見性
```

## 每個情境的設計取捨

### 1. 登入

帳密登入跟 SSO 登入分成兩個檔案，因為 SSO 需要額外的外部依賴（OIDC 提供者、真實帳號），
測試人員可能沒有環境可以跑，拆開後可以獨立跳過不影響其他情境的驗收進度。

SSO 案例特別涵蓋「用同一個外部帳號第二次登入，不會重複建立 `users` 資料列」——這是
`crud/user.get_or_create_by_sso`（以 email 比對既有使用者）的行為，也是這個 session 前段
使用者明確想要驗證的重點（「因為我要檢查 user 這個 table 會寫入什麼」），值得寫成獨立案例
而不只是口頭提醒。

### 2. Agent 管理

拆成「agent 本身 + 共同編輯者」跟「version + 依賴」兩個檔案，因為前者是一次性設定，後者
會在整個生命週期反覆操作（每個 version 都要重新設定依賴），測試人員使用時通常是分開跑的。

寫作時發現一個跟使用者這次需求描述不完全一致的地方：使用者提到「設定需要用到的 mcp, skill
與 models」，但目前 `frontend/src/api/types.ts` 的 `DependencyType` 只有 `"skill" | "mcp"`
兩種，`VersionDetail.tsx` 的新增依賴表單也只有 Skill/MCP 兩個選項——Registry > Model
頁面（`RegistryModels.tsx`）目前只能建立/同步模型清單本身，還沒有串接成 agent version
可選的依賴類型。這不是文件疏漏，是目前程式碼真實的功能範圍。

處理方式：`agent-versions-and-dependencies.md` 的依賴設定案例只寫 skill/mcp 兩種（照實際
可操作的畫面撰寫），並在案例中加一條「確認 Model 目前不是可選依賴類型」的案例，讓測試人員
知道這是已知現狀而不是要去找的 bug；同時在 README.md 的「已知範圍限制」重申一次。

### 3. 送審與審核

`docs/roles-and-permissions.md` 記錄了審核者指定的規則是「指定為可選」：有給 `reviewer_ids`
就驗證每個都是 active 的 reviewer/admin 且不是自己；不給就 fallback 成所有 reviewer/admin
（排除送審者）。這兩條路徑都各自寫成獨立案例（TC-3.1 指定審核者、TC-3.2 不指定的
fallback），而不是只測其中一種，因為這是這次規格反覆澄清出來、容易被誤測成「一定要指定」的
地方。

`reviewer-decision.md` 額外涵蓋兩個容易被忽略的邊界：
- reject 沒有填寫理由會被前端擋下（`ReviewQueue.tsx`/`ReviewDetail.tsx` 都有這個檢查）。
- 不是被指派的 reviewer（也不是 admin）嘗試核決會被後端擋下（403 "Not your review"），
  對應 `reviews.py` `decide_review` 的權限檢查——admin 則有 oversight bypass，可以代為決定
  任何人的 pending review，這條也拆出來單獨驗證，因為容易被誤解成「reviewer 才能審」。

### 4. Admin 設定 reviewer

只涵蓋「調整角色」與最基本的使用者建立/停用/自己不能停用自己，不涵蓋 Admin 選單下其他統計類
頁面（Review/Agent/User Summary、Stats、Agent Templates、SkillHub Registry 同步）——這些不在
使用者這次列出的五個重點裡，範圍已在 README.md 的「已知範圍限制」寫明，避免測試人員誤以為
遺漏。

### 5. Browse

依 `ensure_agent_visible`（`backend/app/core/agent_access.py`）的邏輯設計案例：`public`/
`internal` 對所有登入使用者可見，`private` 只有 admin、owner、editor、被指派審核的 reviewer
看得到。Browse 頁面的 Public/All 兩個 tab 只是加一層「visibility == public」的前端過濾，
不影響底層可見性判斷，所以案例特別包含「internal agent 在 Public tab 應該看不到，但在
All tab 對任何登入使用者都看得到」這種容易漏測的組合，對應使用者原始需求「member 可以看到
被設定為 public 與自己建立的 agent」——這句話沒提到 internal，實測時要注意 internal 的可見
範圍其實比字面上的「public + 自己的」更寬。

## 測試帳號設計

四個代稱帳號（Admin / Alice / Bob / Carol）夠涵蓋所有情境需要的角色組合（owner、editor、
reviewer、oversight admin、以及「看不到別人 private agent 的第三方member」），不用每個情境
重新建帳號；帳號規劃統一寫在 README.md，各案例的「前置條件」只標注實際會用到哪幾個代稱。
