# Pattern：多部署目標的設定分流（Multi-Target Deployment Scoping）

這份文件記錄一個可以套用到其他專案的設計模式，來源是 agent-registry 這次「一個 agent version
可以部署到多個廠區（fab），部分設定要能因廠區而異」的改動（見文末案例對照，對應
[history 0011](../history/0011-fab-scoped-dependency-validation.md)、
[0012](../history/0012-fab-scoped-agent-dependencies.md)、
[0013](../history/0013-remove-active-version-cap.md)、
[0014](../history/0014-per-fab-tabs-in-version-detail.md)）。內文刻意用抽象詞彙
（resource／target／item）描述，方便套用到其他領域：可能是「一個服務部署到多個環境／region／
租戶」，不一定是「fab」。

## 適用情境

你的系統裡有一個**資源（resource）**——一個 config、一個 version、一個 deployment 定義——會被
同時部署到多個**目標（target）**（環境、地區、廠區、租戶……）。這個資源底下掛著一些子設定/子
資料（item），你發現：

- 有些子設定天生就該**全部 target 共用**（描述、能力宣告、全域參數）。
- 有些子設定應該**可以因 target 而異**（依賴的元件版本、連線位址、per-target 覆寫、限流設定）。

如果現在的設計是「resource 只有一份子設定、套用到它部署的所有 target」，就會卡在一個常見的
真實需求：*只想調整/修好其中一個 target，不想影響其他 target，也不想為了這個小調整整個
resource 重新走一次完整的發版流程*。

## 常見的錯誤解法

- **人為的「同時只能有 N 個活躍版本」上限**：想靠開新版本、把不同 target 分配到不同版本來
  模擬「per-target 差異」，但版本數量被人為限制死，逼你在「浪費一個版本名額」跟「硬改共用設定
  影響所有 target」之間二選一。這種上限如果不是資源本身的限制（例如真的有硬體/授權數量限制），
  通常是歷史包袱，值得檢查是否該拿掉。
- **退回編輯狀態、原地修改再重新發布**：如果 resource 是「所有 target 共用一份」，退回編輯狀態
  意味著它服務的**所有** target 在編輯/重新審核期間都會受影響（甚至斷線），而且改完之後所有
  target 還是被迫吃到同一份新設定——並沒有達成「只影響一個 target」的目的。

## 核心設計決策

### 1. Nullable `target_id`，但只有一種意思

在 item 表上加一個 nullable 的 `target_id` 外鍵。**NULL 不是「套用到全部 target」的萬用值**，
而是「這個 item 天生沒有 target 維度」——例如一個全域設定、一個不受部署位置影響的能力宣告。一旦
resource 已經部署到至少一個 target，凡是「有 target 維度」的 item 就必須明確指向某一個 target，
不能留 NULL。

這樣設計的好處是 NULL 永遠只有一種解讀方式，不會出現「NULL 那一列跟指定 target 的那一列同時
存在、不知道誰蓋過誰」的歧義——那種「NULL = 預設值，特定 target 覆寫預設值」的設計聽起來方便，
實際上每次都要多想一層合併規則，值得盡量避免。

### 2. Unique constraint 要包含 `target_id`，但注意 NULL 語意

`(resource_id, item_key, target_id)` 的唯一約束，讓同一個 item 可以在不同 target 各存一列。但
大部分資料庫的 UNIQUE 對 NULL 是「互不相等」——同一個 resource+item 出現兩筆 `target_id=NULL`
的列，DB 不會擋下來。這個重複檢查要在應用層另外做（新增前先查一次完全相同的 key 組合是否已存在）。

### 3. 驗證邏輯從「集合覆蓋」簡化成「單一 target 合法性」

沒有 per-target 分流之前，驗證邏輯常常長成「這個 item 要覆蓋 resource 部署的**所有** target，
不然就擋下」——這種集合運算，一旦每筆資料都明確歸屬某一個 target，就可以整個拿掉，改成單點
檢查：

- 這個 `target_id` 是不是 resource 目前部署的其中一個？
- 這個 item 本身在這一個 target 是否可用？

不需要再檢查「整組資料要覆蓋所有部署 target」，因為現在本來就允許不同 target 各自獨立。這也
連帶讓「幫 resource 增加一個新的部署 target」變得不需要驗證舊資料——新 target 從零筆 item 開始，
跟新建一個 resource 時本來就是空的一樣正常。

### 4. 拿掉會跟這個模式衝突的人為上限

檢查系統裡「最多 N 個活躍版本/實例」這類限制是不是在阻止「同一個 resource 合法地在不同 target
各自服務不同版本」——如果 item 的 schema 已經是 per-target 設計（決策1、2），這種上限往往只是
擋在門口，拿掉之後 per-target 差異化能力才真正可用，且通常不需要新的 schema 或邏輯（能力其實
早就在資料模型裡了，只是被上限鎖住沒機會用到）。

### 5. 遷移既有資料，不要靜默捨棄

把既有「套用到所有部署 target」的資料，按照它當時實際部署的 target 展開成多筆（每個 target
一筆）；沒有部署任何 target 的維持 `target_id=NULL`。這樣遷移前後的**行為**一致（原本「這個
item 對所有已部署 target 都有效」，遷移後變成「這個 item 對每個已部署 target 都各自有一筆記
錄」），而不是讓舊資料因為新規則變成語意不明、甚至消失的孤兒列。

## 前端模式：per-target tabs

### 6. 只有「因 target 而異」的設定進 tabs，共用設定留在外面

不要因為「使用者想在畫面上同時看到 X」就把 X 塞進每一個 tab 各自渲染一份——如果 X 是共用資料，
在 N 個 tab 裡各自渲染一份表單，會變成 N 份獨立的前端 state 同步同一份後端資料，容易出現「A
tab 編輯到一半切到 B tab，兩邊顯示不一致」的 bug。共用設定維持單一表單、單一存檔按鈕，放在
tabs 外面（上方或下方皆可），只有 per-target 才真正需要分開的內容（URL、依賴/子項目、
per-target 預覽）進到 tabs 裡。

### 7. Tabs 反映「已存檔」的部署目標清單，不是還沒存檔的勾選狀態

新增/移除「這個 resource 要部署到哪些 target」獨立成一個管理用的 Modal/面板，存檔後 tabs 才
跟著變；單一 target 的 tab 內不能加減 target。這避免「使用者在某個 target 的 tab 裡誤操作，
意外影響了 target 清單本身」，也讓 tabs 的資料來源單純（永遠對應已儲存狀態，不會因為使用者
還沒存檔的勾選而在畫面上憑空冒出/消失）。

### 8. 「新增 item 要歸屬哪個 target」用 UI 情境隱含帶出

使用者已經在某個 target 的 tab 裡點「新增」，就不需要再跳出一個下拉選單問他要加到哪個
target——直接用目前 active tab 的 target id。這同時簡化了選項過濾邏輯（只需要驗證「這個
候選項目在這一個 target 是否可用」，不用管其他 target），也讓「新增」表單本身變簡單（少一個
欄位、少一組條件判斷）。

### 9. 衍生預覽可以純前端算，不用改後端

如果「這個 target 專屬的樣子」只是既有彙總資料的一個子集（例如整個 resource 的組態 API 回應
本來就列出了所有 target 各自的 endpoint，只是彙總在一起），可以在前端用已經抓到的彙總資料直接
算出 per-target 版本（篩選/取代對應欄位），不需要為了每個 target 各自新增一個後端端點。

## Checklist：套用到其他專案

1. 盤點哪些子設定真的該因部署目標而異，哪些該維持共用——不要預設全部都要拆，這會不必要地放大
   改動範圍（見案例對照裡「執行參數／Agent Card Skills 維持共用」的決定）。
2. Schema：resource↔target 的部署關聯表（多對多）+ item 表上加 nullable `target_id`，語意
   只有一種（決策1）。
3. Unique constraint 包含 `target_id`，並在應用層補上 NULL-safe 的重複檢查（決策2）。
4. Migration：既有 item 按 resource 當時的部署 target 展開，不要靜默捨棄（決策5）。
5. 驗證邏輯改成單一 target 合法性檢查，拿掉「集合覆蓋」邏輯（決策3）與相關的人為上限（決策4）。
6. 前端：per-target tabs，只放真正因 target 而異的內容；共用設定留在外面（決策6）；target
   清單管理獨立成一個 Modal/面板，tabs 只反映已存檔狀態（決策7）；新增 item 用當前 tab 的
   target 隱含帶出，不用另外選一次（決策8）；能純前端算的 per-target 預覽就不要改後端（決策9）。

## 案例對照：agent-registry 的 fab 部署改動

| 抽象概念 | agent-registry 裡對應什麼 |
|---|---|
| resource | Agent Version |
| target | Fab（廠區） |
| resource↔target 部署關聯表 | `agent_fabs`（含每個 (version, fab) 各自的部署 URL） |
| item（因 target 而異） | `agent_dependencies`（依賴的 Skill/MCP，`fab_id` 決定因 target 而異） |
| 天生無 target 維度的 item | `type=model` 的依賴、`source=registry` 的 skill（沒有 `*_fabs` 表） |
| 拿掉的人為上限 | `MAX_ACTIVE_VERSIONS_PER_AGENT = 2`（[0013](../history/0013-remove-active-version-cap.md)） |
| 前端 per-target tabs | `VersionDetail.tsx` 的 fab tabs（[0014](../history/0014-per-fab-tabs-in-version-detail.md)） |
| 維持共用、留在 tabs 外面的設定 | 執行參數（streaming/input-output modes）、Agent Card Skills |
| 純前端算的 per-target 預覽 | 每個 fab tab 的 Agent Card（A2A 1.0）預覽，沒有新增後端端點 |

決策1–5 的完整實作見 [0011](../history/0011-fab-scoped-dependency-validation.md)、
[0012](../history/0012-fab-scoped-agent-dependencies.md)、
[0013](../history/0013-remove-active-version-cap.md)；決策6–9 見
[0014](../history/0014-per-fab-tabs-in-version-detail.md)。
