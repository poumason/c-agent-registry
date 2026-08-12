# Agent 建立與共同編輯者

前置條件（全檔共用）：已依 [README.md](../README.md) 的測試帳號規劃準備好 Alice（member）與
Bob（member）兩個帳號，並知道兩人的使用者 ID（可在 Admin > Users 或登入後個人資訊取得，
邀請共同編輯者時要輸入 User ID）。

## TC-2.1 建立 agent（成為 owner）

前置條件：以 Alice 登入。

步驟：
1. 進入 **My Agents**，點擊「新增 Agent」。
2. 填寫 Slug（例如 `invoice-extractor-test`，只能小寫英數字與 `-`）、Name、Description、
   Provider，Visibility 選 `private`。
3. 送出。

預期結果：
- 建立成功，導向該 agent 的 Agent Detail 頁。
- 頁面顯示剛填寫的資訊，Visibility 標示為 Private。
- **Members** 區塊顯示 Alice 為 `owner`。

- [ ] Pass / Fail
備註：

## TC-2.2 Slug 重複或格式錯誤

前置條件：TC-2.1 已建立 slug `invoice-extractor-test`。

步驟：
1. 再次嘗試建立一個 slug 相同（`invoice-extractor-test`）的 agent。
2. 嘗試建立一個 slug 含大寫字母或空白（例如 `Invoice Test`）的 agent。

預期結果：
- 重複 slug：送出後顯示錯誤（衝突），不會建立第二筆。
- 格式錯誤：表單在送出前即提示格式不符（僅允許小寫英數字與 `-`），無法送出。

- [ ] Pass / Fail
備註：

## TC-2.3 編輯 agent 基本資料

前置條件：Alice 登入，且是 TC-2.1 agent 的 owner。

步驟：
1. 進入該 agent 的 Agent Detail，點擊「編輯」。
2. 修改 Name、Description、Provider，並把 Visibility 改成 `public`。
3. 儲存。

預期結果：
- 頁面即時反映修改後的資料與 Visibility 標籤（Public）。

- [ ] Pass / Fail
備註：

## TC-2.4 邀請共同編輯者（editor）

前置條件：Alice 是 owner；已知 Bob 的 User ID。

步驟：
1. 在 Agent Detail 點擊「邀請成員」，輸入 Bob 的 User ID。
2. 送出。

預期結果：
- Members 清單新增 Bob，角色標示為 `editor`。

- [ ] Pass / Fail
備註：

## TC-2.5 editor 有等同 owner 的內容管理權限，但不能管理成員

前置條件：承 TC-2.4，改用 Bob 登入。

步驟：
1. Bob 開啟同一個 agent 的 Agent Detail（可從 My Agents 或直接網址進入，即使 Bob 不是
   owner，也應該看得到並能操作，因為是 editor）。
2. 嘗試：新增 version、編輯 agent 基本資料。
3. 觀察頁面上是否有「刪除 agent」「移除成員」等管理性操作可用。

預期結果：
- 新增 version、編輯 agent 資料皆成功（跟 owner 權限相同）。
- 邀請/移除成員、刪除整個 agent 的操作應該被禁止或畫面上不可用（editor 不能管理成員/
  刪除 agent，只有 owner 或 admin 可以）。

- [ ] Pass / Fail
備註：

## TC-2.6 移除共同編輯者

前置條件：Alice 登入，agent 中已有 Bob 為 editor。

步驟：
1. 在 Members 清單找到 Bob，點擊「移除」。

預期結果：
- Bob 從 Members 清單消失。
- Bob 之後開啟該 agent 的網址（若 Visibility 是 private）應該看不到（見
  [05-browse/visibility-and-search.md](../05-browse/visibility-and-search.md)）。

- [ ] Pass / Fail
備註：

## TC-2.7 Owner 無法被移除

前置條件：Alice 是 owner。

步驟：
1. 在 Members 清單中查看 Alice（owner）這一列，確認是否有「移除」按鈕可操作。

預期結果：
- Owner 這一列不提供移除操作（或操作後被系統拒絕），owner 只能由建立者本人持有，不能被移除。

- [ ] Pass / Fail
備註：

## TC-2.8 第三方 member 看不到別人的 private agent，也不能管理

前置條件：Carol（或任一與該 agent 無關的帳號）登入，且未被邀請加入 TC-2.1 的 private agent。

步驟：
1. 嘗試直接用網址開啟 `/agents/invoice-extractor-test`（或 TC-2.3 之後仍為 private 狀態的
   agent，如果 TC-2.3 已改成 public 則另建一個 private agent測試）。

預期結果：
- 顯示「找不到 agent」（404），不會洩漏此 agent 存在，也無法查看或操作任何內容。

- [ ] Pass / Fail
備註：

## TC-2.9 刪除 agent（僅 owner 或 admin）

前置條件：Alice 登入，是某個測試用 agent 的 owner。

步驟：
1. 在 Agent Detail 點擊「刪除」，確認彈窗後送出。

預期結果：
- 出現二次確認提示。
- 確認後該 agent 從 My Agents 清單消失，直接訪問其網址回應找不到（軟刪除，非硬刪除，但對
  使用者而言等同整個消失）。

- [ ] Pass / Fail
備註：
