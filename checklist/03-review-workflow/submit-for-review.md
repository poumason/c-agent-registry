# 送審與指定 Reviewer

前置條件（全檔共用）：
- Alice（member，agent owner）已建立一個 draft 狀態的 version（見
  [02-agent-management/agent-versions-and-dependencies.md](../02-agent-management/agent-versions-and-dependencies.md)）。
- Carol 已被 admin 設定為 `reviewer` 角色（見
  [04-admin/manage-reviewers-and-users.md](../04-admin/manage-reviewers-and-users.md) 的
  TC-4.2）。
- Admin（系統角色 admin）帳號可用——admin 本身也符合「可被指定為審核者」的資格。

## TC-3.1 送審時明確指定 reviewer

前置條件：Alice 登入，draft version 準備送審。

步驟：
1. 在 Version Detail 點擊「送審」。
2. 在 Reviewer 欄位（多選）選擇 Carol。
3. 送出。

預期結果：
- Version 狀態變成 `in_review`。
- Version Detail 的 Review History 出現一筆對應 Carol 的 pending 審核紀錄。
- Carol 登入後在 **Review Queue**（pending 分頁）能看到這筆待審項目；未被指定的其他
  reviewer（若有）看不到這筆。

- [ ] Pass / Fail
備註：

## TC-3.2 不指定 reviewer 時 fallback 給所有 reviewer/admin

前置條件：Alice 登入，另一個 draft version 準備送審；系統中至少有 Carol（reviewer）與
Admin（admin）兩個具審核資格的帳號。

步驟：
1. 在 Version Detail 點擊「送審」。
2. Reviewer 欄位保持空白，直接送出。

預期結果：
- 送審成功，Version 狀態變成 `in_review`。
- Review History 出現多筆 pending 紀錄，對象是系統中**所有**系統角色為 `reviewer` 或
  `admin` 的使用者（不含送審者 Alice 自己，Alice 本身是 member 也不會被算進去）。
- Carol 與 Admin 都能在各自的 Review Queue 看到這筆待審項目。

- [ ] Pass / Fail
備註：

## TC-3.3 不能指定自己為 reviewer

前置條件：以 Carol（reviewer，同時也是某個 agent 的 owner）登入，該 agent 有一個 draft
version。

步驟：
1. 送審該 version，Reviewer 欄位選擇 Carol 自己。
2. 送出。

預期結果：
- 送出失敗，顯示錯誤（不能指定自己為審核者），version 狀態仍維持 `draft`。

- [ ] Pass / Fail
備註：

## TC-3.4 指定非 reviewer/admin 的一般 member 會被拒絕

前置條件：Alice 登入，draft version 準備送審；Bob 是一般 member（未被設為 reviewer）。

步驟：
1. 若前端 Reviewer 選單只列出合格候選人（reviewer/admin），先確認 Bob 是否根本不會出現在
   選單中；若選單本身已過濾掉不合格對象，此案例改為「確認選單只列出合格 reviewer/admin」。

預期結果：
- Reviewer 選單只列出系統角色為 `reviewer` 或 `admin` 且狀態 active 的使用者，Bob（一般
  member）不會出現在候選清單中，因此不可能被指定。

- [ ] Pass / Fail
備註：

## TC-3.5 送審後 version 進入唯讀狀態

前置條件：承 TC-3.1 或 TC-3.2，version 已是 `in_review`。

步驟：
1. 開啟該 version 的 Version Detail。

預期結果：
- 同 [02-agent-management/agent-versions-and-dependencies.md](../02-agent-management/agent-versions-and-dependencies.md)
  的 TC-2.18：參數表單唯讀，無法新增/移除依賴，也沒有「送審」按鈕（避免審核中途被改動內容）。
- 頁面顯示「審核中」的提示訊息。

- [ ] Pass / Fail
備註：

## TC-3.6 被退回（rejected）後可以修改並重新送審

前置條件：某個 `in_review` version 已被 reviewer 退回（見
[reviewer-decision.md](reviewer-decision.md) 的 TC-3.9），狀態變成 `rejected`。

步驟：
1. Alice 登入，開啟該 version。
2. 確認可以編輯參數/依賴（同 draft 狀態）。
3. 修改後再次點擊「重新送審」，指定 reviewer（可與上次不同）。

預期結果：
- 修改成功。
- 重新送審後狀態回到 `in_review`，Review History 保留先前那筆 `rejected` 紀錄
  （含理由），並新增一筆新的 pending 紀錄——同一個 version slug 累積審核歷史，不會另外
  開一個新版本。

- [ ] Pass / Fail
備註：
