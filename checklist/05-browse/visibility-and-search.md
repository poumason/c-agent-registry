# Browse 畫面與可見性

前置條件（全檔共用）：準備三個各自不同 visibility 的 agent（都用 Alice 建立）：
- `browse-test-private`：Visibility = `private`，Alice 為 owner，Bob 未被邀請。
- `browse-test-internal`：Visibility = `internal`。
- `browse-test-public`：Visibility = `public`。

建立方式見 [02-agent-management/create-agent-and-editors.md](../02-agent-management/create-agent-and-editors.md)
的 TC-2.1。

## TC-5.1 Public agent 對任何登入使用者可見

前置條件：Bob（member，與這三個 agent 都無關）登入。

步驟：
1. 進入 **Browse**，確認分頁在「Public」。
2. 搜尋或滾動找到 `browse-test-public`。

預期結果：
- `browse-test-public` 出現在 Public 分頁清單中，Bob 可以點進去查看基本資訊（唯讀，因為
  Bob 不是 owner/editor）。

- [ ] Pass / Fail
備註：

## TC-5.2 Internal agent 不在 Public 分頁，但在「All」分頁對任何登入使用者可見

前置條件：Bob 登入。

步驟：
1. 在 Browse 的 Public 分頁搜尋 `browse-test-internal`。
2. 切換到「All」（`browse.allVisible`）分頁，再次搜尋。

預期結果：
- Public 分頁**看不到** `browse-test-internal`（該分頁只列出 `visibility=public` 的
  agent）。
- All 分頁**看得到** `browse-test-internal`——`internal` 對任何已登入使用者都是可見的，
  不需要是成員。Bob 可以點進去查看（唯讀）。

- [ ] Pass / Fail
備註：

## TC-5.3 Private agent 對無關的 member 完全不可見

前置條件：Bob 登入，未被邀請加入 `browse-test-private`。

步驟：
1. 在 Browse 的 Public 與 All 兩個分頁都搜尋 `browse-test-private`。
2. 嘗試直接用網址 `/agents/browse-test-private` 開啟。

預期結果：
- 兩個分頁都找不到這個 agent。
- 直接用網址開啟得到「找不到 agent」（404），不會洩漏 agent 是否存在。

- [ ] Pass / Fail
備註：

## TC-5.4 Owner 在 Browse／My Agents 都看得到自己的 private agent

前置條件：Alice（owner）登入。

步驟：
1. 進入 **My Agents**，確認 `browse-test-private` 出現在清單中。
2. 進入 **Browse** 的「All」分頁，搜尋 `browse-test-private`。

預期結果：
- My Agents 一定看得到（自己建立的 agent，不受 visibility 影響）。
- Browse 的 All 分頁也看得到（`ensure_agent_visible` 對建立者本人放行），Public 分頁則
  看不到（因為它仍是 private，不符合 Public 分頁的過濾條件）。

- [ ] Pass / Fail
備註：

## TC-5.5 Editor 看得到被邀請的 private agent

前置條件：Alice 已把 Bob 加為 `browse-test-private` 的 editor（參考
[create-agent-and-editors.md](../02-agent-management/create-agent-and-editors.md) 的
TC-2.4）。

步驟：
1. Bob 登入，進入 Browse 的「All」分頁搜尋 `browse-test-private`。

預期結果：
- 找得到，且可以點進去操作（editor 權限，同 TC-2.5）。

- [ ] Pass / Fail
備註：

## TC-5.6 被指派審核的 reviewer 即使不是成員也看得到 private agent

前置條件：`browse-test-private` 有一個 version 已送審並指定 Carol（reviewer）為審核者
（見 [03-review-workflow/submit-for-review.md](../03-review-workflow/submit-for-review.md)），
但 Carol 未被加為此 agent 的 editor。

步驟：
1. Carol 登入，進入 Browse 的「All」分頁搜尋 `browse-test-private`，或直接從 Review Queue
   點入該版本連結。

預期結果：
- Carol 能看到並開啟這個 agent/version（因為有一筆指派給她的審核紀錄），即使她從未被邀請
  成為成員。

- [ ] Pass / Fail
備註：

## TC-5.7 Admin 在 All 分頁看得到所有 agent

前置條件：Admin 登入。

步驟：
1. 進入 Browse 的「All」分頁，搜尋 TC 準備的三個 agent（public/internal/private）。

預期結果：
- 三個都找得到（admin 對任何 agent 的可見性有全域 bypass）。

- [ ] Pass / Fail
備註：

## TC-5.8 搜尋與排序

前置條件：Browse 中已有多筆可見的 agent。

步驟：
1. 在搜尋框輸入關鍵字（agent 名稱的一部分）。
2. 切換排序（Newest / Oldest / Name A-Z）。

預期結果：
- 搜尋結果只顯示名稱/描述符合關鍵字的 agent。
- 排序切換後清單順序正確改變。

- [ ] Pass / Fail
備註：

## TC-5.9 分頁（Pagination）

前置條件：可見的 agent 總數足以跨頁（可調整每頁筆數觀察，或建立足夠多筆測試 agent）。

步驟：
1. 調整每頁顯示筆數。
2. 點擊下一頁/上一頁。

預期結果：
- 分頁筆數與頁碼正確反映總筆數，切換頁面後顯示不同的 agent，不重複也不遺漏。

- [ ] Pass / Fail
備註：
