import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# ==========================================
# 1. 核心設定
# ==========================================
SHEET_ID = "1lOCs8X7fzhApCoKBIp35OogqbF2Y-VVVCF3hS19q6d4"
GID = "259728202"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

VND_RATE = 0.00128
COMPANY_KEYWORDS = ['代墊', '公司', '固定']  # 集中管理關鍵字

# ==========================================
# 2. 頁面設定 & CSS
# ==========================================
st.set_page_config(page_title="流水帳統計中心", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }

    [data-testid="stMetric"] {
        background-color: #1a1c24 !important;
        padding: 25px !important;
        border-radius: 15px !important;
        border: 1px solid #3d444d !important;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.6) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 36px !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 16px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        font-weight: bold;
    }

    /* 當月統計頁面專用 */
    .month-header {
        background: linear-gradient(135deg, #1e3a5f, #0d2137);
        border: 1px solid #2563eb;
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 20px;
        text-align: center;
    }
    .month-header h2 {
        color: #60a5fa;
        font-size: 28px;
        margin: 0;
    }
    .month-header p {
        color: #94a3b8;
        margin: 4px 0 0 0;
        font-size: 14px;
    }
    .daily-item {
        background-color: #1a1c24;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 8px;
        color: #FFFFFF;
    }
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
# 4. 主程式
# ==========================================
st.title("📊 流水帳統計中心")

df = load_and_fix_data()

# 側邊欄
st.sidebar.markdown("### ⚙️ 控制面板")

if st.sidebar.button("🔄 強制刷新數據"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(f"🕐 上次更新：{datetime.now().strftime('%H:%M:%S')}")

if df.empty:
    st.info("👋 副理，目前還沒有數據，或是連線發生問題。請確認試算表是否開放存取。")
    st.stop()

# ==========================================
# 5. 分頁架構
# ==========================================
tab_current, tab_all, tab_list = st.tabs(["🗓️ 當月統計", "📉 全期分析", "📋 流水帳清單"])

# ------------------------------------------
# 分頁一：當月統計（新增）
# ------------------------------------------
with tab_current:
    today = date.today()
    current_ym = today.strftime('%Y-%m')

    # 月份切換器（預設當月）
    all_months = sorted(df['年月'].unique(), reverse=True)
    selected_month = st.selectbox(
        "📅 選擇月份",
        all_months,
        index=0,
        key="month_selector"
    )

    df_month = df[df['年月'] == selected_month].copy()
    is_current = (selected_month == current_ym)

    # 標題區塊
    month_label = pd.Period(selected_month).strftime('%Y 年 %m 月')
    days_in_month = pd.Period(selected_month).days_in_month
    today_day = today.day if is_current else days_in_month
    progress_pct = round(today_day / days_in_month * 100)

    st.markdown(f"""
    <div class="month-header">
        <h2>📅 {month_label} 消費統計</h2>
        <p>{'本月進度：第 ' + str(today_day) + ' 天 / 共 ' + str(days_in_month) + ' 天（' + str(progress_pct) + '%）' if is_current else '完整月份數據'}</p>
    </div>
    """, unsafe_allow_html=True)

    if df_month.empty:
        st.warning("這個月還沒有任何記錄。")
    else:
        # --- 頂部摘要卡片 ---
        total_month = df_month['台幣金額'].sum()
        co_mask = df_month['類別'].str.contains('|'.join(COMPANY_KEYWORDS), na=False)
        co_sum = df_month[co_mask]['台幣金額'].sum()
        me_sum = total_month - co_sum
        daily_avg = round(me_sum / today_day) if today_day > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 當月總支出 (TWD)", f"{total_month:,.0f}")
        col2.metric("🚩 公司代墊 (TWD)", f"{co_sum:,.0f}")
        col3.metric("👤 個人實支 (TWD)", f"{me_sum:,.0f}")
        col4.metric("📆 日均個人消費", f"{daily_avg:,.0f}",
                    help="個人實支 ÷ 已過天數")

        # 月底預估（只在當月顯示）
        if is_current and today_day > 0:
            estimated_total = round(me_sum / today_day * days_in_month)
            st.info(f"📈 **本月預估個人支出：TWD {estimated_total:,.0f}**（依目前日均消費推算）")

        st.divider()

        # --- 圖表區域 ---
        col_pie, col_bar = st.columns([1, 1])

        with col_pie:
            pie_data = df_month.groupby('類別')['台幣金額'].sum().reset_index()
            fig_pie = px.pie(
                pie_data, values='台幣金額', names='類別',
                hole=0.5, title="📊 類別佔比",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textinfo='percent+label', textfont_size=13, textfont_color="white")
            fig_pie.update_layout(
                showlegend=False,
                title_font_color="white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_bar:
            # 每日消費長條圖
            df_month['日'] = pd.to_datetime(df_month['日期']).dt.day
            daily_data = df_month.groupby('日')['台幣金額'].sum().reset_index()

            fig_bar = px.bar(
                daily_data, x='日', y='台幣金額',
                title="📅 每日消費走勢",
                color_discrete_sequence=['#3b82f6']
            )
            fig_bar.update_layout(
                xaxis_title="日期",
                yaxis_title="台幣金額",
                title_font_color="white",
                font_color="white",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#2d3748'),
                yaxis=dict(gridcolor='#2d3748')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- 類別排行榜 ---
        st.subheader("⚠️ 類別支出排行")
        rank = pie_data.sort_values('台幣金額', ascending=False).reset_index(drop=True)
        rank.index += 1
        rank['金額 (TWD)'] = rank['台幣金額'].map('{:,.0f}'.format)
        rank['佔比'] = (rank['台幣金額'] / rank['台幣金額'].sum() * 100).round(1).astype(str) + '%'
        st.table(rank[['類別', '金額 (TWD)', '佔比']])

# ------------------------------------------
# 分頁二：全期分析（原有）
# ------------------------------------------
with tab_all:
    total_spent = df['台幣金額'].sum()
    co_mask_all = df['類別'].str.contains('|'.join(COMPANY_KEYWORDS), na=False)
    co_sum_all = df[co_mask_all]['台幣金額'].sum()
    me_sum_all = total_spent - co_sum_all

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 累計總支出 (TWD)", f"{total_spent:,.0f}")
    col2.metric("🚩 公司代墊 (TWD)", f"{co_sum_all:,.0f}")
    col3.metric("👤 個人累計實支 (TWD)", f"{me_sum_all:,.0f}")

    st.divider()

    c1, c2 = st.columns([2, 1])
    with c1:
        pie_data_all = df.groupby('類別')['台幣金額'].sum().reset_index()
        fig = px.pie(
            pie_data_all, values='台幣金額', names='類別',
            hole=0.5, title="各項消費佔比分析（全期）",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo='percent+label', textfont_size=14, textfont_color="white")
        fig.update_layout(
            showlegend=False,
            title_font_color="white",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.write("### ⚠️ 支出排行榜")
        rank_all = pie_data_all.sort_values(by='台幣金額', ascending=False)
        rank_all['金額'] = rank_all['台幣金額'].map('{:,.0f}'.format)
        st.table(rank_all[['類別', '金額']])

# ------------------------------------------
# 分頁三：流水帳清單（原有）
# ------------------------------------------
with tab_list:
    # 月份篩選
    all_months_list = ['全部'] + sorted(df['年月'].unique().tolist(), reverse=True)
    filter_month = st.selectbox("📅 篩選月份", all_months_list, key="list_month")

    df_show = df.copy() if filter_month == '全部' else df[df['年月'] == filter_month].copy()

    if '收據照片' in df_show.columns:
        df_show['照片附件'] = df_show['收據照片'].apply(
            lambda x: "🔗 查看照片" if pd.notnull(x) else ""
        )

    clean_cols = [c for c in df_show.columns if c not in ['時間戳記', 'resourcekey', '收據照片', '年月']]

    st.dataframe(
        df_show[clean_cols].sort_index(ascending=False).style.format({
            "金額": "{:,.0f}",
            "台幣金額": "{:,.0f}"
        }),
        use_container_width=True
    )
    st.caption(f"共 {len(df_show)} 筆記錄")