# Reviewer 審核決策

前置條件（全檔共用）：至少一個 version 已送審且指定 Carol（reviewer）為審核者，狀態
`in_review`（見 [submit-for-review.md](submit-for-review.md) 的 TC-3.1）。

## TC-3.7 Reviewer 在 Review Queue 看到待審項目

前置條件：Carol 登入。

步驟：
1. 進入 **Review Queue**（左側 Reviews 選單），確認分頁在「Pending」。

預期結果：
- 清單出現指定給 Carol 的待審項目，顯示 agent 名稱、version 編號、送審者名稱。
- 一般 member（非 reviewer/admin）登入後訪問 `/review-queue` 應顯示無權限，看不到任何清單
  內容。

- [ ] Pass / Fail
備註：

## TC-3.8 核准（Approve）

前置條件：Carol 登入，Review Queue 或 Review Detail 中有指定給她的 pending 項目。

步驟：
1. 點擊該筆的「核准」，可選填備註。
2. 確認送出。

預期結果：
- 該筆 Review 狀態變成 `approved`。
- 對應的 Agent Version 狀態變成 `approved`，並自動觸發打包（`agent_card.json`、
  `install.yaml`、`skills/` 會被壓成 zip 放進 MinIO）。
- Version Detail 出現「下載封裝檔」按鈕，可成功下載（同
  [02-agent-management/agent-versions-and-dependencies.md](../02-agent-management/agent-versions-and-dependencies.md)
  的 TC-2.20）。

- [ ] Pass / Fail
備註：

## TC-3.9 退回（Reject）且未填理由會被擋下

前置條件：另一筆 pending review（送審一個新 version 走 TC-3.1 流程）。

步驟：
1. Carol 在 Review Queue 或 Review Detail 點擊「退回」，理由欄位留空直接送出。

預期結果：
- 送出被前端擋下，顯示「退回必須填寫理由」之類的提示，不會呼叫 API、Review 狀態維持
  pending。

- [ ] Pass / Fail
備註：

## TC-3.10 退回並填寫理由

步驟：
1. 承 TC-3.9，填入退回理由文字。
2. 送出。

預期結果：
- Review 狀態變成 `rejected`，理由文字被儲存。
- 對應 Agent Version 狀態變成 `rejected`。
- 該理由會顯示在：Review Queue 該列、Review Detail、以及 Agent Version 頁面的 Review
  History 中。

- [ ] Pass / Fail
備註：

## TC-3.11 已決定的 review 不能重複決定

前置條件：承 TC-3.8 或 TC-3.10，該筆 review 已有結果（非 pending）。

步驟：
1. 嘗試再次對同一筆 review 呼叫核准或退回（例如直接開啟該 Review Detail 頁面觀察操作按鈕
   是否還存在）。

預期結果：
- Review Detail 顯示已有的結果與理由，不再提供核准/退回的操作按鈕（畫面上判斷
  `result !== pending` 即不可再決定）。

- [ ] Pass / Fail
備註：

## TC-3.12 未被指派的使用者不能代為決定他人的 review

前置條件：另一位 reviewer（非 Carol，例如把 Bob 也升成 reviewer）登入；有一筆指定給 Carol
的 pending review。

步驟：
1. 該其他 reviewer 嘗試開啟 Carol 那筆 review 的 Review Detail，並嘗試核准/退回。

預期結果：
- 操作被拒絕（顯示「不是你的審核項目」或按鈕本身不可用），該筆 review 狀態不受影響。

- [ ] Pass / Fail
備註：

## TC-3.13 Admin 可以代為決定任何人的 pending review（oversight）

前置條件：Admin 帳號登入；有一筆指定給 Carol 的 pending review。

步驟：
1. Admin 進入 **Review Queue**，確認能看到系統中**所有** reviewer 的 pending 項目（不像
   一般 reviewer 只看得到指定給自己的）。
2. 對指定給 Carol 的那筆項目執行核准或退回。

預期結果：
- Admin 的 Review Queue 顯示全部 reviewer 的待審項目（oversight 視角），一般 reviewer 只
  看得到自己的。
- Admin 可以成功核准/退回原本指定給 Carol 的項目，結果與 TC-3.8/TC-3.10 相同，
  `signoff_by` 記錄為 Admin。

- [ ] Pass / Fail
備註：

## TC-3.14 一般 member 的「My Reviews」與 Review Queue 權限

前置條件：Alice（member，非 reviewer）登入。

步驟：
1. 訪問 `/reviews`（My Reviews）與 `/review-queue`。

預期結果：
- `/reviews` 可正常進入（任何登入使用者都能看自己「被指派」的審核，Alice 目前沒有被指派
  過任何審核，清單應為空）。
- `/review-queue` 顯示無權限（僅 reviewer/admin 可用）。

- [ ] Pass / Fail
備註：
