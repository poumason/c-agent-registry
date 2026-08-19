# 0014 — Version Detail 頁面：Fab 相關設定改成 per-fab tabs

**Commit**: _(尚未 commit)_ · 2026-08-19

## 做了什麼

`VersionDetail.tsx` 原本把「部署 fab」「依賴的 skill/mcp」「Agent Card」三個區塊各自攤平成獨立
卡片——部署 fab 是一份勾選+URL 清單，依賴清單是所有 fab 混在一起顯示（0012 已經讓每筆依賴自己帶
`fab_id`，但畫面上還是一個扁平列表），Agent Card 是彙總所有 fab 的單一 JSON 預覽。這次把這些
fab 相關的東西改成「每個 fab 一個 tab」的呈現：每個 tab 裡放這個 fab 的部署 URL、依賴的
Skill/MCP、Agent Card（A2A 1.0）預覽，各自獨立存檔。

跟使用者確認過的範圍：**執行參數跟 Agent Card Skills 維持 version 共用一份**，不會變成每個 fab
各自獨立的資料（那需要新的 schema migration，這次沒做）——這兩塊卡片留在 tabs 外面、原位置不動。
真正需要按 fab 分開的，本來就只有部署 URL（`AgentFab.url`）跟依賴的 skill/mcp
（`AgentDependency.fab_id`，0012 已經做好），這次是**純前端重新排版，後端完全沒改一行**。

**前端**（`frontend/src/pages/VersionDetail.tsx`，唯一改動的檔案）：

- 拿掉「部署 fab」勾選清單卡片，改放進一個由「管理部署廠區」按鈕開啟的 Modal（勾選+URL 清單原封
  不動搬過去），存檔沿用既有的 `saveFabsMutation`（`PUT /versions/{slug}/fabs`，整批替換）。
- 新增 `<Tabs>`：`items` 來自 `versionFabsQuery.data`（已儲存的部署清單，不是還沒存檔的勾選狀
  態），每個 tab 對應一個 fab，內容是這個 fab 的 URL 輸入+存檔按鈕、依賴清單（`fab_id` 相符 +
  `fab_id` 為 null 的共用依賴，標「共用」）、純前端算出的單一 fab Agent Card 預覽（拿
  `agentCardQuery.data` 當底，把 `supportedInterfaces` 換成這個 fab 目前 URL 算出的單一
  interface，`GET .../agent-card` 本身不用改）。version 目前沒有部署任何 fab 時 fallback 成
  之前的未過濾依賴清單 + 彙總 Agent Card。
- Add Dependency modal 拿掉原本（0012）裡的「Fab」下拉——現在從哪個 tab 點「新增依賴」就自動帶
  那個 tab 的 `fab_id`（新增的 `depTargetFabId` state），Modal 標題會帶上目前是哪個 fab；選項
  過濾邏輯從「fabPending 邏輯」簡化成單一 fab 的可用性檢查。
- i18n 新增「管理部署廠區」按鈕/Modal 標題、空狀態文字、「共用」標籤等 key；移除 0012 加的、現在
  沒有呼叫端的 `fabRequiredForDependency`／`pickFabFirstHint`／`versionDetail.fabLabel`。

## 為什麼

0012 讓依賴的 fab 維度真正落地，但畫面上還是「一個扁平列表，靠 tag 上一小段文字標哪個 fab」，
使用者要找「這個 fab 到底吃了哪些依賴、URL 是什麼、Agent Card 長怎樣」得在一堆混在一起的資料裡
自己拼湊。改成 per-fab tabs 之後，每個 fab 的完整設定（URL/依賴/卡片預覽）都在同一個畫面區塊內
自成一組，且新增依賴時系統直接知道「你現在在哪個 fab 的 tab 裡」，不用使用者自己再選一次 fab
（0012 版本的 UI 還需要多選一次）。執行參數／Agent Card Skills 之所以沒有跟著搬進 tabs 裡，是
因為它們目前仍是 version 級別共用資料——如果硬要在每個 tab 各自渲染一份 Form，會變成 5 份獨立
React Form state 同步同一份後端資料，容易出現「A tab 編輯到一半切到 B tab，兩邊顯示不一致」的
bug，所以維持原位置、原本的單一存檔按鈕。

## 驗證

`cd frontend && npx tsc --noEmit` 通過。因為後端沒改，沒有新增/修改 pytest。手動在瀏覽器對著
本機跑起來的服務走了一次：在既有的 `ocap-agent-v1`（draft）版本上，透過「管理部署廠區」把 F15
加進部署清單，確認立刻多出一個 F15 tab；分別在 F12/F15 tab 各自編輯 URL，確認互不影響
（DOM 層級直接讀 input value 驗證，兩個 tab 各自保留自己的值）；F12 tab 的 Agent Card 預覽只有
F12 自己的 `supportedInterfaces` 一筆，F15 同理；臨時 seed 一個只指派到 F12 的 skill，從 F12
tab 新增依賴，確認送出的 `POST .../dependencies` payload 正確帶 `fab_id=F12`、F12 tab 顯示這筆
依賴、F15 tab 不顯示；從 F15 tab 開新增依賴 Modal，確認那個只在 F12 可用的 skill 不會出現在
F15 的候選清單裡（單一 fab 可用性過濾正確）；全程 console 沒有任何錯誤。驗證用的暫時測試資料
（skill 本身、skill_fab 指派、依賴列）已經清掉，沒有留在資料庫裡。
