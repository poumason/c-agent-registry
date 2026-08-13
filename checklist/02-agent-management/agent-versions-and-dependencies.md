# Agent Version 與依賴（MCP / Skill / Model）

前置條件（全檔共用）：Alice（member）已依
[create-agent-and-editors.md](create-agent-and-editors.md) 的 TC-2.1 建立好一個 agent，並以
Alice 身份登入。

依賴設定前，建議先在 **Registry > Skill** 與 **Registry > MCP** 各自建立至少一筆可用
（status = available）的項目，做法見 TC-2.14、TC-2.15。

## TC-2.10 建立多個 version

步驟：
1. 在 Agent Detail 點擊「新增 Version」，可留空 Endpoint URL 直接建立。
2. 重複一次，再建立第二個 version。

預期結果：
- Agent Detail 的 Version 清單出現 `v1`、`v2` 兩筆，狀態皆為 `draft`。
- 每個 version 有獨立的 slug（例如 `invoice-extractor-test-v1`、`...-v2`）。

- [ ] Pass / Fail
備註：

## TC-2.11 編輯 draft 狀態的 version 參數

前置條件：TC-2.10 的 `v1` 仍是 `draft`。

步驟：
1. 點入 `v1` 的 Version Detail。
2. 填寫 Endpoint URL、切換 Streaming 開關。
3. 儲存參數。

預期結果：
- 儲存成功，畫面即時反映新的 Endpoint URL 與 Streaming 狀態。

- [ ] Pass / Fail
備註：

## TC-2.12 加入 Skill 依賴

前置條件：Registry > Skill 至少有一筆 status = available 的 skill（見 TC-2.14）。

步驟：
1. 在 `v1` 的 Version Detail，點擊「新增依賴」。
2. Type 選 `Skill`，從清單選擇一個 skill。
3. 送出。

預期結果：
- Dependencies 區塊出現該 skill 的標籤（顯示名稱與版本）。
- 只有 status = available 的 skill 出現在下拉選單中（若先前手動讓某個 skill 變成
  unavailable，該筆不應出現，可對照 TC-2.14 驗證）。

- [ ] Pass / Fail
備註：

## TC-2.13 加入 MCP 依賴

步驟：
1. 同 TC-2.12，Type 改選 `MCP`，選擇一個 available 的 MCP。
2. 送出。

預期結果：
- Dependencies 區塊新增該 MCP 標籤（顯示為 `geekblue` 顏色以區別於 skill）。
- 下拉選單同樣只列出 status = available 的 MCP。

- [ ] Pass / Fail
備註：

## TC-2.14 Registry > Skill 的可用狀態如何影響依賴選單

步驟：
1. 進入 **Registry > Skill**，新增一筆 skill（上傳任意檔案）。
2. 回到某個 draft version 的「新增依賴」表單，確認剛建立的 skill 出現在選單中。
3. 回 Registry > Skill，點擊「同步」按鈕。
4. 觀察同步後的狀態列（上次同步時間、可用/不可用數量）與該筆 skill 的狀態標籤。

預期結果：
- 新建立的 skill 預設狀態為 `available`（綠色標籤），且能被選為依賴。
- 同步後（正常情況下檔案仍在 MinIO）狀態維持 `available`，狀態列顯示同步時間與正確的
  可用/不可用計數。
- 預設清單只顯示可用項目；開啟頁面上方「顯示不可用項目」開關後，才能看到已變成不可用的項目
  （此案例若要製造 unavailable 情境，需要手動從 MinIO 移除對應物件後再同步，屬進階驗證，
  非必要案例）。

- [ ] Pass / Fail
備註：

## TC-2.15 Registry > MCP 的同步與可用狀態

步驟：
1. 進入 **Registry > MCP**，新增一筆 Host 為不可連線位址的 MCP（例如
   `http://127.0.0.1:1`）。
2. 點擊「同步」。
3. 觀察該筆狀態。
4. 再新增一筆 Host 為非 http(s) 格式（例如 `stdio://local-tool`）的 MCP，同步後觀察狀態。

預期結果：
- Host 是連不到的 http(s) 位址：同步後狀態變成 `unavailable`（紅色標籤），不再出現在
  Version Detail 的依賴選單中。
- Host 不是 http(s) 格式：同步後仍維持 `available`（系統對非網址格式的 host 一律視為
  無法驗證但不判定失敗）。

- [ ] Pass / Fail
備註：

## TC-2.16 Model 目前不是可選的依賴類型（已知現狀）

前置條件：**Registry > Model** 已建立至少一筆模型（例如 name=`claude-sonnet-5`、
provider=`anthropic`、model_id=`claude-sonnet-5`）。

步驟：
1. 回到某個 draft version 的「新增依賴」表單，查看 Type 欄位的可選項目。

預期結果：
- Type 只有 `Skill`、`MCP` 兩個選項，沒有 `Model`——目前 Registry > Model 建立的模型
  只能在 Registry 頁面本身管理（建立、同步），還不能被選為 agent version 的依賴。
  這是目前系統的真實範圍，不是要回報的 bug（詳見
  [PLANNING.md](../PLANNING.md) 的說明）。

- [ ] Pass / Fail（若未來加上 Model 依賴類型，此案例需要更新為驗證新流程）
備註：

## TC-2.17 移除依賴

前置條件：`v1` 已有至少一筆 skill 或 mcp 依賴（draft 狀態）。

步驟：
1. 在 Dependencies 標籤上點擊關閉（x）圖示。

預期結果：
- 該依賴從清單移除。

- [ ] Pass / Fail
備註：

## TC-2.18 已送審/已核准的 version 不能再編輯依賴或參數

前置條件：`v1` 已送審（見
[03-review-workflow/submit-for-review.md](../03-review-workflow/submit-for-review.md)），
狀態變成 `in_review` 或之後的 `approved`。

步驟：
1. 開啟該 version 的 Version Detail。
2. 觀察「新增依賴」按鈕與參數表單是否還能操作。

預期結果：
- 參數表單呈現唯讀（disabled），沒有「新增依賴」按鈕——只有 `draft` 或 `rejected` 狀態的
  version 可以編輯（`rejected` 是被退回後可修改重新送審，不會被強迫開新版本）。

- [ ] Pass / Fail
備註：

## TC-2.19 同一個 agent 最多同時 2 個 active version

前置條件：已有兩個以上的 version 都走完審核流程變成 `approved`
（見 [03-review-workflow](../03-review-workflow/)）。

步驟：
1. 將第一個 approved version 點擊「啟用（Activate）」。
2. 將第二個 approved version 也點擊「啟用」。
3. 若有第三個 approved version，嘗試再次啟用。

預期結果：
- 前兩次啟用成功，version 狀態變成 `active`。
- 第三次啟用被拒絕（衝突錯誤），提示已達到該 agent 可同時啟用的版本數上限（2 個）。
- 對其中一個 active version 執行「停用（Deactivate）」，狀態退回 `approved`，此時應該可以
  再啟用剛才被擋下的第三個 version。

- [ ] Pass / Fail
備註：

## TC-2.20 下載已核准版本的封裝檔

前置條件：某個 version 已是 `approved` 或 `active` 狀態。

步驟：
1. 在 Version Detail 點擊「下載封裝檔」。

預期結果：
- 成功取得下載連結並下載一個 zip 檔案。
- 尚未核准（`draft`/`in_review`/`rejected`）的 version 不會出現下載按鈕。

- [ ] Pass / Fail
備註：
