# 兩階段規劃 (Brainstorm And Plan)

收到複雜功能開發或架構重構需求時，先走兩個階段再動手：

1. **研析**：閱讀專案原始碼與既有設計文件，釐清現況與約束。**這個階段不得修改任何程式碼。**
2. **撰寫 Implementation Plan**：在專案或快取區產出 `implementation_plan.md`，內含目標說明、需使用者審核的項目、開放問題、以及預計變更的檔案清單。

Plan 產出後立即停止呼叫工具，等待使用者給予 Proceed 或修改意見。規劃階段的授權邊界見 [Core Rule 06](../core-rules/06-authorization-boundary.md)：使用者說「先討論」、「先確認」時，提出方案就停，不要接著實作。
