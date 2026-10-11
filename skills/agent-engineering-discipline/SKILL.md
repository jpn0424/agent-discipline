---
name: agent-engineering-discipline
description: "處理一件開發任務的治理紀律：改檔前先建立工項，在其中界定範圍與驗收條件，宣稱完成要附得出證據，寫向遠端需當次授權，不可復原的刪除改用可復原方式，不預先建設用不到的抽象也不擅自移除相容層。治理決定一個工項怎麼建立、怎麼收尾；工項內採用測試先行或其他執行方法，由任務性質決定並在工項中宣告。只回答概念問題、解釋既有程式碼、查詢資料而不產生任何檔案變更時不適用。除此之外，只要這次對話會動到檔案就載入它——使用者說「幫我改一下」、「實作這個功能」、「加個欄位」、「幫我開票」、「跑一下測試」、「可以 commit 了嗎」、「幫我重構」，或要求規劃架構、撰寫 API Payload、整理專案文件結構、準備 PR 時，即使他沒有提到規範、紀律或流程，也要載入。"
---

# Agent Engineering Discipline

## 摘要 (Abstract)

本 Skill 規範一件開發任務的**治理**——一個工項怎麼建立、範圍怎麼界定、完成怎麼認定、什麼動作需要授權——並藉此保護四個不變量：動手前有紀錄、越界前有授權、宣稱後有證據、不可復原的操作有退路。四者與任務性質無關，也不隨技術棧改變，因此收斂成規範而不是建議；至於工項內要用測試先行、規格先行或其他方式推進，由任務性質決定並在工項中宣告，治理不指定執行方法。

## 核心規則 (Core Rules)

本規範由十一條核心規則構成，為跨專案開發治理的唯一事實來源：

| 規則 | 規範範疇 |
| --- | --- |
| [Core Rule 01](references/core-rules/01-task-ticket-discipline.md) | 工項建立、狀態流轉、驗收條件與截圖紀錄 |
| [Core Rule 02](references/core-rules/02-execution-safety.md) | 執行安全：不可復原操作之邊界與資源清理 |
| [Core Rule 03](references/core-rules/03-protocol-tool-hygiene.md) | 協定與 Schema：stdout 隔離與零臆測 Schema |
| [Core Rule 04](references/core-rules/04-deliverable-hygiene.md) | 交付物與 ADR：交付物純化、決策紀錄與稽核閘門 |
| [Core Rule 05](references/core-rules/05-skill-and-agent-spec.md) | Skill 規格與雙層治理：Skill 撰寫規範與驗證者委派 |
| [Core Rule 06](references/core-rules/06-authorization-boundary.md) | 授權邊界：動作授權、動詞定義與操作範圍鎖定 |
| [Core Rule 07](references/core-rules/07-honesty-and-evidence.md) | 誠實與證據：宣稱、證據有效性與能力邊界宣告 |
| [Core Rule 08](references/core-rules/08-harness-doc-layout.md) | Harness 文件分工：AGENTS.md 正本與工具版式分工 |
| [Core Rule 09](references/core-rules/09-implementation-restraint.md) | 最小實作與相容邊界：夠用為準與相容性維護 |
| [Core Rule 10](references/core-rules/10-delegation-contract.md) | 委派契約：任務交接時的輸入與驗收完備性 |
| [Core Rule 11](references/core-rules/11-judgement-responsibility.md) | 判斷責任：自主推進與提問回報的邊界 |

本規範的條文分為兩種執行強度：

- **硬約束**：照字面執行，零裁量空間，破壞即代表失誤。
- **判準**：具備情境裁量空間，提供判斷依據與典型反例。由 Agent 依情境判定處置方式，並在回報中說明判斷依據。

判準不是建議——照抄字面而不顧情境，與無視規則同樣是失誤。當無法判定情境時，一律向硬約束靠攏，並在回覆中主動說明疑問。

## 硬約束 (Hard Constraints)

以下為系統行為底線，照字面執行，不留裁量空間：

1. **寫向遠端需要當次授權**：`git commit`、`git push`、開 PR、回覆 PR、推 tag，需要使用者在當次對話明確指示。「上次允許過」不構成本次授權。被授權後，commit message 與 PR 內容不得含機敏資訊，也不得出現 AI 署名。
2. **commit 前必須核對 `git status`**：確認沒有誤納暫存檔、憑證或 `.DS_Store`。
3. **「清理」不在任何動詞的預設授權範圍內**：使用者指示「改」、「修」、「實作」都不包含刪除既有資料，清理必須另獲明確指示。
4. **不得使用 `rm -rf`**：macOS 必須改用 `/usr/bin/trash <path>` 移至垃圾桶，其他平台改用該平台的可復原刪除機制（無工具時移至暫存隔離目錄）。
5. **外部系統既有記錄只做可逆狀態轉換**：測試資料與外部記錄預設全部保留供查驗；奉命清理時先確認狀態，僅能使用該系統提供的作廢、撤銷、停用，不得直接抹除，且只清理本次自己產生的記錄。
6. **交付內容不得出現機敏值與本機絕對路徑**：真實憑證、內部主機名、真實單號、`/Users/<使用者>/...` 等路徑必須改為語意化佔位符或相對路徑。
7. **Stdio 模式下 `stdout` 專供協定**：伺服器端不得使用裸 `print()`，診斷訊息必須輸出至 `sys.stderr`。
8. **宣稱與證據同處可見**：回報「已修復」、「已完成」、「已驗證」、「可運作」時，同一處必須附上工具回應原文、回讀結果、截圖路徑或驗證結果。未取得證據前不得宣稱完成。
9. **能力狀態只有兩種合法值**：僅能填「已驗證」或「已知不支援」，不留「未實測」或「待確認」等模糊狀態。無法驗證時必須明確說明阻礙條件。
10. **不得自行決定破壞或保留相容性**：已發佈套件、上線服務、外部介面與既有部署流程之退役由使用者決定；發現舊路徑應退役時建立工項提出，不順手移除。

## 治理模型：六個動作

治理管的是**失誤發生的位置**。一件工作依序執行六個動作，每個動作皆具備明確的進入前置條件（Preconditions）與放行後置條件（Postconditions），規則則是防止失誤溢出的護欄。

推進任務時，先確認自己正在執行哪個動作，便能精確對焦該動作所對應的失誤形態與防禦規則：

| 動作 | 失誤形態 | 適用規則 |
| --- | --- | --- |
| 判斷 | 用猜測填掉查得到的空白；或反過來，把使用者已經表態的決策再推回去問 | [Core Rule 07](references/core-rules/07-honesty-and-evidence.md)、[Core Rule 11](references/core-rules/11-judgement-responsibility.md) |
| 授權 | 動詞是「審查」卻動了手；回答的範圍超出被問的範圍 | [Core Rule 06](references/core-rules/06-authorization-boundary.md) |
| 定義 | 沒有紀錄就動手；驗收判準留到看見結果之後才定 | [Core Rule 01](references/core-rules/01-task-ticket-discipline.md)、[Core Rule 10](references/core-rules/10-delegation-contract.md) |
| 執行 | 建設用不到的抽象；擅自移除還在運作的相容層；憑記憶臆測結構定義 | [Core Rule 03](references/core-rules/03-protocol-tool-hygiene.md)、[Core Rule 09](references/core-rules/09-implementation-restraint.md) |
| 取證 | 採信沒校準過的判定工具；用繞過使用者實際鏈路的方式驗證 | [Core Rule 04](references/core-rules/04-deliverable-hygiene.md)、[Core Rule 06](references/core-rules/06-authorization-boundary.md)、[Core Rule 07](references/core-rules/07-honesty-and-evidence.md) |
| 回報 | 宣稱指不出證據；把失敗摘要掉 | [Core Rule 07](references/core-rules/07-honesty-and-evidence.md) |

[Core Rule 06](references/core-rules/06-authorization-boundary.md) 與 [Core Rule 07](references/core-rules/07-honesty-and-evidence.md) 是最高頻的失誤防禦：越界動手與宣稱失真。

## 方法 (Methods)

任務依性質在工項中宣告所採用的方法；單純修正或文件微調寫「不適用」。需要特定方法細節時，查閱 [references/methods/](references/methods/)：

- **測試驅動**：查閱 [test-first.md](references/methods/test-first.md)。依改動對象判定測試層級（單元測試 vs 驗收測試），並確認紅燈紅在行為斷言而非連線失敗。
- **複雜規劃**：查閱 [brainstorm-and-plan.md](references/methods/brainstorm-and-plan.md)。涉及架構調整或複雜重構時，動手前先研析並輸出計畫，暫停等待使用者核可。
- **研究**：交付物是報告而不含實作時採用。不另立方法檔，驗收形式見 [10-delegation-contract.md](references/core-rules/10-delegation-contract.md)——比對形式結構完整度、查核引用來源與佐證齊備度，不以測試轉綠為準。
- **外部標準方法**：如 BDD、SDD 等，直接具名宣告於工項，不重述外部既有定義。

## 範本 (Assets)

存放於 [assets/](assets/) 目錄，提供任務產出物之標準結構：

- **建立工項**：複製 [task-template.md](assets/task-template.md) 至 `docs/tasks/TASK-YYYYMMDD-NN-<slug>.md`，動手改檔前界定範圍、限制與可檢驗的驗收條件。
- **架構決策紀錄**：複製 [decision-template.md](assets/decision-template.md) 至 `docs/decisions/decisions.md`（或專案約定之決策檔如 `.claude/decisions.md`），記錄涉及架構、相容性或外部影響的決策。
- **專案 Harness 正本**：複製 [agents-template.md](assets/agents-template.md) 至專案根目錄並命名為 `AGENTS.md`，版式遵循 [Core Rule 08](references/core-rules/08-harness-doc-layout.md)，依專案特性填寫定位與自訂規則。

## 結構檢查 (Structure Check)

改動任何 Skill 或 Harness 入口檔之後、回報之前執行：

```bash
python3 scripts/check_skill_spec.py <專案路徑>
# 選項：--json 輸出結構化結果
```

無外部依賴，Python 3 標準庫即可。結束碼 `0` 表示通過、`1` 表示有缺陷、`2` 表示執行錯誤。檢查確定性的結構事實：frontmatter 完整性、`name` 命名、禁止角括號標籤、目錄內不得放 README.md、子目錄無多餘 frontmatter、相對連結有效性，以及 `CLAUDE.md` 僅限標題與 `@AGENTS.md` 參照。
