# 目的
我想要設計一個 agent-registry 的網站，讓使用者可以到 agent-registry 建立 agent 後，並且產生 agent card 與 agent 相關的檔案。

## 架構
- web frontend (react)
- web backend (python + fastapi)
- postgresql
- minio

## 使用情境
### 使用者
1. 網站建立後會有一個 admin 的管理者可以管理使用者
   - 基本功能：建立，啟動，刪除，調整角色（例如把某個 member 設定成 reviewer）
2. 角色清單
   - system admin
     - admin 負責整個系統的權限(建立使用者，建立 review 規則等)
   - member
     - 基本角色，只能管理自己建立的 agent
   - Reviwer
     - 功能繼承 member
     - 增加擁有審核 agent 的能力
3. 加入 SSO 登入的機制，預設登入的使用使用 member 角色
4. 角色的權限大綱
    | 功能/角色  | Member | Reviewer | System admin |
    |---|---|---|---|
    | agent management| | | |
    | 建立/修改/刪除 agent | V | V | V |
    | 建立多個 sagent version | V | V | V |
    | 瀏覽已核准的 agent | V | V | V |
    | 加入其他 member 共同編輯 agent | V | V | V |
    | review management | | | |
    | 審核待 review 的 agent | X |V | V|
    | System management| | | |
    | 設定資料庫 | X | X | V|
    | 建立/刪除使用者 | X | X | V|
    | 設定審核檢核規則 | X | X | V|

### Agent
1. 參考 idea.drawio 中的 ERD，他會被使用者建立，設定參數，每一個 agent 會有多個版本，同時只能有 2 個版本被 active。
2. 建立 agent 的人視為 owner，可以邀請其他 member 變成共同編輯者。
3. agent 在建立時可用選擇需要的 skill/mcp，他會被紀錄起來 agent_dependcy
4. agent 被 submit 時需要指定擁有 reviewer 權限的使用者來進行審核（如果沒有指定就是按 agent 可被審核的人數清單來寫入 reviews）
5. 在 agent 被 review 通過後，會產生 zip 檔案(內容如下）
   - agent_card.json
   - install.yaml
   - skills/
6. zip 檔會被放在 minio 中，路徑結構
   ```
   --> bucket
   ----> agent_id/
   ------> agent_version.zip
   ```



# 前端開發
## 登入
- 進入時預設需要登入(SSO 與 帳號密碼 同時提供)

## 畫面
- 需注意 RWD
### 首頁
- 顯示目前已通過審核的 agent (預設設定為 public)
- 左側欄位
  - browse
  - agent management
    - my agents
### my agents
- 顯示目前已建立的 agents （利用放 list 顯示，需要包含一些資料： name, description, statur(draft/staging/production), version)
- 點擊 agent 可用看到 agent detail page
### agent detail page
- 顯示 agent 基本資料( from agent table)
- 顯示現有的 version list
- 點擊 version list 可用看到 version 的細節
  - version 細節可用設定相關的參數(from agent_version )
  - 細節還可以選擇 sklls/ mcp 來使用 (from skill/ mcp table)
### skill/mcp page
- 顯示目前 DB 中有的資料內容
- skill/mcp 利用 backend api 自動同步而來
