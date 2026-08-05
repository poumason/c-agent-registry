# 目的
我想要設計一個 agent-registry 的網站，讓使用者可以到 agent-registry 建立 agent 後，並且產生 agent card 與 agent 相關的檔案。

## 架構
- web frontend (react)
- web backend (python + fastapi)
- postgresql
- minio

## 使用情境
### 使用者
1. 網站建立後會有一個 admin 的管理者可以幫忙建立多個使用者
   - 預期角色： admin, owner, member
     - admin 負責整個系統的權限
     - owner 可以建立 agent, review member 建立的 agent, 調整 agent 的所有參數
     - member 基本角色，可建立 agent, submit agent 給 owner 檢查
2. owner/member 可用建立 agent 所以他們需要有能力設定 agent
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
5. 每個建立 agent 的人視為 owner，他可以邀請其他 member 變成共同編輯者。

### Agent
1. 參考 idea.drawio 中的 ERD，他會被使用者建立，設定參數，每一個 agent 會有多個版本，同時只能有 2 個版本被 active。
2. agent 被 submit 後需要按 agent 可被審核的人數清單來寫入 reviews
3. 在 agent 被 review 通過後，會產生 zip 檔案，內容有
   - agent_card.json
   - install.yaml
   - skills/
4. agent 在建立時可用選擇需要的 skill/mcp，他會被紀錄起來 agent_dependcy
