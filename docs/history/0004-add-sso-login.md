# 0004 — 加入通用 OIDC SSO 登入

**Commit**: `4de2f45` · 2026-08-05

## 做了什麼

在既有的密碼登入之外，加了一條 SSO 登入路徑（Authorization Code + PKCE，通用 OIDC，不綁定
特定廠商）：

- `GET /auth/sso/login` → `GET /auth/sso/callback`
- `state` 參數是簽章過的 JWT（帶 PKCE `code_verifier` + `nonce`），不需要 server-side session
- 第一次用某 email 登入自動建立帳號，角色固定 `member`；既有帳號的角色/狀態不會被 SSO 覆蓋
- 密碼登入完全不受影響，兩種方式並存

順手修了一個問題：`Settings` 讀 `.env` 原本相對 CWD 解析，導致照 README 建議的
`cd backend && uv run ...` 流程時讀不到 repo 根目錄的 `.env`（之前沒發現是因為 DB/MinIO 預設值
剛好對得上 docker-compose）。

## 為什麼

Claude.md 第 3 點要求加入 SSO，且明確要求密碼登入（系統帳號直接登入）要繼續保留，不能因為加了
SSO 就被取代。

## 驗證

用使用者提供的 GitLab OAuth app 憑證，實際打過 `/auth/sso/login`，確認 redirect_uri/client_id/
PKCE 參數都被接受（正常導到 GitLab 登入頁）；完整登入流程因為需要互動式輸入帳密，用 mock 測試
覆蓋 callback 邏輯。

## 細節

完整流程圖與設計理由見 [docs/sso.md](../sso.md)。
