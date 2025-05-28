import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Заголовок приложения
st.title("Анализ показателей «Факт» и «Факт Валовая прибыль»")

# Путь к Excel-файлу
FILE_PATH ="https://github.com/N-sam-sn/N/blob/main/Data01.xlsx"

@st.cache_data
def load_data(path):
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()
    return df

df = load_data(FILE_PATH)

# Сайдбар с фильтрами
st.sidebar.header("Фильтры")

kanals = ["Все"] + sorted(df["Канал"].dropna().unique().tolist())
otdels = ["Все"] + sorted(df["Отдел"].dropna().unique().tolist())
regions = ["Все"] + sorted(df["Регион"].dropna().unique().tolist())

sel_kanal = st.sidebar.selectbox("Канал", kanals)
sel_otdel = st.sidebar.selectbox("Отдел", otdels)
sel_region = st.sidebar.selectbox("Регион", regions)

# Применяем фильтрацию
filtered = df.copy()
if sel_kanal != "Все":
    filtered = filtered[filtered["Канал"] == sel_kanal]
if sel_otdel != "Все":
    filtered = filtered[filtered["Отдел"] == sel_otdel]
if sel_region != "Все":
    filtered = filtered[filtered["Регион"] == sel_region]

st.markdown(f"**Показатели для**:  "
            f"{'Канал = ' + sel_kanal if sel_kanal!='Все' else ''}  "
            f"{'Отдел = ' + sel_otdel if sel_otdel!='Все' else ''}  "
            f"{'Регион = ' + sel_region if sel_region!='Все' else ''}")

if filtered.empty:
    st.warning("Нет данных для выбранных фильтров.")
else:
    # Группируем по покупателю и суммируем
    agg = filtered.groupby("Покупатель")[["Факт", "Факт Валовая прибыль"]].sum().reset_index()

    # Строим график
    fig = go.Figure([
        go.Bar(name="Факт", x=agg["Покупатель"], y=agg["Факт"]),
        go.Bar(name="Факт Валовая прибыль", x=agg["Покупатель"], y=agg["Факт Валовая прибыль"])
    ])
    fig.update_layout(
        barmode="group",
        xaxis_title="Покупатель",
        yaxis_title="Сумма",
        height=600,
        width=900
    )

    st.plotly_chart(fig, use_container_width=True)
