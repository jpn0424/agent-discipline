# Core Rule 03: Protocol & Tool Hygiene (Stdio 隔離與零臆測 Schema)

## 為什麼要制定此規則？ (Why)
在 Stdio MCP 模式下，`stdout` 被 JSON-RPC 協定專用。若程式碼寫入裸 `print()`，診斷訊息會直接混入 JSON 串流，導致 MCP Client 報 JSON Parse Error 而崩潰。
同時，憑空臆測 API 欄位 Key 名，例如把 `memo` 或 `details` 當成真實欄位填入，會引發傳入非預期 Payload 的 Runtime 錯誤。

---

## 具體執行方式 (How)

### 1. Stdio / Stderr 通訊隔離 (Stdout Protection)
> [!IMPORTANT]
> **硬約束。** 照字面執行，沒有判斷空間——違反後不可復原或影響第三方。
- **Stdout 專供 JSON-RPC**：伺服器端程式碼**不得使用裸 `print(...)`**。
- **診斷 Log 走 Stderr**：所有除錯、診斷訊息必須寫入 `sys.stderr`：
  ```python
  import sys
  print("[DEBUG] Processing payload...", file=sys.stderr)
  ```

### 2. 零臆測 Schema (No Schema Guessing)
判準是「這個 Key 名，你指得出它從哪裡來嗎」。指不出來就還不能填。

- **寫入前先查**：組裝 API Payload 前向源頭取得結構，確認 Key 名、型態與必填性後再填入。憑印象推論出來的欄位名與真實欄位名在字面上沒有差別，差別只在有沒有查證過。
- **什麼算源頭**：由目標系統本身即時回傳或發布的結構定義——結構查詢端點、OpenAPI／JSON Schema、工具自身的 schema 宣告、該系統的官方欄位契約文件。
- **什麼不算源頭**：記憶中的欄位名、其他專案的類似 API、範例程式碼、以及上一個工作階段取得但本次未重新確認的結構。
- **查不到就停下**：源頭查不到該欄位，回報查不到，不得改用看起來合理的鍵名頂替。
