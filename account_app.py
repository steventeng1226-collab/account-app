import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import requests

# ══════════════════════════════════════════
#  設定
# ══════════════════════════════════════════
APP_VERSION  = "v3.2.2"
WEBHOOK_URL  = "https://script.google.com/macros/s/AKfycby25v70CU_TEdxEs9V81tJ6W-xJkg1dZNBh6ga5Bz4LpBwO8ipa1ETIDHrzPDsYV23y/exec"
SHEET_ID    = "1lOCs8X7fzhApCoKBIp35OogqbF2Y-VVVCF3hS19q6d4"
GID         = "259728202"
CSV_URL     = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
VND_RATE    = 0.00128
CO_KEYS     = ['代墊', '公司', '固定']

CATEGORIES  = ['食', '住', '行', '育', '樂', '醫療', '代墊', '固定', '其他']
CURRENCIES  = ['TWD', 'VND', 'USD']
PAYMENTS    = ['現金', '信用卡', '簽帳卡', '銀行轉帳', '電子錢包', '其他']

# ══════════════════════════════════════════
#  頁面設定
# ══════════════════════════════════════════
st.set_page_config(
    page_title=f"流水帳 {APP_VERSION}",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ══ 隱藏所有 Streamlit 原生浮動元件 ══ */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="manage-app-button"],
.stAppDeployButton,
.viewerBadge_container__1QSob,
.styles_viewerBadge__1yB5_,
iframe[title="streamlit_analytics"] { display:none !important; }

/* ══ 強制隱藏右下角廠商 badge（多層保險） ══ */
[class*="viewerBadge"] { display:none !important; visibility:hidden !important; }
[class*="badge"] { display:none !important; }
a[href*="streamlit.io"] { display:none !important; }
a[href*="streamlit.app"] { display:none !important; }
div[class*="styles_viewerBadge"] { display:none !important; }
#badge-container { display:none !important; }
.badge-container { display:none !important; }

/* ══ 終極保險：用背景色遮罩蓋住右下角 ══ */
body::after {
    content: '';
    position: fixed;
    bottom: 0; right: 0;
    width: 180px; height: 56px;
    background: #080c14;
    z-index: 999999;
    pointer-events: none;
}

/* ══ 全域 ══ */
html, body, [class*="css"] { font-size:12px; }
.main { background:#080c14; }
.block-container {
    padding: 0.3rem 0.6rem 0.3rem !important;
    max-width: 820px;
}

/* ══ Header ══ */
.hdr {
    display:flex; align-items:center; gap:8px;
    background:linear-gradient(135deg,#0f172a,#1a2540);
    border:1px solid #1e3a8a30; border-radius:8px;
    padding:6px 12px; margin-bottom:6px;
}
.hdr-title { font-size:14px; font-weight:700; color:#e2e8f0; white-space:nowrap; }
.hdr-ver {
    font-size:9px; color:#60a5fa; background:#1e3a5f;
    border:1px solid #2563eb44; border-radius:20px;
    padding:1px 7px; font-weight:600;
}

/* ══ 分頁 ══ */
.stTabs [data-baseweb="tab-list"] {
    gap:2px; background:#0f172a; border-radius:7px;
    padding:2px; margin-bottom:6px;
}
.stTabs [data-baseweb="tab"] {
    color:#64748b; font-size:11px; font-weight:500;
    padding:4px 10px; border-radius:5px; white-space:nowrap;
}
.stTabs [aria-selected="true"] {
    color:#f1f5f9 !important; font-weight:700; background:#1e293b !important;
}

/* ══ 月份 Banner（小版） ══ */
.m-banner {
    background:linear-gradient(135deg,#0f2044,#0d1a30);
    border:1px solid #1d4ed840; border-radius:8px;
    padding:5px 10px; margin-bottom:6px; text-align:center;
}
.m-banner h3 { color:#60a5fa; font-size:12px; margin:0; font-weight:700; }
.m-banner p  { color:#64748b; font-size:10px; margin:2px 0 0; }

/* ══ 數字卡片（自訂，不用 st.metric） ══ */
.stat-row {
    display:grid; grid-template-columns:1fr 1fr 1fr 1fr;
    gap:5px; margin-bottom:6px;
}
.stat-card {
    background:#111827; border:1px solid #1f2937;
    border-radius:8px; padding:6px 8px; text-align:center;
}
.stat-lbl { color:#64748b; font-size:9px; font-weight:600; text-transform:uppercase; letter-spacing:.4px; }
.stat-val { color:#f1f5f9; font-size:15px; font-weight:700; line-height:1.2; margin-top:2px; }

/* ══ 預估條 ══ */
.est-bar {
    background:#0c1f38; border-left:3px solid #3b82f6;
    border-radius:5px; padding:4px 10px; margin-bottom:5px;
    color:#93c5fd; font-size:10px; font-weight:600;
}

/* ══ 圖表區 ══ */
.chart-row { display:grid; grid-template-columns:1fr 1fr; gap:4px; }

/* ══ 排行榜 ══ */
.rank-table { width:100%; border-collapse:collapse; font-size:11px; margin-top:4px; }
.rank-table th {
    color:#64748b; font-size:9px; text-transform:uppercase;
    padding:3px 6px; border-bottom:1px solid #1f2937; text-align:left;
}
.rank-table td { color:#e2e8f0; padding:3px 6px; border-bottom:1px solid #1f293720; }
.rank-table tr:last-child td { border-bottom:none; }

/* ══ 記帳：大按鈕 ══ */
.sec-lbl {
    font-size:9px; color:#64748b; font-weight:700;
    text-transform:uppercase; letter-spacing:.7px; margin:5px 0 3px;
}

/* ══ 換算預覽 ══ */
.twd-preview {
    background:#0c1f38; border-left:3px solid #2563eb;
    border-radius:5px; padding:6px 10px; margin:5px 0;
    color:#93c5fd; font-size:11px;
}

/* ══ 表格 ══ */
.stDataFrame { font-size:11px !important; }

/* ══ Divider ══ */
hr { border-color:#1f2937 !important; margin:5px 0 !important; }

/* ══ input/label ══ */
.stSelectbox label, .stDateInput label,
.stNumberInput label, .stTextInput label,
.stFileUploader label {
    font-size:9px !important; color:#64748b !important;
    font-weight:700 !important; text-transform:uppercase; letter-spacing:.4px;
}

/* ══ 月份下拉縮小 ══ */
.stSelectbox > div > div { padding-top:3px !important; padding-bottom:3px !important; }

/* ══ button 縮小 ══ */
div[data-testid="column"] > div > div > div > button {
    padding:5px 3px !important; font-size:12px !important;
    border-radius:7px !important;
}

/* ══ Sidebar ══ */
[data-testid="stSidebar"] {
    background:#080b12 !important; border-right:1px solid #1f2937;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
#  資料讀取
# ══════════════════════════════════════════
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        if df.empty:
            return pd.DataFrame()
        df['日期'] = pd.to_datetime(df['日期']).dt.date

        def to_twd(row):
            try:
                amt = float(row['金額'])
                cur = str(row['幣別']).upper()
                return round(amt * VND_RATE) if any(x in cur for x in ['VND','越南']) else round(amt)
            except:
                return 0

        df['台幣金額'] = df.apply(to_twd, axis=1)
        df['金額']    = df['金額'].astype(float).round(0)
        df['年月']    = pd.to_datetime(df['日期']).dt.to_period('M').astype(str)
        return df
    except Exception as e:
        st.error(f"❌ 讀取失敗：{e}")
        return pd.DataFrame()

# ══════════════════════════════════════════
#  圖表通用設定（極度精簡 margin）
# ══════════════════════════════════════════
CL = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#94a3b8', size=9),
    title_font=dict(color='#e2e8f0', size=10),
    margin=dict(l=4, r=4, t=22, b=4),
)

# ══════════════════════════════════════════
#  Header
# ══════════════════════════════════════════
st.markdown(f"""
<div class="hdr">
  <span style="font-size:18px;">💹</span>
  <span class="hdr-title">流水帳統計中心</span>
  <span class="hdr-ver">{APP_VERSION}</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
#  Sidebar
# ══════════════════════════════════════════
with st.sidebar:
    st.markdown("#### ⚙️ 控制面板")
    if st.button("🔄 刷新數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    st.divider()
    st.markdown(f'<div style="font-size:10px;color:#334155;text-align:center;">{APP_VERSION} © 2026</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════
#  載入資料
# ══════════════════════════════════════════
df = load_data()
if df.empty:
    st.info("👋 尚無資料，或試算表未開放存取。")
    st.stop()

# ══════════════════════════════════════════
#  分頁
# ══════════════════════════════════════════
t1, t2, t3, t4 = st.tabs(["🗓️ 當月", "📉 全期", "📋 清單", "✏️ 記帳"])

# ─────────────────────────────────────────
#  當月統計（設計目標：手機一頁不滑動）
# ─────────────────────────────────────────
with t1:
    today      = date.today()
    cur_ym     = today.strftime('%Y-%m')
    all_months = sorted(df['年月'].unique(), reverse=True)

    sel    = st.selectbox("月份", all_months, index=0,
                           key="t1_month", label_visibility="collapsed")
    dfm    = df[df['年月'] == sel].copy()
    is_cur = (sel == cur_ym)
    dim    = pd.Period(sel).days_in_month
    t_day  = today.day if is_cur else dim
    pct    = round(t_day / dim * 100)
    lbl    = pd.Period(sel).strftime('%Y/%m')
    prog   = f"第 {t_day}/{dim} 天（{pct}%）" if is_cur else "完整月份"

    # Banner（一行式，極精簡）
    st.markdown(f"""
    <div class="m-banner">
      <h3>📅 {lbl} &nbsp;|&nbsp; {prog}</h3>
    </div>""", unsafe_allow_html=True)

    if dfm.empty:
        st.warning("這個月還沒有記錄。")
    else:
        co_mask = dfm['類別'].str.contains('|'.join(CO_KEYS), na=False)
        total   = dfm['台幣金額'].sum()
        co_sum  = dfm[co_mask]['台幣金額'].sum()
        me_sum  = total - co_sum
        d_avg   = round(me_sum / t_day) if t_day else 0

        # ── 4格數字卡（自訂 HTML，不用 st.metric 避免過高）──
        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-card">
            <div class="stat-lbl">💰 總支出</div>
            <div class="stat-val">{total:,.0f}</div>
          </div>
          <div class="stat-card">
            <div class="stat-lbl">🚩 公司代墊</div>
            <div class="stat-val">{co_sum:,.0f}</div>
          </div>
          <div class="stat-card">
            <div class="stat-lbl">👤 個人實支</div>
            <div class="stat-val">{me_sum:,.0f}</div>
          </div>
          <div class="stat-card">
            <div class="stat-lbl">📆 日均</div>
            <div class="stat-val">{d_avg:,.0f}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 預估條
        if is_cur and t_day >= 3:
            est = round(me_sum / t_day * dim)
            st.markdown(f"""
            <div class="est-bar">
              📈 本月預估：<strong>TWD {est:,.0f}</strong>
              <span style="color:#475569;font-weight:400;margin-left:4px;">（日均 {d_avg:,.0f} 推算）</span>
            </div>""", unsafe_allow_html=True)
        elif is_cur:
            st.markdown('<div class="est-bar" style="color:#334155;border-color:#1f2937;">📈 累積 3 天後顯示預估</div>', unsafe_allow_html=True)

        # ── 圓餅 + 長條（並排，壓縮高度）──
        pie_df = dfm.groupby('類別')['台幣金額'].sum().reset_index()
        dfm['日'] = pd.to_datetime(dfm['日期']).dt.day
        bar_df = dfm.groupby('日')['台幣金額'].sum().reset_index()

        pc, bc = st.columns(2)
        with pc:
            fig_p = px.pie(pie_df, values='台幣金額', names='類別',
                           hole=0.5, title="類別佔比",
                           color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_p.update_traces(textinfo='percent+label', textfont_size=9, textfont_color='white')
            fig_p.update_layout(**CL, showlegend=False, height=170)
            st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})

        with bc:
            fig_b = px.bar(bar_df, x='日', y='台幣金額', title="每日走勢",
                           color_discrete_sequence=['#2563eb'])
            fig_b.update_layout(**CL, height=170,
                xaxis=dict(title='', gridcolor='#1f2937', tickfont=dict(size=8)),
                yaxis=dict(title='', gridcolor='#1f2937', tickfont=dict(size=8)))
            st.plotly_chart(fig_b, use_container_width=True, config={'displayModeBar': False})

        # ── 排行榜（HTML table 更精簡）──
        rk = pie_df.sort_values('台幣金額', ascending=False).reset_index(drop=True)
        rk['佔比'] = (rk['台幣金額'] / rk['台幣金額'].sum() * 100).round(1)

        rows_html = ''.join([
            f"<tr><td>{r['類別']}</td><td style='text-align:right'>{r['台幣金額']:,.0f}</td>"
            f"<td style='text-align:right;color:#60a5fa'>{r['佔比']}%</td></tr>"
            for _, r in rk.iterrows()
        ])
        st.markdown(f"""
        <table class="rank-table">
          <tr><th>類別</th><th style='text-align:right'>金額 TWD</th><th style='text-align:right'>佔比</th></tr>
          {rows_html}
        </table>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  全期分析
# ─────────────────────────────────────────
with t2:
    co_all  = df['類別'].str.contains('|'.join(CO_KEYS), na=False)
    tot_all = df['台幣金額'].sum()
    co_s    = df[co_all]['台幣金額'].sum()
    me_s    = tot_all - co_s

    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-card" style="grid-column:span 1">
        <div class="stat-lbl">💰 累計總支出</div>
        <div class="stat-val">{tot_all:,.0f}</div>
      </div>
      <div class="stat-card" style="grid-column:span 1">
        <div class="stat-lbl">🚩 公司代墊</div>
        <div class="stat-val">{co_s:,.0f}</div>
      </div>
      <div class="stat-card" style="grid-column:span 2">
        <div class="stat-lbl">👤 個人累計實支</div>
        <div class="stat-val">{me_s:,.0f}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    pie_all = df.groupby('類別')['台幣金額'].sum().reset_index()
    p1, p2  = st.columns([3,2])
    with p1:
        fg = px.pie(pie_all, values='台幣金額', names='類別',
                    hole=0.5, title="全期佔比",
                    color_discrete_sequence=px.colors.qualitative.Pastel)
        fg.update_traces(textinfo='percent+label', textfont_size=9, textfont_color='white')
        fg.update_layout(**CL, showlegend=False, height=210)
        st.plotly_chart(fg, use_container_width=True, config={'displayModeBar': False})
    with p2:
        rk2 = pie_all.sort_values('台幣金額', ascending=False).copy()
        rows2 = ''.join([
            f"<tr><td>{r['類別']}</td><td style='text-align:right'>{r['台幣金額']:,.0f}</td></tr>"
            for _, r in rk2.iterrows()
        ])
        st.markdown(f"""
        <table class="rank-table">
          <tr><th>類別</th><th style='text-align:right'>TWD</th></tr>
          {rows2}
        </table>""", unsafe_allow_html=True)

    st.divider()
    trend = df.groupby('年月')['台幣金額'].sum().reset_index().sort_values('年月')
    ft = px.line(trend, x='年月', y='台幣金額', title="月消費趨勢",
                 markers=True, color_discrete_sequence=['#3b82f6'])
    ft.update_layout(**CL, height=170,
        xaxis=dict(title='', gridcolor='#1f2937', tickfont=dict(size=8)),
        yaxis=dict(title='', gridcolor='#1f2937', tickfont=dict(size=8)))
    st.plotly_chart(ft, use_container_width=True, config={'displayModeBar': False})

# ─────────────────────────────────────────
#  流水帳清單
# ─────────────────────────────────────────
with t3:
    opts    = ['全部'] + sorted(df['年月'].unique().tolist(), reverse=True)
    flt     = st.selectbox("月份", opts, key="t3_month", label_visibility="collapsed")
    df_show = df.copy() if flt == '全部' else df[df['年月'] == flt].copy()

    if '收據照片' in df_show.columns:
        df_show['📎'] = df_show['收據照片'].apply(lambda x: '🔗' if pd.notnull(x) else '')

    cols = [c for c in df_show.columns if c not in ['時間戳記','resourcekey','收據照片','年月']]
    st.dataframe(
        df_show[cols].sort_index(ascending=False).style.format(
            {"金額":"{:,.0f}", "台幣金額":"{:,.0f}"}),
        use_container_width=True, height=400)
    st.caption(f"共 {len(df_show)} 筆")

# ─────────────────────────────────────────
#  新增記帳
# ─────────────────────────────────────────
with t4:

    # CSS：讓 radio 變成橫向 pill 按鈕
    st.markdown("""
    <style>
    /* radio 橫向排列 */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 5px !important;
    }
    div[data-testid="stRadio"] > div > label {
        background: #1f2937 !important;
        border: 1px solid #374151 !important;
        border-radius: 7px !important;
        padding: 5px 10px !important;
        color: #e2e8f0 !important;
        font-size: 12px !important;
        cursor: pointer !important;
        margin: 0 !important;
        flex: 0 0 auto !important;
    }
    div[data-testid="stRadio"] > div > label *,
    div[data-testid="stRadio"] label * {
        color: #e2e8f0 !important;
        font-size: 12px !important;
        background: transparent !important;
    }
    div[data-testid="stRadio"] > div > label:has(input:checked),
    div[data-testid="stRadio"] > div > label:has(input:checked) * {
        background: #1d4ed8 !important;
        border-color: #3b82f6 !important;
        color: #fff !important;
        font-weight: 600 !important;
    }
    div[data-testid="stRadio"] > div > label > div:first-child {
        display: none !important;
    }
    /* radio 隱藏原始圓點 */
    div[data-testid="stRadio"] input[type="radio"] {
        display: none !important;
    }
    /* 類別 radio 小一點，4欄感覺 */
    .cat-radio div[data-testid="stRadio"] > div > label {
        min-width: calc(25% - 4px);
        text-align: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="color:#60a5fa;font-size:13px;font-weight:700;margin-bottom:6px;">✏️ 新增記帳</div>', unsafe_allow_html=True)

    # ── 日期 + 金額 並排 ──
    col_d, col_a = st.columns(2)
    with col_d:
        inp_date = st.date_input("📅 日期", value=date.today())
    with col_a:
        inp_amt = st.number_input("💵 金額 *", min_value=0.0, value=0.0, step=1.0, format="%.0f")

    # ── 項目名稱 ──
    inp_name = st.text_input("📝 項目名稱（簡述用途）")

    st.divider()

    # ── 類別（radio 橫向 pill） ──
    st.markdown('<div class="sec-lbl">🏷️ 類別</div>', unsafe_allow_html=True)
    ex_cats  = sorted(df['類別'].dropna().unique().tolist()) if '類別' in df.columns else []
    all_cats = list(dict.fromkeys(ex_cats + CATEGORIES))

    st.markdown('<div class="cat-radio">', unsafe_allow_html=True)
    cat_sel = st.radio("類別", ["（未選）"] + all_cats,
                        key="cat_radio", label_visibility="collapsed",
                        horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)
    inp_cat = "" if cat_sel == "（未選）" else cat_sel

    st.divider()

    # ── 幣別 ──
    st.markdown('<div class="sec-lbl">💱 幣別</div>', unsafe_allow_html=True)
    inp_cur = st.radio("幣別", CURRENCIES,
                        index=0, key="cur_radio",
                        label_visibility="collapsed", horizontal=True)

    st.divider()

    # ── 支付方式 ──
    st.markdown('<div class="sec-lbl">💳 支付方式</div>', unsafe_allow_html=True)
    inp_pay = st.radio("支付方式", ["（未選）"] + PAYMENTS,
                        key="pay_radio",
                        label_visibility="collapsed", horizontal=True)

    st.divider()

    # ── 備註 + 附件 ──
    col_n, col_f = st.columns(2)
    with col_n:
        inp_note = st.text_input("💬 備註（可選）")
    with col_f:
        inp_file = st.file_uploader("📎 附件（收據照片）", type=['jpg','jpeg','png','pdf'])

    # ── 換算預覽 ──
    if inp_amt > 0:
        twd = round(inp_amt * VND_RATE) if 'VND' in inp_cur else round(inp_amt)
        st.markdown(f"""
        <div class="twd-preview">
          💱 換算台幣：<strong style="color:#f1f5f9;font-size:16px;">{twd:,.0f}</strong> TWD
        </div>""", unsafe_allow_html=True)
    else:
        twd = 0

    # ── 提交 / 清除 ──
    sb, cb = st.columns([2, 1])
    with sb:
        submitted = st.button("✅ 提交", type="primary", use_container_width=True)
    with cb:
        cleared = st.button("🗑️ 清除", use_container_width=True)

    if cleared:
        st.rerun()

    if submitted:
        errs = []
        if inp_amt <= 0: errs.append("請輸入金額")
        if not inp_cat:  errs.append("請選擇類別")
        if errs:
            for e in errs: st.error(f"❌ {e}")
        else:
            # 幣別格式對應（與 Google Form 一致）
            cur_map = {'TWD': 'TWD (新台幣)', 'VND': 'VND (越南盾)', 'USD': 'USD (美元)'}
            payload = {
                "timestamp": datetime.now().strftime('%Y/%-m/%-d %p %I:%M:%S').replace('AM','上午').replace('PM','下午'),
                "date":      str(inp_date),
                "category":  inp_cat,
                "item":      inp_name or "",
                "amount":    inp_amt,
                "currency":  cur_map.get(inp_cur, inp_cur),
                "payment":   inp_pay if inp_pay != "（未選）" else "",
                "note":      inp_note or "",
            }
            try:
                res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
                result = res.json()
                if result.get("status") == "ok":
                    st.success("✅ 已成功寫入 Google Sheets！")
                    st.table(pd.DataFrame([{
                        "日期": str(inp_date),
                        "類別": inp_cat,
                        "項目": inp_name or "－",
                        "金額": f"{inp_amt:,.0f}",
                        "幣別": inp_cur,
                        "支付": inp_pay if inp_pay != "（未選）" else "未填",
                        "備註": inp_note or "－",
                        "台幣": f"{twd:,.0f}",
                    }]))
                    st.cache_data.clear()  # 清快取，下次讀取可看到新資料
                else:
                    st.error(f"❌ 寫入失敗：{result.get('msg','未知錯誤')}")
            except Exception as ex:
                st.error(f"❌ 連線錯誤：{ex}")
