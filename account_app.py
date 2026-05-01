import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# ==========================================
# 版本資訊
# ==========================================
APP_VERSION = "v2.1.0"
APP_NAME = "流水帳統計中心"

# ==========================================
# 1. 核心設定
# ==========================================
SHEET_ID = "1lOCs8X7fzhApCoKBIp35OogqbF2Y-VVVCF3hS19q6d4"
GID = "259728202"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

VND_RATE = 0.00128
COMPANY_KEYWORDS = ['代墊', '公司', '固定']

# ==========================================
# 2. 頁面設定 & CSS
# ==========================================
st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    layout="wide",
    page_icon="💹",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* ---- 全域 ---- */
    html, body, [class*="css"] { font-size: 14px; }
    .main { background-color: #0a0d14; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }

    /* ---- 標題區塊 ---- */
    .app-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 20px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 12px;
        border: 1px solid #1e40af44;
        margin-bottom: 14px;
    }
    .app-header .app-icon { font-size: 28px; line-height: 1; }
    .app-header .app-title {
        font-size: 20px;
        font-weight: 700;
        color: #e2e8f0;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .app-header .app-version {
        font-size: 11px;
        color: #60a5fa;
        background: #1e3a5f;
        border: 1px solid #2563eb55;
        border-radius: 20px;
        padding: 2px 8px;
        margin-left: 4px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    /* ---- Metric 卡片 ---- */
    [data-testid="stMetric"] {
        background-color: #111827 !important;
        padding: 14px 16px !important;
        border-radius: 10px !important;
        border: 1px solid #1f2937 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 12px !important;
        font-weight: 500 !important;
        opacity: 1 !important;
    }
    [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricDelta"] { font-size: 12px !important; }

    /* ---- 分頁 ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #0f172a;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748b;
        font-size: 13px;
        font-weight: 500;
        padding: 6px 14px;
        border-radius: 6px;
    }
    .stTabs [aria-selected="true"] {
        color: #f1f5f9 !important;
        font-weight: 700;
        background: #1e293b !important;
    }

    /* ---- 月份標題 ---- */
    .month-header {
        background: linear-gradient(135deg, #0f2044, #0d1a30);
        border: 1px solid #1d4ed855;
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 14px;
        text-align: center;
    }
    .month-header h3 {
        color: #60a5fa;
        font-size: 18px;
        margin: 0 0 4px 0;
        font-weight: 700;
    }
    .month-header p {
        color: #64748b;
        margin: 0;
        font-size: 12px;
    }

    /* ---- 預估橫條 ---- */
    .estimate-bar {
        background: linear-gradient(90deg, #0c2340, #0f3460);
        border: 1px solid #1d4ed855;
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 10px 16px;
        margin: 10px 0;
        color: #93c5fd;
        font-size: 13px;
        font-weight: 600;
    }

    /* ---- 側邊欄 ---- */
    [data-testid="stSidebar"] {
        background-color: #080b12 !important;
        border-right: 1px solid #1f2937;
    }
    .sidebar-version {
        position: fixed;
        bottom: 16px;
        font-size: 10px;
        color: #334155;
        text-align: center;
        width: 100%;
        letter-spacing: 0.5px;
    }

    /* ---- 輸入表單 ---- */
    .form-section {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 14px;
    }
    .form-section h4 {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
        margin: 0 0 12px 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ---- 小字說明 ---- */
    .hint { color: #475569; font-size: 11px; margin-top: 2px; }

    /* ---- 表格 ---- */
    .stDataFrame { font-size: 13px !important; }

    /* ---- 選擇框 ---- */
    .stSelectbox label { font-size: 12px !important; color: #94a3b8 !important; }

    /* ---- Divider ---- */
    hr { border-color: #1f2937 !important; margin: 12px 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. 數據讀取
# ==========================================
@st.cache_data(ttl=300)
def load_and_fix_data():
    try:
        df = pd.read_csv(CSV_URL)
        if df.empty:
            return pd.DataFrame()

        df['日期'] = pd.to_datetime(df['日期']).dt.date

        def smart_convert(row):
            try:
                amt = float(row['金額'])
                cur = str(row['幣別']).upper()
                if any(x in cur for x in ['VND', '越南']):
                    return round(amt * VND_RATE)
                return round(amt)
            except Exception:
                return 0

        df['台幣金額'] = df.apply(smart_convert, axis=1)
        df['金額'] = df['金額'].astype(float).round(0)
        df['年月'] = pd.to_datetime(df['日期']).dt.to_period('M').astype(str)
        return df

    except Exception as e:
        st.error(f"❌ 數據讀取失敗：{e}")
        return pd.DataFrame()

# ==========================================
# 4. 通用圖表設定
# ==========================================
CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#94a3b8', size=11),
    title_font=dict(color='#e2e8f0', size=13),
    margin=dict(l=10, r=10, t=36, b=10),
)

# ==========================================
# 5. App 標題
# ==========================================
st.markdown(f"""
<div class="app-header">
  <div class="app-icon">💹</div>
  <div>
    <span class="app-title">{APP_NAME}</span>
    <span class="app-version">{APP_VERSION}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 6. 側邊欄
# ==========================================
with st.sidebar:
    st.markdown("#### ⚙️ 控制面板")

    if st.button("🔄 強制刷新數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"🕐 上次更新：{datetime.now().strftime('%H:%M:%S')}")
    st.divider()

    st.markdown(f"""
    <div style="font-size:10px; color:#334155; text-align:center; padding-top:8px;">
        {APP_NAME}<br>{APP_VERSION}<br>
        <span style="color:#1e3a5f;">© 2026</span>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 7. 讀取數據
# ==========================================
df = load_and_fix_data()

if df.empty:
    st.info("👋 目前還沒有數據，或是連線發生問題。請確認試算表是否開放存取。")
    st.stop()

# ==========================================
# 8. 分頁架構
# ==========================================
tab_current, tab_all, tab_list, tab_input = st.tabs([
    "🗓️ 當月統計",
    "📉 全期分析",
    "📋 流水帳清單",
    "✏️ 新增記帳"
])

# ------------------------------------------
# 分頁一：當月統計
# ------------------------------------------
with tab_current:
    today = date.today()
    current_ym = today.strftime('%Y-%m')

    all_months = sorted(df['年月'].unique(), reverse=True)
    selected_month = st.selectbox("📅 選擇月份", all_months, index=0, key="month_selector")

    df_month = df[df['年月'] == selected_month].copy()
    is_current = (selected_month == current_ym)

    month_label = pd.Period(selected_month).strftime('%Y 年 %m 月')
    days_in_month = pd.Period(selected_month).days_in_month
    today_day = today.day if is_current else days_in_month
    progress_pct = round(today_day / days_in_month * 100)

    progress_text = (
        f"本月進度：第 {today_day} 天 / 共 {days_in_month} 天（{progress_pct}%）"
        if is_current else "完整月份數據"
    )

    st.markdown(f"""
    <div class="month-header">
        <h3>📅 {month_label} 消費統計</h3>
        <p>{progress_text}</p>
    </div>
    """, unsafe_allow_html=True)

    if df_month.empty:
        st.warning("這個月還沒有任何記錄。")
    else:
        total_month = df_month['台幣金額'].sum()
        co_mask = df_month['類別'].str.contains('|'.join(COMPANY_KEYWORDS), na=False)
        co_sum = df_month[co_mask]['台幣金額'].sum()
        me_sum = total_month - co_sum
        daily_avg = round(me_sum / today_day) if today_day > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 當月總支出 (TWD)", f"{total_month:,.0f}")
        col2.metric("🚩 公司代墊", f"{co_sum:,.0f}")
        col3.metric("👤 個人實支", f"{me_sum:,.0f}")
        col4.metric("📆 日均消費", f"{daily_avg:,.0f}")

        if is_current and today_day > 0:
            estimated_total = round(me_sum / today_day * days_in_month)
            st.markdown(f"""
            <div class="estimate-bar">
                📈 本月預估個人支出：TWD {estimated_total:,.0f}
                <span style="font-weight:400; color:#475569; font-size:11px; margin-left:8px;">依目前日均推算</span>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        col_pie, col_bar = st.columns([1, 1])

        with col_pie:
            pie_data = df_month.groupby('類別')['台幣金額'].sum().reset_index()
            fig_pie = px.pie(
                pie_data, values='台幣金額', names='類別',
                hole=0.55, title="類別佔比",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(
                textinfo='percent+label',
                textfont_size=11,
                textfont_color="white"
            )
            fig_pie.update_layout(**CHART_LAYOUT, showlegend=False, height=260)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_bar:
            df_month['日'] = pd.to_datetime(df_month['日期']).dt.day
            daily_data = df_month.groupby('日')['台幣金額'].sum().reset_index()

            fig_bar = px.bar(
                daily_data, x='日', y='台幣金額',
                title="每日消費走勢",
                color_discrete_sequence=['#2563eb']
            )
            fig_bar.update_layout(
                **CHART_LAYOUT,
                height=260,
                xaxis=dict(title="日", gridcolor='#1f2937', tickfont=dict(size=10)),
                yaxis=dict(title="TWD", gridcolor='#1f2937', tickfont=dict(size=10))
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("類別支出排行")
        rank = pie_data.sort_values('台幣金額', ascending=False).reset_index(drop=True)
        rank.index += 1
        rank['金額 (TWD)'] = rank['台幣金額'].map('{:,.0f}'.format)
        rank['佔比'] = (rank['台幣金額'] / rank['台幣金額'].sum() * 100).round(1).astype(str) + '%'
        st.table(rank[['類別', '金額 (TWD)', '佔比']])

# ------------------------------------------
# 分頁二：全期分析
# ------------------------------------------
with tab_all:
    total_spent = df['台幣金額'].sum()
    co_mask_all = df['類別'].str.contains('|'.join(COMPANY_KEYWORDS), na=False)
    co_sum_all = df[co_mask_all]['台幣金額'].sum()
    me_sum_all = total_spent - co_sum_all

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 累計總支出 (TWD)", f"{total_spent:,.0f}")
    col2.metric("🚩 公司代墊", f"{co_sum_all:,.0f}")
    col3.metric("👤 個人累計實支", f"{me_sum_all:,.0f}")

    st.divider()

    c1, c2 = st.columns([3, 2])
    with c1:
        pie_data_all = df.groupby('類別')['台幣金額'].sum().reset_index()
        fig = px.pie(
            pie_data_all, values='台幣金額', names='類別',
            hole=0.5, title="各項消費佔比（全期）",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo='percent+label', textfont_size=11, textfont_color="white")
        fig.update_layout(**CHART_LAYOUT, showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**支出排行榜**")
        rank_all = pie_data_all.sort_values(by='台幣金額', ascending=False)
        rank_all['金額'] = rank_all['台幣金額'].map('{:,.0f}'.format)
        st.table(rank_all[['類別', '金額']])

    # 月趨勢圖
    st.divider()
    monthly_trend = df.groupby('年月')['台幣金額'].sum().reset_index().sort_values('年月')
    fig_trend = px.line(
        monthly_trend, x='年月', y='台幣金額',
        title="月消費趨勢",
        markers=True,
        color_discrete_sequence=['#3b82f6']
    )
    fig_trend.update_layout(
        **CHART_LAYOUT,
        height=220,
        xaxis=dict(title="", gridcolor='#1f2937', tickfont=dict(size=10)),
        yaxis=dict(title="TWD", gridcolor='#1f2937', tickfont=dict(size=10))
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# ------------------------------------------
# 分頁三：流水帳清單
# ------------------------------------------
with tab_list:
    all_months_list = ['全部'] + sorted(df['年月'].unique().tolist(), reverse=True)
    filter_month = st.selectbox("📅 篩選月份", all_months_list, key="list_month")

    df_show = df.copy() if filter_month == '全部' else df[df['年月'] == filter_month].copy()

    if '收據照片' in df_show.columns:
        df_show['照片附件'] = df_show['收據照片'].apply(
            lambda x: "🔗 查看" if pd.notnull(x) else ""
        )

    clean_cols = [c for c in df_show.columns if c not in ['時間戳記', 'resourcekey', '收據照片', '年月']]

    st.dataframe(
        df_show[clean_cols].sort_index(ascending=False).style.format({
            "金額": "{:,.0f}",
            "台幣金額": "{:,.0f}"
        }),
        use_container_width=True,
        height=420
    )
    st.caption(f"共 {len(df_show)} 筆記錄")

# ------------------------------------------
# 分頁四：新增記帳
# ------------------------------------------
with tab_input:
    st.markdown("""
    <div style="background:#0f172a; border:1px solid #1e3a5f; border-radius:10px;
                padding:14px 18px; margin-bottom:14px;">
        <div style="color:#60a5fa; font-size:13px; font-weight:700; margin-bottom:4px;">
            ✏️ 手動新增記帳
        </div>
        <div style="color:#475569; font-size:11px;">
            填寫後點選送出，資料將寫入 Google 試算表
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 取得類別選項（從現有資料抓）
    existing_cats = sorted(df['類別'].dropna().unique().tolist()) if '類別' in df.columns else []
    existing_currency = sorted(df['幣別'].dropna().unique().tolist()) if '幣別' in df.columns else ['TWD', 'VND']

    col_a, col_b = st.columns(2)

    with col_a:
        input_date = st.date_input("📅 日期", value=date.today())
        input_amount = st.number_input("💵 金額", min_value=0.0, value=0.0, step=1.0, format="%.0f")
        input_currency = st.selectbox("💱 幣別", options=existing_currency if existing_currency else ['TWD', 'VND'])

    with col_b:
        if existing_cats:
            input_cat = st.selectbox("🏷️ 類別", options=existing_cats)
        else:
            input_cat = st.text_input("🏷️ 類別")

        input_note = st.text_input("📝 備註（選填）")
        input_store = st.text_input("🏪 地點／商店（選填）")

    st.divider()

    # 試算顯示
    if input_amount > 0:
        cur_upper = str(input_currency).upper()
        if any(x in cur_upper for x in ['VND', '越南']):
            twd_preview = round(input_amount * VND_RATE)
        else:
            twd_preview = round(input_amount)

        st.markdown(f"""
        <div style="background:#0c2340; border-left:3px solid #2563eb; border-radius:6px;
                    padding:10px 14px; margin-bottom:12px; font-size:13px; color:#93c5fd;">
            💱 換算台幣：<strong style="color:#f1f5f9; font-size:16px;">{twd_preview:,.0f} TWD</strong>
        </div>
        """, unsafe_allow_html=True)

    col_btn, col_hint = st.columns([1, 3])
    with col_btn:
        submitted = st.button("✅ 送出記帳", type="primary", use_container_width=True)

    if submitted:
        if input_amount <= 0:
            st.error("❌ 請輸入金額")
        elif not input_cat:
            st.error("❌ 請選擇類別")
        else:
            # 組合 Google 表單 URL（依你的表單欄位調整）
            FORM_BASE = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

            # 顯示待寫入的資料預覽
            preview_data = {
                "日期": str(input_date),
                "金額": f"{input_amount:,.0f}",
                "幣別": input_currency,
                "類別": input_cat,
                "備註": input_note or "－",
                "地點": input_store or "－",
                "台幣金額": f"{twd_preview:,.0f}" if input_amount > 0 else "0",
            }

            st.success("✅ 資料已準備完成！")
            st.markdown("**📋 本次記帳內容：**")

            preview_df = pd.DataFrame([preview_data])
            st.table(preview_df)

            st.info("""
            ⚠️ **直接寫入功能說明**

            目前 Streamlit Cloud 為公開部署，直接寫入 Google Sheets 需要 Service Account 憑證。
            請告知是否要設定自動寫入，或繼續使用 Google 表單填寫。
            """)

            st.cache_data.clear()
