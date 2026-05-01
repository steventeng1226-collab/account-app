import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# ══════════════════════════════════════════
#  設定
# ══════════════════════════════════════════
APP_VERSION  = "v3.0.0"
SHEET_ID     = "1lOCs8X7fzhApCoKBIp35OogqbF2Y-VVVCF3hS19q6d4"
GID          = "259728202"
CSV_URL      = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
VND_RATE     = 0.00128
CO_KEYS      = ['代墊', '公司', '固定']

CATEGORIES   = ['食', '住', '行', '育', '樂', '醫療', '代墊', '固定', '其他']
CURRENCIES   = ['TWD', 'VND', 'USD']
PAYMENTS     = ['現金', '信用卡', '簽帳卡', '銀行轉帳', '電子錢包', '其他']

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
/* ── 隱藏 Streamlit 原生 UI ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.viewerBadge_container__1QSob { display:none !important; }

/* ── 全域 ── */
html, body, [class*="css"] { font-size:13px; }
.main  { background:#080c14; }
.block-container { padding:0.5rem 0.8rem 1rem !important; max-width:820px; }

/* ── 頂部 Header ── */
.hdr {
  display:flex; align-items:center; gap:8px;
  background:linear-gradient(135deg,#0f172a,#1a2540);
  border:1px solid #1e3a8a30; border-radius:10px;
  padding:8px 14px; margin-bottom:8px;
}
.hdr-title { font-size:15px; font-weight:700; color:#e2e8f0; white-space:nowrap; }
.hdr-ver   { font-size:10px; color:#60a5fa; background:#1e3a5f;
              border:1px solid #2563eb44; border-radius:20px;
              padding:1px 8px; font-weight:600; }

/* ── 分頁 ── */
.stTabs [data-baseweb="tab-list"] {
  gap:3px; background:#0f172a; border-radius:8px; padding:3px; margin-bottom:8px;
}
.stTabs [data-baseweb="tab"] {
  color:#64748b; font-size:12px; font-weight:500;
  padding:5px 10px; border-radius:6px; white-space:nowrap;
}
.stTabs [aria-selected="true"] {
  color:#f1f5f9 !important; font-weight:700; background:#1e293b !important;
}

/* ── Metric 卡片 ── */
[data-testid="stMetric"] {
  background:#111827 !important; padding:9px 11px !important;
  border-radius:8px !important; border:1px solid #1f2937 !important;
}
[data-testid="stMetricLabel"] {
  color:#94a3b8 !important; font-size:10px !important;
  font-weight:500 !important; opacity:1 !important;
}
[data-testid="stMetricValue"] {
  color:#f1f5f9 !important; font-size:16px !important; font-weight:700 !important;
}

/* ── 月份標題 Banner ── */
.m-banner {
  background:linear-gradient(135deg,#0f2044,#0d1a30);
  border:1px solid #1d4ed840; border-radius:10px;
  padding:9px 14px; margin-bottom:8px; text-align:center;
}
.m-banner h3 { color:#60a5fa; font-size:14px; margin:0 0 2px; font-weight:700; }
.m-banner p  { color:#64748b; font-size:11px; margin:0; }

/* ── 預估條 ── */
.est-bar {
  background:#0c1f38; border-left:3px solid #3b82f6;
  border-radius:6px; padding:7px 12px; margin:6px 0;
  color:#93c5fd; font-size:12px; font-weight:600;
}

/* ── 大按鈕群組（記帳用） ── */
div[data-testid="column"] > div > div > div > button {
  border-radius:8px !important;
  font-size:13px !important;
  padding:8px 4px !important;
  width:100% !important;
}

/* ── Section label ── */
.sec-lbl {
  font-size:10px; color:#64748b; font-weight:700;
  text-transform:uppercase; letter-spacing:.8px; margin:8px 0 4px;
}

/* ── 換算預覽 ── */
.twd-preview {
  background:#0c1f38; border-left:3px solid #2563eb;
  border-radius:6px; padding:8px 12px; margin:8px 0;
  color:#93c5fd; font-size:12px;
}

/* ── 表格 ── */
.stDataFrame { font-size:12px !important; }

/* ── Divider ── */
hr { border-color:#1f2937 !important; margin:8px 0 !important; }

/* ── Selectbox / input label ── */
.stSelectbox label, .stDateInput label,
.stNumberInput label, .stTextInput label,
.stFileUploader label {
  font-size:10px !important; color:#64748b !important;
  font-weight:700 !important; text-transform:uppercase; letter-spacing:.5px;
}

/* ── Sidebar ── */
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
#  圖表通用設定
# ══════════════════════════════════════════
CL = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#94a3b8', size=10),
    title_font=dict(color='#e2e8f0', size=12),
    margin=dict(l=6, r=6, t=26, b=6),
)

# ══════════════════════════════════════════
#  Header
# ══════════════════════════════════════════
st.markdown(f"""
<div class="hdr">
  <span style="font-size:20px;">💹</span>
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
    st.markdown(f'<div style="font-size:10px;color:#334155;text-align:center;">流水帳統計中心 {APP_VERSION}<br>© 2026</div>', unsafe_allow_html=True)

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
#  當月統計
# ─────────────────────────────────────────
with t1:
    today      = date.today()
    cur_ym     = today.strftime('%Y-%m')
    all_months = sorted(df['年月'].unique(), reverse=True)

    sel = st.selectbox("月份", all_months, index=0,
                        key="t1_month", label_visibility="collapsed")
    dfm        = df[df['年月'] == sel].copy()
    is_cur     = (sel == cur_ym)
    dim        = pd.Period(sel).days_in_month
    t_day      = today.day if is_cur else dim
    pct        = round(t_day / dim * 100)
    lbl        = pd.Period(sel).strftime('%Y 年 %m 月')
    prog_txt   = f"本月進度：第 {t_day} 天 / {dim} 天（{pct}%）" if is_cur else "完整月份"

    st.markdown(f"""
    <div class="m-banner">
      <h3>📅 {lbl} 消費統計</h3>
      <p>{prog_txt}</p>
    </div>""", unsafe_allow_html=True)

    if dfm.empty:
        st.warning("這個月還沒有記錄。")
    else:
        co_mask  = dfm['類別'].str.contains('|'.join(CO_KEYS), na=False)
        total    = dfm['台幣金額'].sum()
        co_sum   = dfm[co_mask]['台幣金額'].sum()
        me_sum   = total - co_sum
        d_avg    = round(me_sum / t_day) if t_day else 0

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("💰 當月總支出", f"{total:,.0f}")
        c2.metric("🚩 公司代墊",   f"{co_sum:,.0f}")
        c3.metric("👤 個人實支",   f"{me_sum:,.0f}")
        c4.metric("📆 日均消費",   f"{d_avg:,.0f}")

        # 預估（≥3天才顯示）
        if is_cur and t_day >= 3:
            est = round(me_sum / t_day * dim)
            st.markdown(f"""
            <div class="est-bar">
              📈 本月預估個人支出：<strong>TWD {est:,.0f}</strong>
              <span style="font-size:10px;color:#475569;margin-left:6px;">依日均 {d_avg:,.0f} 推算</span>
            </div>""", unsafe_allow_html=True)
        elif is_cur:
            st.markdown('<div class="est-bar" style="color:#475569;border-color:#334155;">📈 累積 3 天後顯示預估（避免月初大額失真）</div>', unsafe_allow_html=True)

        st.divider()

        # 圓餅 + 長條
        pie_df = dfm.groupby('類別')['台幣金額'].sum().reset_index()
        dfm['日'] = pd.to_datetime(dfm['日期']).dt.day
        bar_df = dfm.groupby('日')['台幣金額'].sum().reset_index()

        pc, bc = st.columns(2)
        with pc:
            fig_p = px.pie(pie_df, values='台幣金額', names='類別',
                           hole=0.52, title="類別佔比",
                           color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_p.update_traces(textinfo='percent+label', textfont_size=10, textfont_color='white')
            fig_p.update_layout(**CL, showlegend=False, height=210)
            st.plotly_chart(fig_p, use_container_width=True)

        with bc:
            fig_b = px.bar(bar_df, x='日', y='台幣金額', title="每日走勢",
                           color_discrete_sequence=['#2563eb'])
            fig_b.update_layout(**CL, height=210,
                xaxis=dict(title='', gridcolor='#1f2937', tickfont=dict(size=9)),
                yaxis=dict(title='', gridcolor='#1f2937', tickfont=dict(size=9)))
            st.plotly_chart(fig_b, use_container_width=True)

        # 排行榜
        rk = pie_df.sort_values('台幣金額', ascending=False).reset_index(drop=True)
        rk.index += 1
        rk['金額']  = rk['台幣金額'].map('{:,.0f}'.format)
        rk['佔比']  = (rk['台幣金額'] / rk['台幣金額'].sum() * 100).round(1).astype(str) + '%'
        st.table(rk[['類別','金額','佔比']])

# ─────────────────────────────────────────
#  全期分析
# ─────────────────────────────────────────
with t2:
    co_all  = df['類別'].str.contains('|'.join(CO_KEYS), na=False)
    tot_all = df['台幣金額'].sum()
    co_s    = df[co_all]['台幣金額'].sum()
    me_s    = tot_all - co_s

    a,b,c = st.columns(3)
    a.metric("💰 累計總支出", f"{tot_all:,.0f}")
    b.metric("🚩 公司代墊",   f"{co_s:,.0f}")
    c.metric("👤 個人實支",   f"{me_s:,.0f}")

    st.divider()

    pie_all = df.groupby('類別')['台幣金額'].sum().reset_index()
    p1, p2  = st.columns([3,2])
    with p1:
        fg = px.pie(pie_all, values='台幣金額', names='類別',
                    hole=0.5, title="各項消費佔比（全期）",
                    color_discrete_sequence=px.colors.qualitative.Pastel)
        fg.update_traces(textinfo='percent+label', textfont_size=10, textfont_color='white')
        fg.update_layout(**CL, showlegend=False, height=240)
        st.plotly_chart(fg, use_container_width=True)
    with p2:
        rk2 = pie_all.sort_values('台幣金額', ascending=False).copy()
        rk2['金額'] = rk2['台幣金額'].map('{:,.0f}'.format)
        st.table(rk2[['類別','金額']])

    st.divider()
    trend = df.groupby('年月')['台幣金額'].sum().reset_index().sort_values('年月')
    ft = px.line(trend, x='年月', y='台幣金額', title="月消費趨勢",
                 markers=True, color_discrete_sequence=['#3b82f6'])
    ft.update_layout(**CL, height=190,
        xaxis=dict(title='', gridcolor='#1f2937', tickfont=dict(size=9)),
        yaxis=dict(title='', gridcolor='#1f2937', tickfont=dict(size=9)))
    st.plotly_chart(ft, use_container_width=True)

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
        use_container_width=True, height=420)
    st.caption(f"共 {len(df_show)} 筆")

# ─────────────────────────────────────────
#  新增記帳
# ─────────────────────────────────────────
with t4:

    # session state
    for k,v in [('cat',''), ('cur','TWD'), ('pay','')]:
        if k not in st.session_state:
            st.session_state[k] = v

    def sel_btn(key, val):
        st.session_state[key] = val
        st.rerun()

    st.markdown('<div style="color:#60a5fa;font-size:13px;font-weight:700;margin-bottom:8px;">✏️ 新增記帳</div>', unsafe_allow_html=True)

    # ── 日期 ──
    inp_date = st.date_input("📅 日期", value=date.today())

    st.divider()

    # ── 類別 ──
    st.markdown('<div class="sec-lbl">🏷️ 類別</div>', unsafe_allow_html=True)
    ex_cats  = sorted(df['類別'].dropna().unique().tolist()) if '類別' in df.columns else []
    all_cats = list(dict.fromkeys(ex_cats + CATEGORIES))
    rows_cat = [all_cats[i:i+4] for i in range(0, len(all_cats), 4)]
    for row in rows_cat:
        cols_c = st.columns(len(row))
        for i, cat in enumerate(row):
            with cols_c[i]:
                picked = st.session_state.cat == cat
                if st.button(cat, key=f"c_{cat}",
                             type="primary" if picked else "secondary",
                             use_container_width=True):
                    sel_btn('cat', cat)

    if st.session_state.cat:
        st.markdown(f'<div style="font-size:11px;color:#3b82f6;margin:2px 0 4px;">✓ {st.session_state.cat}</div>', unsafe_allow_html=True)

    st.divider()

    # ── 項目名稱 ──
    inp_name = st.text_input("📝 項目名稱（簡述用途）")

    # ── 金額 ──
    inp_amt  = st.number_input("💵 金額 *", min_value=0.0, value=0.0, step=1.0, format="%.0f")

    st.divider()

    # ── 幣別 ──
    st.markdown('<div class="sec-lbl">💱 幣別</div>', unsafe_allow_html=True)
    cur_cols = st.columns(len(CURRENCIES))
    for i, cur in enumerate(CURRENCIES):
        with cur_cols[i]:
            if st.button(cur, key=f"cur_{cur}",
                         type="primary" if st.session_state.cur == cur else "secondary",
                         use_container_width=True):
                sel_btn('cur', cur)

    st.divider()

    # ── 支付方式 ──
    st.markdown('<div class="sec-lbl">💳 支付方式</div>', unsafe_allow_html=True)
    rows_pay = [PAYMENTS[i:i+3] for i in range(0, len(PAYMENTS), 3)]
    for row in rows_pay:
        cols_p = st.columns(len(row))
        for i, pm in enumerate(row):
            with cols_p[i]:
                if st.button(pm, key=f"p_{pm}",
                             type="primary" if st.session_state.pay == pm else "secondary",
                             use_container_width=True):
                    sel_btn('pay', pm)

    if st.session_state.pay:
        st.markdown(f'<div style="font-size:11px;color:#3b82f6;margin:2px 0 4px;">✓ {st.session_state.pay}</div>', unsafe_allow_html=True)

    st.divider()

    # ── 備註 + 附件 ──
    inp_note = st.text_input("💬 備註（可選）")
    inp_file = st.file_uploader("📎 附件（收據照片，最大 10MB）",
                                 type=['jpg','jpeg','png','pdf'])

    st.divider()

    # ── 台幣換算預覽 ──
    if inp_amt > 0:
        twd = round(inp_amt * VND_RATE) if 'VND' in st.session_state.cur else round(inp_amt)
        st.markdown(f"""
        <div class="twd-preview">
          💱 換算台幣：<strong style="color:#f1f5f9;font-size:18px;">{twd:,.0f}</strong> TWD
        </div>""", unsafe_allow_html=True)
    else:
        twd = 0

    # ── 提交 / 清除 ──
    sb, cb = st.columns([2,1])
    with sb:
        submitted = st.button("✅ 提交", type="primary", use_container_width=True)
    with cb:
        if st.button("🗑️ 清除", use_container_width=True):
            st.session_state.cat = ''
            st.session_state.cur = 'TWD'
            st.session_state.pay = ''
            st.rerun()

    if submitted:
        errs = []
        if inp_amt <= 0:           errs.append("請輸入金額")
        if not st.session_state.cat: errs.append("請選擇類別")
        if errs:
            for e in errs: st.error(f"❌ {e}")
        else:
            st.success("✅ 資料準備完成！")
            st.table(pd.DataFrame([{
                "日期": str(inp_date),
                "類別": st.session_state.cat,
                "項目": inp_name or "－",
                "金額": f"{inp_amt:,.0f}",
                "幣別": st.session_state.cur,
                "支付": st.session_state.pay or "未填",
                "備註": inp_note or "－",
                "台幣": f"{twd:,.0f}",
                "附件": f"✅ {inp_file.name}" if inp_file else "無",
            }]))
            st.info("⚠️ 直接寫入 Google Sheets 需設定 Service Account，請告知是否要啟用。")
