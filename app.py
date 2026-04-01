import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
import streamlit as st
import json

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="AI数据分析工具", layout="wide")
st.title("📊 AI 智能数据分析工具")

# 获取 API Key
if hasattr(st, 'secrets') and "api_key" in st.secrets:
    API_KEY = st.secrets["api_key"]
    api_ready = True
else:
    API_KEY = None
    api_ready = False

with st.sidebar:
    st.header("⚙️ 设置")
    if api_ready:
        st.success("✅ AI 分析已就绪")
    else:
        api_key_input = st.text_input("智谱 API Key", type="password", help="输入你的智谱 API Key")
        if api_key_input:
            API_KEY = api_key_input
            api_ready = True
            st.success("✅ API Key 已设置")
        else:
            st.warning("⚠️ 请输入 API Key 以使用 AI 分析")
    st.markdown("---")
    st.markdown("### 使用说明")
    st.markdown("1. 上传 CSV/Excel/JSON 文件")
    st.markdown("2. 选择销售额和利润列")
    st.markdown("3. 点击分析按钮")
    st.markdown("4. 查看统计、图表和 AI 建议")

def read_file(uploaded_file):
    """读取不同格式文件"""
    file_name = uploaded_file.name.lower()

    if file_name.endswith('.csv'):
        try:
            return pd.read_csv(uploaded_file, encoding='gbk')
        except:
            return pd.read_csv(uploaded_file, encoding='utf-8')
    elif file_name.endswith('.xlsx'):
        return pd.read_excel(uploaded_file)
    elif file_name.endswith('.xls'):
        return pd.read_excel(uploaded_file, engine='xlrd')
    elif file_name.endswith('.json'):
        content = uploaded_file.getvalue().decode('utf-8')
        data = json.loads(content)
        return pd.json_normalize(data)
    elif file_name.endswith('.parquet'):
        return pd.read_parquet(uploaded_file)
    elif file_name.endswith('.tsv'):
        return pd.read_csv(uploaded_file, sep='\t')
    else:
        st.error(f"不支持的文件格式: {file_name}")
        return None

uploaded_file = st.file_uploader("上传文件", type=['csv', 'xlsx', 'json', 'xls', 'parquet', 'tsv'])

if uploaded_file is not None:
    try:
        df = read_file(uploaded_file)
        if df is None:
            st.stop()
    except Exception as e:
        st.error(f"读取文件失败：{e}")
        st.stop()

    st.success(f"✅ 成功读取文件，共 {len(df)} 行，{len(df.columns)} 列")
    st.info(f"📁 文件格式：{uploaded_file.name.split('.')[-1].upper()}")

    with st.expander("📋 数据预览"):
        st.dataframe(df.head(10))

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if len(numeric_cols) >= 2:
        col1 = st.selectbox("选择销售额列", numeric_cols, index=0)
        col2 = st.selectbox("选择利润列", numeric_cols, index=min(1, len(numeric_cols)-1))

        if st.button("🔍 开始分析", type="primary"):
            total_sales = df[col1].sum()
            avg_sales = df[col1].mean()
            total_profit = df[col2].sum()
            avg_profit = df[col2].mean()
            max_month = df[df[col1] == df[col1].max()].iloc[0, 0] if len(df) > 0 else "无"

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("总销售额", f"{total_sales:,.0f}")
            with col_b:
                st.metric("平均销售额", f"{avg_sales:,.0f}")
            with col_c:
                st.metric("总利润", f"{total_profit:,.0f}")
            with col_d:
                st.metric("平均利润", f"{avg_profit:,.0f}")

            # 柱状图
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
            x_labels = df.iloc[:, 0].astype(str)

            ax1.bar(x_labels, df[col1], color='steelblue')
            ax1.set_title(f"{col1} 分布")
            ax1.set_xlabel("类别")
            ax1.set_ylabel(col1)
            ax1.tick_params(axis='x', rotation=45)

            ax2.bar(x_labels, df[col2], color='coral')
            ax2.set_title(f"{col2} 分布")
            ax2.set_xlabel("类别")
            ax2.set_ylabel(col2)
            ax2.tick_params(axis='x', rotation=45)

            plt.tight_layout()
            st.pyplot(fig)

            # 折线图
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(x_labels, df[col1], marker='o', label=col1, linewidth=2)
            ax.plot(x_labels, df[col2], marker='s', label=col2, linewidth=2)
            ax.set_title("趋势对比")
            ax.set_xlabel("类别")
            ax.set_ylabel("金额")
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            st.pyplot(fig)

            # AI 分析
            if api_ready and API_KEY:
                with st.spinner("🤖 AI 正在分析中..."):
                    try:
                        client = OpenAI(
                            api_key=API_KEY,
                            base_url="https://open.bigmodel.cn/api/paas/v4/"
                        )

                        data_summary = f"""
数据明细：
{df.to_string()}

统计结果：
- 总销售额：{total_sales} 元
- 平均销售额：{avg_sales} 元
- 总利润：{total_profit} 元
- 平均利润：{avg_profit} 元
- 销售额最高的月份：{max_month}

请根据以上数据，给出3条业务建议和分析洞察。
"""

                        response = client.chat.completions.create(
                            model="glm-4-flash",
                            messages=[
                                {"role": "system", "content": "你是一个专业的数据分析师"},
                                {"role": "user", "content": data_summary}
                            ]
                        )

                        st.markdown("### 🤖 AI 分析建议")
                        st.info(response.choices[0].message.content)
                    except Exception as e:
                        st.error(f"AI 分析出错：{e}")
            else:
                st.warning("⚠️ 请先输入 API Key 以获取 AI 分析")
    else:
        st.error("请确保数据包含至少两列数值型数据")
else:
    st.info("👈 请先上传文件开始分析")
