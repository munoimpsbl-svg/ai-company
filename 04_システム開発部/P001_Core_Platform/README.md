# P001 Core Platform

AI COMPANY全体で利用する共通基盤ライブラリです。

---

## 目的

P003（グラビア事業部）、P004（アダルト事業部）、P002（SNS事業部）、AI社長が共通で利用する機能を提供します。

---

## 環境構築

### Python仮想環境

```bash
python3 -m venv .venv
```

### 仮想環境の有効化

macOS / Linux

```bash
source .venv/bin/activate
```

Windows

```powershell
.venv\Scripts\activate
```

### ライブラリ

```bash
pip install -r requirements.txt
```

---

## 認証情報

Google Drive認証情報はコードへ直書きしません。

`.env` または環境変数で管理します。

設定例は `.env.example` を参照してください。

---

## 現在の機能

- Google Drive接続
- REPORT保存
- REVIEW保存
- テンプレート読込
- ログ出力

---

## 今後追加予定

- AI社長連携
- Dashboard
- Google Calendar連携
- Gmail連携