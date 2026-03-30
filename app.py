import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
import streamlit as st

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="AI数据分析工具", layout="wide")
st.title("📊 AI 智能数据分析工具")

#从Secrets读取API KEY
if "api_key" in st.secrets:
    API_KEY = st.secrets["api_key"]
    api_ready =True
else :
    API_KEY = None
    api_ready =False

with st.sidebar:
    st.header("⚙ 设置")
    if api_ready:
        st.success("AI分析已就绪(密钥已配置)")
    else :
        st.warning("❗ API key 未配置,AI分析不可用")
        st.markdown("---")
        st.markdown("### 使用说明")
        st.markdown("1.上传CSV文件")
        st.markdown("2.选择销售额和利润列")
        st.markdown("3.点击分析按钮")
        st.markdown("4.查看统计、图表和AI建议")
# 侧边栏：输入 API Key
#with st.sidebar:
    #st.header("⚙️ 设置")
    #api_key = st.text_input("智谱 API Key", type="password", help="输入你的智谱 API Key")
    #st.markdown("---")
    #st.markdown("### 使用说明")
    #st.markdown("1. 输入 API Key")
    #st.markdown("2. 上传 CSV 文件")
    #st.markdown("3. 点击分析按钮")
    #st.markdown("4. 查看统计、图表和 AI 建议")

# 主区域：文件上传
uploaded_file = st.file_uploader("上传 CSV 文件", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 读取文件
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, encoding='gbk')
    else:
        df = pd.read_excel(uploaded_file)

    st.success(f"✅ 成功读取文件，共 {len(df)} 行，{len(df.columns)} 列")

    # 显示数据预览
    with st.expander("📋 数据预览"):
        st.dataframe(df.head(10))

    # 选择数值列
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if len(numeric_cols) >= 2:
        col1 = st.selectbox("选择销售额列", numeric_cols, index=0)
        col2 = st.selectbox("选择利润列", numeric_cols, index=min(1, len(numeric_cols)-1))

        if st.button("🔍 开始分析", type="primary"):
            # 计算统计
            total_sales = df[col1].sum()
            avg_sales = df[col1].mean()
            total_profit = df[col2].sum()
            avg_profit = df[col2].mean()
            max_month = df[df[col1] == df[col1].max()].iloc[0, 0] if len(df) > 0 else "无"

            # 显示统计
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("总销售额", f"{total_sales:,.0f}")
            with col_b:
                st.metric("平均销售额", f"{avg_sales:,.0f}")
            with col_c:
                st.metric("总利润", f"{total_profit:,.0f}")
            with col_d:
                st.metric("平均利润", f"{avg_profit:,.0f}")

            # 画图
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

            # 柱状图
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
            fig2, ax = plt.subplots(figsize=(10, 5))
            ax.plot(x_labels, df[col1], marker='o', label=col1, linewidth=2)
            ax.plot(x_labels, df[col2], marker='s', label=col2, linewidth=2)
            ax.set_title("趋势对比")
            ax.set_xlabel("类别")
            ax.set_ylabel("金额")
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            st.pyplot(fig2)

            # AI 分析（如果有 API Key）
            if API_key:
                with st.spinner("🤖 AI 正在分析中..."):
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://open.bigmodel.cn/api/paas/v4/"
                    )

                    data_summary = f"""
数据明细：
{df.to_string()}

统计结果：
- 总{col1}：{total_sales} 元
- 平均{col1}：{avg_sales} 元
- 总{col2}：{total_profit} 元
- 平均{col2}：{avg_profit} 元
- {col1}最高的行：{max_month}

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
            else:
                st.warning("⚠️ AI分析不可用:未配置API key")
                #st.warning("⚠️ 请在左侧输入 API Key 以获取 AI 分析")
    else:
        st.error("请确保数据包含至少两列数值型数据（如销售额、利润）")
else:
    st.info("👈 请先上传 CSV 文件开始分析")
