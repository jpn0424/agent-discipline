# Contributing to agent-discipline

感謝你參與維護與改善 `agent-discipline`。

本專案是 AI Agent 的工程開發紀律與交付文字品質套件。`agent-engineering-discipline` 的每一條規則都在約束 Agent 的行為邊界、防止不可逆操作並保護交付物的真實性；`deliverable-writing-audit` 的每一條徵狀都在指出一種讓規範退化成草稿的寫法。為了維持規範的可執行性，請在提交 Issue 或 Pull Request 前閱讀以下指引。

---

## 核心設計哲學

貢獻任何規則或修改時，請遵守四大基本原則：

1. **真實證據定錨（No Speculation）**：
   - 每條規則與徵狀必須來自真實開發階段中反覆發生的失誤或糾正，例如誤刪檔案、假成功宣稱、越權動手、Schema 臆測。
   - 拒絕空泛的「最佳實踐」或「假設性防護」。

2. **二元約束強度（Deontic Modality）**：
   - **【硬約束】(Hard Constraints / MUST & MUST NOT)**：僅用於不可逆操作（刪除、提交）、資安、外部影響與真實性底線。零自由裁量空間，照字面執行。
   - **【判準】(Criteria / SHOULD & MAY)**：具備情境裁量空間者，必須寫明「判準是『...』」，並附帶具體情境與失敗形態對照表。

3. **漸進揭露架構（Progressive Disclosure）**：
   - 主入口 `SKILL.md` 僅保留導覽與核心約束摘要。
   - 具體細節一律模組化至該 Skill 的 `references/`，避免一次性佔滿 Agent 的 Context Window。

4. **單一事實來源（Single Source of Truth）**：
   - 嚴禁同一條規則在多個檔案重複定義。若需引用，以相對連結指向正本。

---

## 提案與貢獻流程

### 1. Issue 與 Pull Request 怎麼被處理

本倉庫的內容由上游的開發倉庫同步發布，每個版本對應一個標籤。上游是內容的正本，因此：

- **Issue**：歡迎直接提出，問題回報與規則提案都可以。
- **Pull Request**：視為提案，不會被直接合併。採納後由維護者把改動套用到上游，隨下一個版本發布，並在該 PR 回覆對應的版本。

直接合併進本倉庫的改動，會在下一次同步時被上游的內容取代，所以不採用這條路徑。

### 2. 新增或修訂規則

若欲為 `agent-engineering-discipline` 新增一條核心約束或調整現有規則，請在 Issue 或 PR 說明中包含：
- **失誤情境**：Agent 在什麼情況下會犯錯？
- **為什麼當下不會察覺**：此錯誤的形式為何具有欺騙性？
- **判準與修法**：如何以可執行的步驟或檢查來防止失誤？
- **硬約束或判準**：此規則的強度為何？

### 3. 新增或修訂徵狀

若欲為 `deliverable-writing-audit` 新增或調整一條徵狀，請依徵狀目錄的六欄提出：徵狀、為什麼、修法、例外、證據、偵測。

- **證據寫問題的型態**：當時的文字出了什麼狀況、讀者因此會誤判或得不到什麼。不收錄對話原話，也不出現人名、專案名與工具名。
- **偵測方式要同步對照表**：新增徵狀時，`references/category-map.md` 要一併標明它由腳本偵測或由判讀處理。

### 4. 本地驗證

在提交前，執行內建的兩項檢查：

```bash
python3 skills/agent-engineering-discipline/scripts/check_skill_spec.py .
python3 skills/deliverable-writing-audit/scripts/detect.py .
```

確認以下項目通過：
- 結構檢查：YAML Frontmatter 格式合法，`description` 清楚載明觸發條件與不適用邊界；所有 Markdown 相對連結均可正常解析。
- 書寫稽核：輸出為 0 處命中。有命中時逐條對照徵狀目錄的例外判讀，並在 PR 說明放過的理由。

另外請人工確認：提交的腳本或工具維持純 Python 3 標準庫，無任何外部 pip 套件依賴。

---

## 授權

凡向本專案提交之貢獻，均視為同意以 [MIT License](LICENSE) 釋出。
