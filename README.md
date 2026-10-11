# agent-discipline

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![skills.sh](https://img.shields.io/badge/ecosystem-skills.sh-purple.svg)](https://skills.sh/)
[![Python: 3.x](https://img.shields.io/badge/python-3.x-green.svg)](skills/agent-engineering-discipline/scripts/check_skill_spec.py)

AI Agent 的工程開發紀律與交付文字品質套件。一個目錄一個 Skill，目錄名與該 Skill 的 `name` 相同，可直接以下方的 [`skills`](https://skills.sh/) 指令安裝。

## 收錄的 Skills

| Skill | 類型 | 說明 |
| :--- | :--- | :--- |
| [`agent-engineering-discipline`](skills/agent-engineering-discipline/) | 規範型 | 工程開發紀律的治理層：建立工項並在工項中界定範圍與驗收、授權邊界、誠實回報與證據、零臆測 Schema、最小實作與相容邊界、雙層治理與 Nygard ADR 決策紀錄。工項內採測試先行或兩階段規劃，由任務性質決定。 |
| [`deliverable-writing-audit`](skills/deliverable-writing-audit/) | 稽核型 | 對既有文字做書寫徵狀的比對與改寫：28 條具名徵狀、六種交付情境各自的寬容度、只標記／回傳改寫版／就地修檔三種模式，預設只標記不改字。附無依賴的偵測腳本。 |

前者規範動手前後的行為，後者稽核寫出來的文字。前者的交付物規則要求以後者稽核改動過的檔案，兩個一起安裝才完整。

## 安裝

在**目標專案的根目錄**執行：

```bash
npx skills add jpn0424/agent-discipline --agent claude-code --copy -y
```

三個旗標的作用：`--agent claude-code` 限定只裝給 Claude Code，不去動 `.junie/`、`.cursor/` 等其他 Agent 的目錄；`--copy` 讓 `.claude/skills/` 內是實體檔案而非指向 `.agents/` 的 symlink，避免 `.agents/` 未一起提交時變成死連結；`-y` 略過互動提示。

## 安裝後如何初次使用

1. **讓 Claude Code 認得它**：若安裝前該專案尚無 `.claude/skills/` 目錄，需重新啟動 Claude Code，新目錄才會被監看；若原本就存在則即時生效。
2. **確認已載入**：輸入 `/`，選單中應出現兩個 Skill 的名字。
3. **開始使用**，兩種觸發方式：
   - **自動**：請求命中它的描述情境時，Claude 會自行載入並套用規範。
   - **手動**：直接輸入 `/agent-engineering-discipline` 或 `/deliverable-writing-audit`。

載入後 `SKILL.md` 的內容會進入對話並在整個工作階段持續生效；其中引用的 `references/`、`assets/` 子文件由 Claude 依需要再讀取，不會一次全部佔用 context。

## 怎麼驗證它有效

**`agent-engineering-discipline`** 不執行任何動作，而是約束 Agent 在後續開發任務中的行為。載入後交派一個開發任務，觀察它是否：

- 動手前先建立工項，並在其中界定範圍與驗收條件。
- 指令是「審查」時只做分析與回報，不擅自改檔。
- 宣稱「已完成」時，同一處指得出證據。

三項都成立才算生效。任一項落空，代表規範沒有進入該次對話。

**`deliverable-writing-audit`** 在你要它看一份既有文字時生效。請它審查一份文件，觀察它是否：

- 只標記、不改檔，除非你明確要求修改。
- 每一處命中都附上行號並引用原文。
- 把資安與可信度的問題，和只影響可讀性的形式問題分開陳列。

偵測腳本也可以單獨執行，不需要 Agent：

```bash
python3 skills/deliverable-writing-audit/scripts/detect.py <檔案或目錄>
```

## 核心約束 (Core Rules)

`agent-engineering-discipline` 的十一條核心規則：

| 編號 | 核心規則 | 防範的失誤形態 (Anti-Patterns) |
| :--- | :--- | :--- |
| CR-01 | 工項紀律 | 口頭承諾「改天再修」，會話結束就遺失 |
| CR-02 | 執行安全 | 未經指示的提交，以及不可復原的刪除 |
| CR-03 | 協定與 Schema | 診斷訊息混入 stdout 協定通道；憑印象填 API 欄位名 |
| CR-04 | 交付物與 ADR | 交付內容夾帶本機路徑與機敏值；重大決策沒有紀錄 |
| CR-05 | Skill 與雙層治理 | Frontmatter 缺漏導致載不到；自己寫又自己驗 |
| CR-06 | 授權邊界 | 說「審查」卻動手；指定改 A 卻順手改了 B |
| CR-07 | 誠實與證據 | 把沒驗證的說成已完成；把做得到的說成做不到 |
| CR-08 | Harness 文件分工 | 規範寫成多份，不同 Agent 讀到矛盾的版本 |
| CR-09 | 最小實作與相容邊界 | 預先建設用不到的抽象；擅自拆掉還在運作的相容處理 |
| CR-10 | 委派契約 | 工項只有自己看得懂，交出去只能靠猜 |
| CR-11 | 判斷責任 | 把該自己判斷的推回去問，要人複述已經給過的東西 |

### 關鍵設計原則 (Key Design Insights)

**CR-09：相容邊界由使用者決定，不由 Agent 裁量。**

- **不提前建設**：選能完整滿足當前需求的最簡實作。要不要加抽象層、設定開關或插件機制，判準是「這一層**現在**有兩個以上的實際使用者嗎」，沒有就不加。
- **破壞相容屬於使用者的決策**：已發佈的套件、已上線的服務、外部專案引用的介面，都有 Agent 看不到的使用者，因此 Agent 不得自行決定破壞或保留相容性。發現舊路徑該退役，建立工項列管並提出；使用者拍板之後，整條路徑一次移除乾淨，不留相容層或遷移殘骸。

這一條刻意不採用「一律移除相容層」的常見寫法。差別在誰決定：退役是使用者的決策，執行才是 Agent 的工作。

**CR-10：以契約完整性取代難度分級。**

- **不設委派難度分級**：等級是對難度的事前預測，預測不準又無從校準，而判級者有低估難度好把工項發出去的動機。
- **契約三段是交派門檻**：可委派的工項要具備輸入、產出與驗收判準、限制三段，缺一段就先補完再交。判準是把工項交給一個不在場、沒有這段對話脈絡的執行者，它能不能只讀這個工項就動手；不能，就是還有留白。

## 使用者可調整與自訂的區塊

本套件的治理設計明確區分了**不變的安全底線**與**使用者可自由調整的專案區塊**：

### 不可更動的治理核心（Invariants）
- **四個不變量**：動手前有紀錄、越界前有授權、宣稱後有證據、不可復原的操作有退路。
- **核心硬約束 (Hard Constraints)**：寫向遠端需當次授權、禁止 `rm -rf`、外部記錄只做可逆狀態轉換、交付物不得出現機敏值與本機絕對路徑、宣稱與證據同處可見等。這些是防範嚴重操作災難的全域底線，Agent 照字面嚴格執行，不留裁量空間。

### 使用者可自由調整的區塊
- **專案規範正本 (`AGENTS.md`)**：
  - 專案自訂的唯一主要入口。複製 `assets/agents-template.md` 至專案根目錄並命名為 `AGENTS.md` 後，使用者自由填寫與自訂：專案定位、路徑與檔案結構、修改邊界、自訂的 `Always` / `Never` 行為規則。
  - **擴充專案專屬約束**：若專案有特定安全或架構紅線，例如特定核心目錄唯讀、敏感環境變數禁止提取、特定部署指令需額外確認，可在 `AGENTS.md` 的 `#### Never` 中自行擴充專案專屬的硬約束。
- **開發方法選擇 (`references/methods/`)**：
  - 治理規範不限定特定開發方法。使用者或任務可依需求宣告採用 `test-first`（測試先行）、`brainstorm-and-plan`（兩階段規劃）、外部業界標準方法（如 TDD、BDD），或直接宣告「不適用」。
- **工項與架構決策範本 (`assets/`)**：
  - `task-template.md` 與 `decision-template.md` 僅提供基礎結構，使用者團隊可依既有工作流自由增刪欄位。

## 目錄結構

```
agent-discipline/
├── README.md                                   # 本說明文件
├── LICENSE                                     # MIT 開源授權
├── CONTRIBUTING.md                             # 貢獻與治理指南
└── skills/
    ├── agent-engineering-discipline/
    │   ├── SKILL.md                            # 主入口：規則導覽、任務階段對照、腳本用法
    │   ├── references/
    │   │   ├── core-rules/                     # 11 條核心約束規範
    │   │   └── methods/                        # 2 份執行方法的校準
    │   ├── assets/                             # 治理範本：agents-template.md, task-template.md, decision-template.md
    │   └── scripts/check_skill_spec.py         # 無依賴結構檢查，驗 frontmatter 與連結
    └── deliverable-writing-audit/
        ├── SKILL.md                            # 主入口：稽核步驟、模式、分級、輸出格式
        ├── references/
        │   ├── pattern-catalog.md              # 28 條徵狀：徵狀、理由、修法、例外、證據、偵測
        │   ├── profile-matrix.md               # 各徵狀在六種交付情境下的寬容度
        │   ├── category-map.md                 # 哪些徵狀由腳本偵測、哪些由判讀
        │   └── methodology-grounding.md        # 徵狀與既有理論框架的對照
        └── scripts/detect.py                   # 無依賴偵測腳本
```

## 貢獻與授權

- 歡迎提出 Issue。Pull Request 視為提案，採納後隨下一個版本發布，處理方式見 [CONTRIBUTING.md](CONTRIBUTING.md)。
- 本專案採用 [MIT License](LICENSE) 釋出。

