---
theme: seriph
title: IQC 進貨抽檢系統
class: text-center
highlighter: shiki
drawings:
  persist: false
transition: slide-left
mdc: true
background: none
---

<div class="absolute inset-0" style="background: radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,0.25), transparent), radial-gradient(ellipse 60% 50% at 80% 110%, rgba(34,197,94,0.12), transparent), #0b0d12;"></div>

<div class="absolute inset-0 opacity-[0.05]" style="background-image: linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px); background-size: 48px 48px;"></div>

<div class="relative flex h-full flex-col items-center justify-center">

<div class="mb-6 flex size-16 items-center justify-center rounded-2xl shadow-2xl" style="background: linear-gradient(135deg, #6366f1, #8b5cf6);">
  <carbon-security class="text-3xl text-white" />
</div>

<h1 class="!text-5xl !font-bold tracking-tight">
  IQC 進貨抽檢系統
</h1>

<p class="mt-3 text-xl opacity-70">紙本檢驗流程數位化</p>

<div class="mt-8 flex gap-3 text-sm">
  <span class="rounded-full border border-indigo-400/40 bg-indigo-500/10 px-4 py-1.5 text-indigo-300">自動判定</span>
  <span class="rounded-full border border-emerald-400/40 bg-emerald-500/10 px-4 py-1.5 text-emerald-300">三道防呆</span>
  <span class="rounded-full border border-amber-400/40 bg-amber-500/10 px-4 py-1.5 text-amber-300">AI 輔助比對</span>
</div>

<div class="mt-12 text-sm opacity-40">
LED 燈具進貨/出貨抽檢 · 2026-08-04
</div>

</div>

<!--
各位好,今天跟大家報告的是進貨抽檢系統。

一句話說:我們把現在紙本的抽檢流程整個數位化了,而且系統已經做完、已經上線,今天會展示實際成果。

接下來大概十分鐘,我會先講現在紙本流程的問題,再講系統怎麼解決,最後講接下來的計畫。
-->

---

# 現況痛點:紙本抽檢的隱形成本

- 📝 **手抄數據** — 積分球測完報告,檢驗員逐格抄寫功率、色溫、光通量,抄錯即誤判
- 🧮 **人工算範圍** — 「標稱 15W 的 90%~110%」每個型號都要現場心算上下限
- 🖊️ **螢光筆標異常** — 超標與否靠人眼比對,漏標就流出
- 👀 **主機板比對靠肉眼** — 拆解後板上型號 vs 認證登記,一字之差(G4/B4)最容易看走眼
- 🚦 **流程靠人自覺** — 不合格該做二次拆檢、簽核前該逐項核對,漏了沒有任何機制擋住
- 📁 **追溯困難** — 客訴時翻紙本找半天,「當時為什麼判合格」說不清楚

<div class="mt-8 rounded-lg bg-red-500/10 p-4 text-red-400">
每一步都依賴「人不出錯」— 而人一定會出錯
</div>

<!--
先看現在的做法有什麼問題,六個痛點。

積分球測完,檢驗員要把六個數字一格一格抄到表單上——抄錯一位,合格變不合格。
合格範圍要現場心算:標稱15瓦,下限90%上限110%,每個型號都算一次。
超標了怎麼辦?拿螢光筆畫起來——全靠眼睛,漏畫就流出去了。
主機板上的型號跟認證登記要用肉眼比對,G4跟B4一字之差,最容易看走眼。
還有,不合格該做二次拆檢、主管簽核前該逐項核對——這些全靠自覺,漏了沒人知道。
最後,客訴的時候要翻紙本,半年前那張單為什麼判合格,說不清楚。

總結一句:每一步都在賭「人不出錯」。而人,一定會出錯。
-->

---

# 解決方案:一套系統管完整個檢驗流程

<div class="rounded-lg bg-green-500/10 p-3 text-green-400 text-sm">
✅ 系統已開發完成、已上線運行 — 今天報告的是「成果」,不是「計畫」
</div>

<div class="grid grid-cols-3 gap-6 pt-8">

<div class="rounded-xl border border-gray-500/30 p-5">
<div class="text-3xl">⚡</div>
<h3 class="mt-2">自動化</h3>
<p class="text-sm opacity-75">積分球 PDF 一鍵匯入、合格範圍自動計算、異常自動高亮 — 取代手抄、心算、螢光筆</p>
</div>

<div class="rounded-xl border border-gray-500/30 p-5">
<div class="text-3xl">🛡️</div>
<h3 class="mt-2">防呆</h3>
<p class="text-sm opacity-75">不合格強制二次拆檢、標示未確認不能簽核 — 規則由系統強制,不靠自覺</p>
</div>

<div class="rounded-xl border border-gray-500/30 p-5">
<div class="text-3xl">🔍</div>
<h3 class="mt-2">可追溯</h3>
<p class="text-sm opacity-75">誰、何時、做了什麼全程留痕;簽核後永久鎖定 — 稽核、客訴隨時拿得出證據</p>
</div>

</div>

<!--
我們的解法是一套系統把整個流程包起來。先強調最上面這行:系統已經開發完成、已經上線——今天報告的是成果,不是計畫書。

三個核心價值,正好對應剛才的痛點:
第一,自動化——手抄、心算、螢光筆,這三件事系統全部代勞。
第二,防呆——剛才說流程靠自覺,現在該做的步驟系統會強制,想跳過都跳不過。
第三,可追溯——每個動作誰做的、什麼時候做的,全部留紀錄,簽核之後就鎖定。

接下來一頁一頁展示。
-->

---

# 檢驗流程:數位化後的完整動線

<div class="flex items-stretch gap-1.5 pt-10">

<div class="flex-1 rounded-xl border border-gray-500/30 bg-gray-500/5 p-3 text-center">
  <div class="mx-auto mb-2 flex size-8 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">1</div>
  <div class="text-sm font-semibold">建檢驗單</div>
  <div class="mt-1 text-xs leading-snug opacity-60">選產品<br/>標準自動帶出</div>
</div>
<div class="flex items-center text-lg text-gray-500">›</div>

<div class="flex-1 rounded-xl border border-gray-500/30 bg-gray-500/5 p-3 text-center">
  <div class="mx-auto mb-2 flex size-8 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">2</div>
  <div class="text-sm font-semibold">匯入積分球 PDF</div>
  <div class="mt-1 text-xs leading-snug opacity-60">六項數據<br/>自動解析</div>
</div>
<div class="flex items-center text-lg text-gray-500">›</div>

<div class="flex-1 rounded-xl border border-gray-500/30 bg-gray-500/5 p-3 text-center">
  <div class="mx-auto mb-2 flex size-8 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">3</div>
  <div class="text-sm font-semibold">拍標示照</div>
  <div class="mt-1 text-xs leading-snug opacity-60">手機直接拍<br/>主機板特寫</div>
</div>
<div class="flex items-center text-lg text-gray-500">›</div>

<div class="flex-1 rounded-xl border border-indigo-400/50 bg-indigo-500/10 p-3 text-center">
  <div class="mx-auto mb-2 flex size-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white">4</div>
  <div class="text-sm font-semibold">系統自動判定</div>
  <div class="mt-1 text-xs leading-snug opacity-60">超標即時<br/>紅框高亮</div>
</div>
<div class="flex items-center text-lg text-gray-500">›</div>

<div class="flex-1 rounded-xl border border-gray-500/30 bg-gray-500/5 p-3 text-center">
  <div class="mx-auto mb-2 flex size-8 items-center justify-center rounded-full bg-indigo-500 text-sm font-bold text-white">5</div>
  <div class="text-sm font-semibold">主管審核簽核</div>
  <div class="mt-1 text-xs leading-snug opacity-60">比對標示<br/>異常已標好</div>
</div>
<div class="flex items-center text-lg text-gray-500">›</div>

<div class="flex-1 rounded-xl border border-emerald-400/40 bg-emerald-500/10 p-3 text-center">
  <div class="mx-auto mb-2 flex size-8 items-center justify-center rounded-full bg-emerald-600 text-sm font-bold text-white">6</div>
  <div class="text-sm font-semibold">Excel 歸檔</div>
  <div class="mt-1 text-xs leading-snug opacity-60">格式同紙本<br/>結案留痕</div>
</div>

</div>

<div class="mt-5 grid grid-cols-2 gap-4 text-xs">
<div class="rounded-lg border border-red-400/30 bg-red-500/5 p-3">
  <b class="text-red-400">④ 判定不合格</b> → 🛡️ 系統強制二次拆檢(第二件數據)→ 完成後才准送審
</div>
<div class="rounded-lg border border-amber-400/30 bg-amber-500/5 p-3">
  <b class="text-amber-400">⑤ 主管退件</b> → 自動開立不良品異常單 → 歸檔留痕
</div>
</div>

<div class="mt-5 text-sm opacity-70">
與現行紙本流程一一對應 — 檢驗員不用改變工作習慣,只是把紙換成畫面
</div>

<!--
這是數位化之後的完整動線,從左到右念一次:

收到進貨通知,建一張檢驗單——選產品,標準自動帶出來。積分球報告用PDF直接匯入,不用抄。主機板標示用手機拍照上傳。然後系統自動判定。

判定不合格的話——注意這裡——系統會「強制」要求做第二件的二次拆檢,做完才能送給主管審核。主管審核時異常項目已經自動標出來,簽核通過就匯出Excel報表,退件就開異常單。

重點是:這條動線跟現在紙本流程是一一對應的,檢驗員不用改變工作習慣,只是把紙換成了畫面。
-->

---
layout: image-right
image: /images/list.png
backgroundSize: contain
---

# 系統實際畫面

**檢驗單列表**

- 一張單 = 一個貨櫃
- 狀態一目了然:草稿 → 待審核 → 已簽核 → 已歸檔
- QC 日期自動帶入當天
- 手機、平板、電腦都能用<br/>(檢驗員現場拿手機操作)

<!--
右邊是系統的實際畫面,不是設計稿——這是已經在跑的系統。

檢驗單列表,一張單對應一個貨櫃。每張單的狀態一眼就看到:草稿、待審核、已簽核、已歸檔。

特別說一下,這個系統手機、平板、電腦都能用——檢驗員在現場就是拿手機操作,拍照直接叫出相機,不用回辦公室。
-->

---

# 積分球數據:從手抄到一鍵匯入

<div class="grid grid-cols-2 gap-8 pt-4">

<div>

### 以前
1. 積分球軟體印出報告
2. 檢驗員逐格手抄 6 個數字
3. 抄錯、看錯行、單位搞混…

</div>

<div>

### 現在
1. 報告 PDF 拖進系統
2. **自動解析**光通量、色溫、功率、光效、PF、CRI
3. 人工核對一眼 → 按「確認數據」

</div>

</div>

<div class="mt-6 rounded-lg bg-blue-500/10 p-4 text-sm">
💡 三層保險:PDF 文字層解析(100% 保真)→ 辨識不到退人工輸入 → 確認畫面把關<br/>
數據永遠經過人眼確認才進判定,系統不會「自作主張」
</div>

<!--
第一個亮點:積分球數據匯入。

以前:軟體印報告,檢驗員手抄六個數字——光通量、色溫、功率、光效、PF、CRI。抄錯、看錯行、單位搞混,都發生過。

現在:報告PDF直接拖進系統,六個數字自動解析、自動填好。檢驗員只做一件事——看一眼、按確認。

底下這行很重要:我們設計了三層保險。PDF解析是讀文字層,百分之百保真;萬一解析不到,退回人工輸入;而且不管哪條路,數據都要人眼確認過才進判定——系統不會自作主張。
-->

---
layout: image-right
image: /images/detail.png
backgroundSize: contain
---

# 自動判定與異常高亮

**取代人工計算和螢光筆**

- 合格範圍由**公式自動算**<br/>(標稱 15W → 13.5~16.5W)
- 超標欄位**自動紅框**+說明<br/>「133.0 高於上限 100」
- 一路帶到審核畫面和 Excel<br/>(黃底紅字,同螢光筆習慣)
- 判定是**規則引擎**,不是 AI —<br/>同樣數據永遠同樣結果,可稽核

<!--
第二個亮點:自動判定。

合格範圍不用心算了——標稱15瓦,系統自動算出13.5到16.5。數據一進來就判定,超標的欄位自動紅框,還告訴你原因:「133.0高於上限100」。

這個異常標記會一路帶到主管審核畫面和匯出的Excel——黃底紅字,跟現在螢光筆的習慣一樣,主管不用適應。

要特別強調:判定用的是規則引擎,不是AI。同樣的數據,永遠得到同樣的結果,原因寫得清清楚楚——這才經得起稽核。AI在我們系統裡只做輔助,等一下會講。
-->

---

# 三道防呆關卡:系統強制,不靠自覺

| 關卡 | 規則 | 沒過會怎樣 |
|------|------|-----------|
| **二次拆檢** | 判不合格 → 必須完成第二件檢驗 | 系統拒絕送審 |
| **標示照片** | 每型號必須有主機板標示特寫照 | 系統拒絕送審 |
| **主管確認** | 主管逐型號勾「標示與認證一致」 | 系統拒絕簽核 |

<div class="mt-6 text-sm opacity-75">

這些規則做在**伺服器端** — 不是畫面上的提示,是繞不過去的閘門。<br/>
對應痛點「流程靠人自覺」:該做的步驟,系統替主管把關,漏不掉。

</div>

<!--
第三個亮點,也是我認為最有價值的:防呆關卡。

三道:第一,判不合格,不做第二件的二次拆檢,系統直接拒絕送審。第二,沒拍主機板標示照,拒絕送審——因為主管審核時要有照片可以比對。第三,主管沒有逐型號勾「標示一致」的確認,系統拒絕簽核。

重點在最下面這句:這些規則做在伺服器端,不是畫面上的提醒文字——是真正繞不過去的閘門。以前靠檢驗員和主管自覺,現在系統替我們把關,想漏都漏不掉。
-->

---
layout: image-right
image: /images/products.png
backgroundSize: contain
---

# 產品主檔:新型號一分鐘上線

**每個型號的「標準答案」建檔一次**

- 標稱參數(瓦數、光通量範圍…)
- 預期主機板標示字串
- 認證照片(選填)

**兩層設計的威力**

- 檢驗標準只定義「公式」
- 新型號**不用建新標準**,<br/>填參數就自動算出合格範圍
- 現有 30 份標準 Excel 遷移入庫,<br/>檢法相同者可望共用(以實際盤點為準)

<!--
系統能自動判定,靠的是「產品主檔」——把每個型號的標準答案預先建檔:標稱幾瓦、光通量範圍多少、主機板上應該印什麼型號。

這裡有個關鍵設計叫「兩層」:檢驗標準只定義公式,比方「功率抓標稱值的正負10%」;數字放在型號的參數裡。所以新型號進來,不用建新標準——主管花一分鐘填參數,系統就自動算出這個型號的合格範圍。

我們現有的三十份標準Excel會全部遷移進系統;檢驗方法相同、只是數字不同的,有機會共用同一份標準——實際能收斂多少,盤點之後跟大家回報。
-->

---

# AI 亮點 ①:主機板標示比對

<div class="grid grid-cols-2 gap-6 pt-2">

<div>

### 怎麼運作

1. 檢驗員手機拍主機板標示特寫
2. **本機 AI 模型**讀出板上字串
3. 程式與認證登記**精確比對**
4. 🟢 一致 / 🟡 不一致提醒主管細看

### 實測成果

- 特寫照 **1.5 秒**讀出完整型號
- `G4` vs `B4` **一字之差正確抓出**<br/>(人眼最容易漏的就是這種)

</div>

<div>

### 設計底線

<div class="rounded-lg bg-amber-500/10 p-4 text-sm">

**AI 只提示,不判定。**

模型負責「讀」,比對是程式的精確邏輯,最終勾選確認永遠是主管 — AI 讀錯最多是提示沒幫上忙,不會造成誤放行。

</div>

<div class="mt-4 text-sm opacity-70">
模型在公司電腦本機運行(Ollama)<br/>照片與數據不出內網、零 API 費用
</div>

</div>

</div>

<!--
接下來兩頁講AI。第一個:主機板標示比對。

流程是:檢驗員手機拍主機板標示的特寫,本機的AI模型把板上的字串讀出來,程式拿去跟認證登記做精確比對——一致亮綠燈,不一致亮黃燈提醒主管細看。

實測數據:特寫照1.5秒讀出完整型號;最重要的是,G4跟B4一字之差,它正確抓出來了——這正是人眼最容易漏的。

但請注意右邊的設計底線:AI只提示,不判定。模型只負責「讀」,比對是程式的精確邏輯,最後打勾確認的永遠是主管。所以AI就算讀錯,最多是提示沒幫上忙,絕對不會造成誤放行。

另外,模型跑在我們自己的電腦上,照片和數據不出內網,也沒有API費用。
-->

---

# AI 亮點 ②:AI 助手

<div class="grid grid-cols-2 gap-8 pt-4">

<div>

### 能做什麼

- 讀懂**當前檢驗單的完整數據**
- 「這張單有哪些異常?」<br/>「為什麼判不合格?」— 直接回答並引用數據
- 新人詢問流程,不用翻 SOP

</div>

<div>

### 一樣有底線

- 只**解讀說明**,不參與判定
- 畫面明示:「判定以系統規則為準」
- 同樣跑在本機,資料不外流

</div>

</div>

<div class="mt-8 rounded-lg bg-gray-500/10 p-4 text-sm opacity-80">
💬 實測:問「這張檢驗單有異常嗎?」→ 正確回答狀態與判定,並引用實際量測值佐證
</div>

<!--
第二個AI功能:內建的AI助手。

它讀得懂當前這張檢驗單的完整數據。主管審核時問它「這張單有哪些異常?」「為什麼判不合格?」,它直接回答,還會引用實際的量測數字佐證。新人不熟流程,問它就好,不用翻SOP。

底線跟剛才一樣:它只解讀、只說明,不參與判定,畫面上也明白寫著「判定以系統規則為準」。而且一樣跑在本機,資料不外流。

我們實測過:問它這張單有沒有異常,它正確回答了狀態和判定結果,引用的數字也都對。
-->

---

# 稽核與追溯:每一步都有據可查

- 📜 **稽核軌跡** — 建單、錄入、判定、確認、簽核…誰在何時做了什麼,只增不改
- 🔒 **簽核即鎖定** — 已簽核的單永久唯讀,杜絕事後竄改
- 📌 **標準版本化** — 檢驗單綁定當時的標準版本,半年後回看判定依據分毫不差
- 📷 **照片政策** — 上傳自動壓縮(5MB→0.3MB);保存期限可設定,未歸檔前絕不清除
- 📊 **Excel 報表** — 格式對齊現行紙本,主管、客戶不用適應新格式

<!--
再來是追溯能力,這是品檢系統的靈魂,五件事。

第一,稽核軌跡:從建單到簽核,每個動作誰做的、什麼時候做的,全部記錄,而且只能增加不能修改。
第二,簽核即鎖定:簽核過的單永久唯讀,不可能事後改數據。
第三,標準版本化:每張單綁定「當時」的標準版本——就算之後標準改版,半年前那張單的判定依據還原得分毫不差。客訴的時候,這就是我們的底氣。
第四,照片自動壓縮,儲存成本降十幾倍,保存期限可以設定。
第五,匯出的Excel格式對齊現行紙本——主管和客戶看到的報表長得跟現在一樣,不用適應。
-->

---

# 技術架構:精簡、可靠、好維護

<div class="grid grid-cols-2 gap-8 pt-4 text-sm">

<div>

| 層 | 選型 |
|----|------|
| 後端 | Python + FastAPI |
| 前端 | Vue 3 + Tailwind |
| 資料庫 | SQLite(單檔好備份) |
| AI | Ollama 本機模型 |
| 部署 | 單一服務,一台主機全包 |

</div>

<div>

### 品質保證

- **27 個自動化測試**全數通過
- 防呆關卡逐一端對端驗證
- 前後端型別自動同步<br/>(後端改欄位,前端編譯即報錯)

### 已可展示

- 已部署上線(HTTPS)
- 手機/平板/電腦全支援

</div>

</div>

<!--
技術架構簡單帶過,重點是右邊。

左邊:技術選型都是主流、精簡的組合,一台主機就能跑完整套,包含AI——維護成本低。

右邊才是重點:目前有27個自動化測試全數通過,三道防呆關卡每一道都做過端對端驗證——不是「應該可以」,是實際擋下來過。系統已經部署上線,有HTTPS,手機平板電腦都支援,今天會後就可以開給大家看。
-->

---

# 下一步

<div class="text-sm">

| 順序 | 項目 | 說明 |
|------|------|------|
| 短期 | **30 份檢驗標準入庫** | 現有 Excel 一次性遷移,逐份人工核對 |
| 短期 | **Excel 報表模板套版** | 拿到公司原版模板後,輸出 100% 一致 |
| 接著 | **正式部署** | 搬進正式主機,含帳號密碼強化 |
| 第二期 | 標準管理後台、統計儀表板 | 主管自行維護標準;月報數據一鍵出 |

</div>

<div class="mt-4 grid grid-cols-2 gap-4 text-sm">
<div class="rounded-lg bg-green-500/10 p-3 text-green-400">
系統本體已完成並上線 — 剩下的是資料遷移與交付,不是開發風險
</div>
<div class="rounded-lg bg-blue-500/10 p-3 text-blue-400">
<b>需要的支援</b>:公司報表 Excel 模板、30 份檢驗標準檔案、正式部署主機
</div>
</div>

<!--
最後講下一步。

短期兩件事:把現有三十份檢驗標準遷移進系統,逐份人工核對;還有拿到公司報表模板後做套版,讓匯出的Excel跟現行格式百分之百一致。接著就是正式部署,搬進正式主機,帳號密碼一併強化。第二期規劃標準管理後台和統計儀表板。

左下角:系統本體已經完成並上線——剩下的是資料遷移和交付,不是開發風險。

右下角是我需要的支援,三樣:公司報表的Excel模板、三十份檢驗標準的檔案、還有正式部署用的主機。這三樣到位,短期項目就能啟動。
-->

---
layout: center
class: text-center
---

# 總結

<div class="pt-4 text-lg">

紙本抽檢的**手抄、心算、肉眼比對** → 系統的**自動解析、自動判定、AI 輔助比對**

</div>

<div class="grid grid-cols-3 gap-6 pt-10">
<div>
<div class="text-4xl font-bold text-blue-400">3 道</div>
<div class="text-sm opacity-70">伺服器端強制防呆關卡</div>
</div>
<div>
<div class="text-4xl font-bold text-green-400">1 分鐘</div>
<div class="text-sm opacity-70">新型號上線(免改程式)</div>
</div>
<div>
<div class="text-4xl font-bold text-amber-400">100%</div>
<div class="text-sm opacity-70">檢驗軌跡可追溯</div>
</div>
</div>

<div class="pt-12 opacity-60">
Q & A
</div>

<!--
總結一下。

我們把紙本抽檢的手抄、心算、肉眼比對,換成了系統的自動解析、自動判定、加上AI輔助比對。

三個數字:三道伺服器端強制的防呆關卡——該做的步驟漏不掉;新型號一分鐘上線,不用改程式;檢驗軌跡百分之百可追溯,稽核客訴都拿得出證據。

系統已經上線,歡迎會後實際操作看看。以上是我的報告,請大家指教。
-->
