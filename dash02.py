import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import requests
import pygame
from io import BytesIO

# Заголовок приложения
st.title("Анализ показателей «Факт ОП» и «Факт Валовая прибыль»")
saved_emoji = pygame.image.load("https://raw.githubusercontent.com/N-sam-sn/N/main/B01r.png")
screen.blit(saved_emoji, (100, 100))
pygame.display.flip()

# Ссылка на Excel-файл в GitHub
FILE_URL = "https://raw.githubusercontent.com/N-sam-sn/N/main/Data01.xlsx"

@st.cache_data
def load_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Проверка ошибок
    df = pd.read_excel(BytesIO(response.content))
    df.columns = df.columns.str.strip()
    return df

df = load_data(FILE_URL)

# Сайдбар с фильтрами- План /Факт/ Прогноз
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
    # Группируем по покупателю и суммируем ВСЕ необходимые столбцы
    agg = filtered.groupby("Вид плана продаж")[
        ["Факт", "План на месяц", "Факт Валовая прибыль", "План Валовая прибыль","Тенденция по кол-ву рабочих дней","ВП Тенденция по кол-ву рабочих дней"]
    ].sum().reset_index()

    # Сортируем данные для графиков
    agg_sorted_fact = agg.sort_values(by="Факт", ascending=False)
    agg_sorted_profit = agg.sort_values(by="Факт Валовая прибыль", ascending=False)
    #agg_sorted_profit = agg.sort_values(by="ВП Тенденция по кол-ву рабочих дней", ascending=False)

    # Исходный график (оставляем как есть)
    fig_original = go.Figure([
        go.Bar(name="Факт ОП", x=agg["Вид плана продаж"], y=agg["Факт"],marker_color='#2ca02c'),
        go.Bar(name="Тенденция ОП", x=agg["Вид плана продаж"], y=agg["Тенденция по кол-ву рабочих дней"],marker_color='#0fd820'),
        go.Bar(name="Факт Валовая прибыль", x=agg["Вид плана продаж"], y=agg["Факт Валовая прибыль"],marker_color='#1f77b4'),
        go.Bar(name="Тенденция ВП", x=agg["Вид плана продаж"], y=agg["ВП Тенденция по кол-ву рабочих дней"],marker_color='#1f07b4')
    ])
    fig_original.update_layout(
        barmode="group",
        title="Факт ОП vs Факт Валовая прибыль",
        xaxis_title="Вид плана продаж",
        yaxis_title="Сумма",
        height=500
    )

    # График 1: Факт ОП vs План ОП
    fig_fact = go.Figure()
    fig_fact.add_trace(go.Bar(
        name="Факт ОП", 
        x=agg_sorted_fact["Вид плана продаж"], 
        y=agg_sorted_fact["Факт"],
        marker_color='#2ca02c'
    ))
    fig_fact.add_trace(go.Bar(
        name="План ОП", 
        x=agg_sorted_fact["Вид плана продаж"], 
        y=agg_sorted_fact["План на месяц"],
        marker_color='#d62728'
    ))
    fig_fact.add_trace(go.Bar(
        name="Тенденция ОП", 
        x=agg_sorted_fact["Вид плана продаж"], 
        y=agg_sorted_fact["Тенденция по кол-ву рабочих дней"],
        marker_color='#1f77b4'
    ))
    fig_fact.update_layout(
        barmode="group",
        title="Факт ОП vs План ОП (сортировка по Факту)",
        xaxis_title="Вид плана продаж",
        yaxis_title="Сумма",
        height=500
    )

    # График 2: Факт Валовая прибыль vs План Валовая прибыль
    fig_profit = go.Figure()
    fig_profit.add_trace(go.Bar(
        name="Факт Валовая прибыль", 
        x=agg_sorted_profit["Вид плана продаж"], 
        y=agg_sorted_profit["Факт Валовая прибыль"],
        marker_color='#2ca02c'
    ))
    fig_profit.add_trace(go.Bar(
        name="План Валовая прибыль", 
        x=agg_sorted_profit["Вид плана продаж"], 
        y=agg_sorted_profit["План Валовая прибыль"],
        marker_color='#d62728'
    ))
    fig_profit.add_trace(go.Bar(
        name="Тенденция ВП", 
        x=agg_sorted_profit["Вид плана продаж"], 
        y=agg_sorted_profit["ВП Тенденция по кол-ву рабочих дней"],
        marker_color='#1f77b4'
    ))
    fig_profit.update_layout(
        barmode="group",
        title="Валовая прибыль: Факт ВП vs План ВП(сортировка по Факту)",
        xaxis_title="Вид плана продаж",
        yaxis_title="Сумма",
        height=500
    )
    #st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(fig_original, use_container_width=True)
    st.plotly_chart(fig_fact, use_container_width=True)
    st.plotly_chart(fig_profit, use_container_width=True)
