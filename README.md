# 鍓嶆部鏃ユ姤锛圖aily Digest锛夝煔€

**鍓嶆部鏃ユ姤**鏄竴涓嫭绔嬭繍琛岀殑姣忔棩绠€鎶ョ郴缁燂紝鑱氱劍**澶фā鍨嬪簲鐢ㄥ紑鍙?*涓?*澶фā鍨嬬畻娉?*锛岃嚜鍔ㄨ仛鍚堜俊鎭簮銆佽瘎鍒嗘帓搴忓苟鐢熸垚鍙鐨勬棩鎶ラ〉闈紙鍚師鏂囬摼鎺ワ級銆傪煣犫湪

## 鍔熻兘鐗规€?鉁?
- 鍗曢〉闈?Dashboard锛氱敓鎴愭棩鎶?+ 娴忚鍘嗗彶
- RSS 浼樺厛鎶撳彇锛?*鍒楄〃椤?fallback**锛堟棤 RSS 鏃跺厹搴曪級
- LLM 鐩稿叧鎬ц瘎鍒嗭紙鍙€夛級+ 鍏抽敭璇嶅厹搴?
- 鍙厤缃?*鐩稿叧鎬ф渶浣庨槇鍊?*锛圡IN_RELEVANCE_SCORE锛?
- 鏈湴 SQLite 瀛樺偍

## 鏈湴鎷夊彇鍚庨渶瑕佽嚜琛岄厤缃殑鍐呭 鈿欙笍
鎷夊彇浠ｇ爜鍚庯紝浣犻渶瑕佹寜瀹為檯鎯呭喌琛ュ叏浠ヤ笅閰嶇疆锛?
1. `.env`锛堜粠 `.env.example.safe` 澶嶅埗骞跺～鍐欙級
   - `GITHUB_TOKEN`锛氶伩鍏?GitHub API 闄愭祦
   - `HF_TOKEN`锛氳闂?Hugging Face锛堝缃戠粶鍙揪锛?
   - `MIN_RELEVANCE_SCORE`锛氫綆浜庤鍒嗘暟涓嶅睍绀?
2. `configs/providers.yaml`
   - 浠?`configs/providers.example.yaml` 澶嶅埗骞跺～鍐欑湡瀹?API Key/妯″瀷淇℃伅
3. `configs/sources.yaml`
   - 鏍规嵁闇€姹傚惎鐢?绂佺敤鏁版嵁婧愭垨璋冩暣 RSS/鍒楄〃椤甸摼鎺?



## 绯荤粺鍔熻兘姒傝 馃З
1. 澶氭簮鎶撳彇锛氭敮鎸?RSS 涓庡垪琛ㄩ〉涓ょ鏂瑰紡锛孯SS 浼樺厛锛屽垪琛ㄩ〉鍏滃簳
2. 姝ｆ枃琛ュ叏锛氬鍊欓€夋潯鐩姄鍙栨鏂囷紝鎻愬崌鎽樿涓庤瘎鍒嗚川閲?
3. 鐩稿叧鎬ц瘎鍒嗭細浼樺厛浣跨敤 LLM 璇勫垎锛屽け璐ユ椂鍥為€€鍒板叧閿瘝绛栫暐
4. 鎺掑簭涓庤繃婊わ細鎸夌浉鍏虫€ч檷搴忥紝骞跺簲鐢ㄦ渶浣庨槇鍊艰繃婊?
5. 鏃ユ姤灞曠ず锛氬崟椤甸潰鏌ョ湅銆佸垏鎹㈡棩鏈熴€佹墜鍔ㄨЕ鍙戠敓鎴?

## 鐩綍缁撴瀯 馃梻锔?
`
app/                      FastAPI 搴旂敤鍏ュ彛
app/daily_digest/         鏃ユ姤鏍稿績閫昏緫锛堟姄鍙?/ 璇勫垎 / 瀛樺偍 / UI锛?
app/static/               鍓嶇璧勬簮
configs/                  鏁版嵁婧愪笌 provider 閰嶇疆
data/                     鏈湴鏁版嵁搴?
`

## 蹇€熷紑濮?鈿?

### 1锛夊畨瑁呬緷璧?馃摝
```bash
pip install -r requirements.txt
```

### 2锛夐厤缃幆澧冨彉閲?馃敡
澶嶅埗 .env.example.safe 涓?.env锛屽苟濉啓蹇呰閰嶇疆锛?
```bash
copy .env.example.safe .env
```

鍏抽敭瀛楁璇存槑锛?
- OPENAI_API_KEY / OPENAI_BASE_URL锛氱敤浜庣浉鍏虫€ц瘎鍒嗭紙鍙€夛級
- GITHUB_TOKEN锛氶伩鍏?GitHub API 闄愭祦
- HF_TOKEN锛氳闂?Hugging Face锛堝缃戠粶鍙揪锛?
- JIQIZHIXIN_TOKEN锛氭満鍣ㄤ箣蹇?MCP/RSS 閴存潈 token锛堢敤浜庤嚜鍔ㄦ嫾鎺ュ埌 mcp.applications.jiqizhixin.com 閾炬帴锛?
- MIN_RELEVANCE_SCORE锛氫綆浜庤鍒嗘暟涓嶅睍绀猴紙榛樿 15锛?

Provider 绀轰緥锛?
- configs/providers.example.yaml

### 3锛夊惎鍔ㄦ湇鍔?鈻讹笍
```bash
.\.venv\Scripts\activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

璁块棶椤甸潰锛?
- http://localhost:8001/daily-digest

## 浣跨敤鏂瑰紡 鉁?
- 鐐瑰嚮 **鐢熸垚鏃ユ姤** 鍙寜褰撳墠鏃ユ湡鐢熸垚
- 榛樿鐢熸垚鈥滃墠涓€澶┾€濈殑鏃ユ姤

### API 鎺ュ彛 馃攲
- GET /api/daily-digest?date=YYYY-MM-DD
- POST /api/daily-digest/run锛圝SON锛歿 "date": "YYYY-MM-DD", "force": true }锛?
- GET /api/daily-digest/status?date=YYYY-MM-DD

## 鏁版嵁婧愰厤缃?馃寪
缂栬緫 configs/sources.yaml锛?
- rss_url锛歊SS 鍦板潃锛堜紭鍏堜娇鐢級
- list_url锛氬垪琛ㄩ〉鍦板潃锛堟棤 RSS 鎴?RSS 涓虹┖鏃朵娇鐢級

琛屼负瑙勫垯锛?
- 鏈?rss_url锛氬厛鐢?RSS 鎷夊€欓€夛紝鍐嶇敤鏂囩珷椤佃ˉ姝ｆ枃
- 鏃?rss_url锛氱洿鎺ヤ娇鐢?list_url 鍋氬垪琛ㄨВ鏋?

## 鏁版嵁婧愬彲鐢ㄦ€ф祴璇曡剼鏈?馃И
杩愯鑴氭湰妫€鏌ュ悇鏁版嵁婧愭槸鍚﹀彲璁块棶锛?
```bash
python scripts/check_sources.py
```
杈撳嚭浼氬垎鍒爣娉?RSS/鍒楄〃椤?缁撴瀯鍖栭〉闈㈢殑鍙敤鎬х姸鎬併€?

## 褰撳墠鏀寔鐨勬暟鎹簮锛堜互 configs/sources.yaml 涓哄噯锛夝煋?
璇存槑锛氬彲鐢ㄦ€у彈缃戠粶鐜銆佸弽鐖瓥鐣ャ€佸湴鍖洪檺鍒跺奖鍝嶏紝寤鸿浠ユ湰鍦伴獙璇佽剼鏈粨鏋滀负鍑嗐€?

| 鏁版嵁婧?| 鑾峰彇鏂瑰紡 | 鍙敤鎬ф爣娉?|
| --- | --- | --- |
| arXiv锛坈s.AI / cs.CL / cs.LG锛?| RSS | 涓€鑸彲鐢?|
| GitHub Watchlist锛圧eleases锛?| API | 闇€ Token锛屾槗闄愭祦 |
| Hugging Face Papers / Trending / Blog | 缁撴瀯鍖栭〉闈?| 鍙兘鍙楅檺锛屾槗闄愭祦 |
| Hacker News | RSS | 涓€鑸彲鐢?|
| Google Blog锛圛nnovation & AI锛?| RSS / 鍒楄〃椤?| 鍙兘鍙樻洿 |
| Reddit r/MachineLearning | RSS | 鍙兘鍙楅檺 |
| Reddit r/LocalLLaMA | RSS | 鍙兘鍙楅檺 |
| Lobsters | RSS | 涓€鑸彲鐢?|
| 鏈哄櫒涔嬪績 | RSS / 鍒楄〃椤?| 鍙兘鍙楅檺 |
| 閲忓瓙浣?| RSS / 鍒楄〃椤?| 鍙兘鍙楅檺 |
| 36 姘?AI 涓撴爮 | 鍒楄〃椤?| 鍙兘鍙楅檺 |
| InfoQ AI | RSS / 鍒楄〃椤?| 涓€鑸彲鐢?|
| 闆峰嘲缃?AI | RSS / 鍒楄〃椤?| 鍙兘鍙楅檺 |
| 鏋佸鍏洯 AI | 鍒楄〃椤?| 鍙兘鍙楅檺 |
| 鐖辫寖鍎?AI | RSS / 鍒楄〃椤?| 涓€鑸彲鐢?|
| AIGC 寮€鏀剧ぞ鍖?| 鍒楄〃椤?| 鍙兘鍙楅檺 |
| 澶фā鍨嬩箣瀹?| 鍒楄〃椤?| 鍙兘鍙楅檺 |
| AI 鍓嶇嚎 | 鍒楄〃椤?| 鍙兘鍙楅檺 |
| 鏅烘簮绀惧尯 | 鍒楄〃椤?| 涓€鑸彲鐢?|
| 鎺橀噾 AI | 鍒楄〃椤?| 涓€鑸彲鐢?|
| CSDN AI | 鍒楄〃椤?| 涓€鑸彲鐢?|
| PaperWeekly | 鍒楄〃椤?| 鍙兘鍙楅檺 |
| 闆嗘櫤淇变箰閮?| 鍒楄〃椤?| 涓€鑸彲鐢?|

## 甯歌闂 鉂?
- 鏌愪簺绔欑偣 404/403锛氬缓璁鐢ㄦ垨鎹㈠垪琛ㄩ〉
- HF 鏃犳硶璁块棶锛氬彲鑳介渶瑕?Token 鎴栦唬鐞?
- 鐘舵€佹帴鍙ｆ棩蹇楀埛灞忥細鍓嶇杞姝ｅ父鐜拌薄

## 鏇存柊鏃ュ織 馃摑
### 2026-03-20
- 鎷嗗垎涓虹嫭绔嬮」鐩紝淇濈暀鍗曢〉闈㈡棩鎶ユ祦绋?
- 鏂板 RSS 浼樺厛 + 鍒楄〃椤靛厹搴曟姄鍙栫瓥鐣?
- 鏂板鐩稿叧鎬ф渶浣庨槇鍊?`MIN_RELEVANCE_SCORE`
- 瀹屾垚鍓嶇鏍峰紡涓庝氦浜掍紭鍖?

