# 0015 — ERD 補上每個欄位的型別/長度/nullable

**Commit**: _(尚未 commit)_ · 2026-08-19

## 做了什麼

`idea.drawio` 的 ERD 分頁整個重新生成（沿用先前 ERD 同步用的「Python 產生 mxGraph XML」做法，
而不是手動一格一格改）：

- 每個欄位從只有「欄位名稱」改成「欄位名稱 : 型別」，型別直接對照
  `backend/app/models/*.py` 的實際 SQLAlchemy 定義——`VARCHAR(255)`、`TEXT`、`UUID`、`INTEGER`、
  `BOOLEAN`、`JSONB`、`TIMESTAMPTZ`、`VARCHAR[]`/`UUID[]`（Postgres array）、`ENUM(type_name)`。
  Nullable 的欄位在型別後面加一個 `?`（例如 `VARCHAR(255)?`），沒有 `?` 一律 NOT NULL——圖最上方
  加了一行圖例說明這個標記慣例。
- 過程中順便核對出兩個既有 ERD 跟實際 schema對不上的地方，一併修正：
  - `Agent` 表完全漏畫 `slug` 欄位（程式碼裡是 unique、前端路由都在用的欄位）。
  - `Agent` 表原本畫的是 `category_id`（打字成 `catetgory_id`），對應到一個獨立的 `Category`
    表——但 `category` 實際上是 `Agent` 自己身上的 `VARCHAR[]` 欄位，程式碼裡從來沒有
    `Category` 這張表。`Category` 表跟它的關聯線一併移除。
- 新增 6 個列舉值參考框（`user_status`/`agent_visibility`/`version_status`/`review_result`/
  `dependency_source`/`availability_status`），跟原本就有的 3 個（`user_role`/`asset_role`/
  `dependency_type`）放在圖最上方，補齊所有 enum 型別的完整值列表。
- `docs/architecture.md`「資料模型與原始 ERD 的差異」整節重新定調成「資料模型的歷史脈絡」——
  原本的寫法（"ERD 上沒有畫出 X，所以加了 X"）在 ERD 補齊之後不再是事實，改成單純記錄「這些欄位
  當初為什麼長這樣」的決策脈絡，拿掉「跟 ERD 有落差」這個現在已經不成立的前提。

## 為什麼

ERD 原本只畫欄位名稱，沒有型別/長度/nullable，不同人看圖時對同一個欄位會有不同的實作假設（例如
一個 `VARCHAR` 欄位該設多長、一個欄位到底能不能是 NULL）——這正是這次要解決的問題。順便核對的
過程中發現 ERD 本身也已經跟實際 schema 有兩處結構性落差（漏掉 `slug`、`Category` 表根本不存在），
如果只加型別不修正這些，等於在錯的資料上補充細節，反而讓誤解更難發現，所以一併修正。

## 驗證

`python3 -c "import xml.etree.ElementTree as ET; ET.parse('idea.drawio')"` 確認 XML 格式正確；
額外寫了一段檢查腳本確認 ERD 分頁所有 26 條關聯線的 `source`/`target` 都指向存在的 cell id，沒有
斷掉的參照。逐一核對每個表格生成的欄位字串（型別、`?`）跟對應 model 檔案的定義一致（包含
`created_by` 這類 FK 欄位的 nullable 狀態）。「Agent Version Lifecycle」跟「Architecture」兩個
分頁沒有被動到（各自的 cell 數量在改動前後不變）。
