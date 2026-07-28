import json
import os
from datetime import datetime

import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DRIVE_SCOPE = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
ROOT_FOLDER = "AI_COMPANY_RUNNER_ARTIFACTS"


def main():
    st.set_page_config(page_title="AI COMPANY", layout="wide")
    _styles()
    _auth_gate()

    st.title("AI COMPANY")
    st.caption("Google Driveを正データとして表示します。投稿・更新・削除は行いません。")

    service, auth_error = _drive_service()
    if auth_error:
        _render_setup(auth_error)
        return

    files, load_error = _load_drive_artifacts(service)
    if load_error:
        st.error(load_error)
        return

    docs = {item["path"]: item for item in files}
    latest = _latest_daily_docs(docs)
    kpi = _find_doc(docs, "KPI_DASHBOARD.md", latest)
    ceo = _find_doc(docs, "CEO_REPORT.md", latest)
    run = _find_doc(docs, "RUN_REPORT.md", latest)
    p002 = _find_by_suffix(docs, "03_SNS事業部/04_Daily/DAILY_BRIEF.md")
    p003 = _find_by_suffix(docs, "04_グラビア事業部/DAILY_BRIEF.md")

    _system_cards(kpi, ceo, run, p002, p003)
    _kpi_cards(kpi.get("content", ""))
    _top3(ceo.get("content", ""), p002.get("content", ""), p003.get("content", ""))
    _blockers(ceo.get("content", ""), p002.get("content", ""), p003.get("content", ""))
    _ceo_comment(ceo.get("content", ""))
    _details({
        "KPI_DASHBOARD.md": kpi,
        "CEO_REPORT.md": ceo,
        "RUN_REPORT.md": run,
        "P002 DAILY_BRIEF.md": p002,
        "P003 DAILY_BRIEF.md": p003,
    })


def _auth_gate():
    password = os.getenv("DASHBOARD_PASSWORD", "").strip()
    if not password or st.session_state.get("ok"):
        return
    st.subheader("Login")
    with st.form("login"):
        entered = st.text_input("Password", type="password")
        submitted = st.form_submit_button("ログイン", use_container_width=True)
    if submitted and entered == password:
        st.session_state["ok"] = True
        st.rerun()
    if submitted:
        st.error("パスワードが違います。")
    st.stop()


def _drive_service():
    token_json = os.getenv("GOOGLE_DRIVE_OAUTH_TOKEN_JSON", "").strip()
    if not token_json:
        return None, "GOOGLE_DRIVE_OAUTH_TOKEN_JSON が未設定です。"
    try:
        info = json.loads(token_json)
        scopes = info.get("scopes") or info.get("scope") or []
        if isinstance(scopes, str):
            scopes = scopes.split()
        if not set(DRIVE_SCOPE).issubset(set(scopes)):
            return None, "Google Drive tokenにdrive scopeがありません。ローカルでDrive OAuthを再発行してください。"
        credentials = Credentials.from_authorized_user_info(info, DRIVE_SCOPE)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials.valid:
            return None, "Google Drive tokenが無効です。"
        return build("drive", "v3", credentials=credentials), ""
    except Exception as exc:
        return None, f"Google Drive認証エラー: {exc}"


@st.cache_data(ttl=300)
def _load_drive_artifacts(_service):
    try:
        root = _find_folder(_service, ROOT_FOLDER)
        if not root:
            return [], f"Drive folderが見つかりません: {ROOT_FOLDER}"
        files = []
        _walk(_service, root["id"], ROOT_FOLDER, files, depth=0)
        return files, ""
    except Exception as exc:
        return [], f"Drive読込エラー: {exc}"


def _find_folder(service, name):
    q = " and ".join([
        "trashed = false",
        f"name = '{_escape(name)}'",
        f"mimeType = '{FOLDER_MIME}'",
    ])
    res = service.files().list(q=q, fields="files(id,name,mimeType)", pageSize=1).execute()
    files = res.get("files", [])
    return files[0] if files else None


def _walk(service, folder_id, prefix, out, depth):
    if depth > 5:
        return
    page_token = None
    while True:
        res = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id,name,mimeType,modifiedTime)",
            pageSize=100,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        for item in res.get("files", []):
            path = f"{prefix}/{item['name']}"
            if item.get("mimeType") == FOLDER_MIME:
                _walk(service, item["id"], path, out, depth + 1)
            elif item["name"].endswith((".md", ".json")):
                out.append({
                    "path": path,
                    "name": item["name"],
                    "modifiedTime": item.get("modifiedTime", ""),
                    "content": _read_text(service, item),
                })
        page_token = res.get("nextPageToken")
        if not page_token:
            break


def _read_text(service, item):
    try:
        if item.get("mimeType") == GOOGLE_DOC_MIME:
            data = service.files().export_media(fileId=item["id"], mimeType="text/plain").execute()
        else:
            data = service.files().get_media(fileId=item["id"]).execute()
        return data.decode("utf-8")
    except Exception as exc:
        return f"未取得: {exc}"


def _latest_daily_docs(docs):
    dates = []
    for path in docs:
        parts = path.split("/")
        for part in parts:
            if len(part) == 10 and part[4] == "-" and part[7] == "-":
                dates.append(part)
    return sorted(dates)[-1] if dates else ""


def _find_doc(docs, name, latest_date=""):
    candidates = [v for k, v in docs.items() if k.endswith("/" + name)]
    if latest_date:
        dated = [v for v in candidates if f"/{latest_date}/" in v["path"]]
        if dated:
            return _newest(dated)
    return _newest(candidates)


def _find_by_suffix(docs, suffix):
    return _newest([v for k, v in docs.items() if k.endswith(suffix)])


def _newest(items):
    if not items:
        return {"path": "未取得", "content": "", "modifiedTime": ""}
    return sorted(items, key=lambda x: x.get("modifiedTime", ""))[-1]


def _system_cards(kpi, ceo, run, p002, p003):
    st.subheader("システム状態")
    cols = st.columns(5)
    items = [("KPI", kpi), ("CEO", ceo), ("Runner", run), ("SNS", p002), ("グラビア", p003)]
    for col, (label, doc) in zip(cols, items):
        ok = bool(doc.get("content"))
        icon = "🟢" if ok else "🔴"
        col.markdown(f"<div class='card'><h3>{icon} {label}</h3><p>{doc.get('modifiedTime') or '未取得'}</p></div>", unsafe_allow_html=True)


def _kpi_cards(text):
    st.subheader("KPI")
    labels = ["posts", "published", "categories", "tags", "clicks", "impressions", "ctr", "position", "users", "sessions", "page_views"]
    values = {label: _value_after(text, label) for label in labels}
    cols = st.columns(4)
    for i, label in enumerate(labels[:8]):
        cols[i % 4].metric(label, values.get(label) or "未取得")


def _top3(ceo, p002, p003):
    st.subheader("今日やること TOP3")
    source = ceo or p003 or p002
    items = _section_lines(source, "Priority 1")[:4] or _section_lines(source, "今日やること TOP3")[:12]
    if not items:
        st.info("未取得")
        return
    for idx, line in enumerate([x for x in items if x.strip()][:3], start=1):
        st.markdown(f"<div class='task'><b>{idx}. {line}</b></div>", unsafe_allow_html=True)


def _blockers(*texts):
    st.subheader("Blocker")
    lines = []
    for text in texts:
        lines.extend(_section_lines(text, "Blocker")[:6])
    lines = [line for line in lines if line and line not in {"---", "なし"}]
    if lines:
        st.warning("\n".join(lines[:10]))
    else:
        st.success("Blockerなし")


def _ceo_comment(text):
    st.subheader("AI社長コメント")
    comment = "\n".join(_section_lines(text, "CTOコメント")[:8]).strip()
    st.info(comment or "未取得")


def _details(items):
    st.subheader("詳細レポート")
    for title, item in items.items():
        with st.expander(title):
            st.caption(item.get("path", "未取得"))
            st.markdown(item.get("content") or "未取得")


def _render_setup(error):
    st.error(error)
    st.markdown("""
    ## Render Environment Variables

    必須:

    - `DASHBOARD_PASSWORD`
    - `AI_COMPANY_NON_INTERACTIVE=1`
    - `GOOGLE_DRIVE_OAUTH_TOKEN_JSON`
    - `P003_WORDPRESS_URL`

    `GOOGLE_DRIVE_OAUTH_TOKEN_JSON` は `.secrets/google_token.json` の中身全体を貼り付けます。
    """)


def _section_lines(text, heading):
    lines = text.splitlines()
    out = []
    active = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("##") and heading in stripped:
            active = True
            continue
        if active and stripped.startswith("##"):
            break
        if active and stripped:
            out.append(stripped.lstrip("-・ "))
    return out


def _value_after(text, key):
    for line in text.splitlines():
        lowered = line.lower()
        if key.lower() in lowered:
            parts = line.replace("|", " ").replace(":", " ").split()
            for part in reversed(parts):
                cleaned = part.strip("` ,")
                if cleaned.replace(".", "", 1).isdigit():
                    return cleaned
    return ""


def _escape(value):
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _styles():
    st.markdown("""
    <style>
      .card {border:1px solid #2f3440; border-radius:8px; padding:14px; background:#121821; min-height:96px;}
      .card h3 {font-size:18px; margin:0 0 8px 0;}
      .card p {font-size:12px; color:#a8b0bd; margin:0;}
      .task {border-left:4px solid #4f8cff; padding:12px; margin:8px 0; background:#101722; border-radius:6px;}
    </style>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
