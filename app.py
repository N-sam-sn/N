from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Дашборд по продажам",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "Result.csv"


@st.cache_data(ttl=300, show_spinner="Загрузка данных...")
def load_data(file_path: str, file_mtime: float) -> pd.DataFrame:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Файл данных не найден: {path}\n"
            "Создайте папку data рядом с app.py и поместите туда Result.csv."
        )

    df = pd.read_csv(
        path,
        encoding="utf-8-sig",
        sep=";",
        low_memory=False,
    )

    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )

    def clean_number(value):
        if pd.isna(value):
            return None

        text = (
            str(value)
            .replace("\xa0", "")
            .replace(" ", "")
            .replace(",", ".")
            .replace("–", "0")
            .replace("—", "0")
            .strip()
        )

        if text in {"", "-", "None", "nan"}:
            return None

        return text

    def clean_text(value):
        if pd.isna(value) or str(value).strip() == "":
            return "-"
        return str(value).strip()

    numeric_columns = ["ОП", "ОП План", "ВП", "ВП План", "ОП_ПГ"]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = df[column].apply(clean_number)
            df[column] = pd.to_numeric(df[column], errors="coerce")

    text_columns = [
        "Менеджер",
        "Код",
        "Покупатель",
        "Регион",
        "Добавить в план",
        "Отдел",
        "Канал",
        "ИНН",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].apply(clean_text)

    required_numeric = ["ОП", "ОП План", "ВП", "ВП План"]
    missing_required = [col for col in required_numeric if col not in df.columns]

    if missing_required:
        raise ValueError(
            "В CSV отсутствуют обязательные столбцы: "
            + ", ".join(missing_required)
        )

    df = df[
        (df["ОП План"].fillna(0) != 0)
        | (df["ОП"].fillna(0) != 0)
        | (df["ВП"].fillna(0) != 0)
        | (df["ВП План"].fillna(0) != 0)
    ].copy()

    df["% ОП"] = df["ОП"].div(df["ОП План"].replace(0, pd.NA))
    df["% ВП"] = df["ВП"].div(df["ВП План"].replace(0, pd.NA))

    return df


def multiselect_with_all(label: str, options: list[str]) -> list[str]:
    all_label = "Все"
    selected = st.sidebar.multiselect(
        label,
        [all_label] + options,
        default=[all_label],
    )
    return options if all_label in selected else selected


def safe_percent(value) -> str:
    return f"{value:.0%}" if pd.notna(value) else ""


def safe_number(value) -> str:
    return f"{value:,.0f}".replace(",", " ") if pd.notna(value) else ""


def highlight_percent_cols(data: pd.DataFrame) -> pd.DataFrame:
    styles = pd.DataFrame("", index=data.index, columns=data.columns)

    for column in ["% ОП", "% ВП"]:
        if column in data.columns:
            styles[column] = data[column].apply(
                lambda value: (
                    "background-color: #c6efce; color: #006100;"
                    if pd.notna(value) and value >= 1
                    else "background-color: #ffc7ce; color: #9c0006;"
                    if pd.notna(value) and value < 1
                    else ""
                )
            )

    return styles


st.markdown(
    """
    <style>
        .main .block-container {
            max-width: 2000px;
            padding-top: 1.2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        .scrollable-table-container {
            max-height: 80vh;
            overflow-y: auto;
            overflow-x: auto;
            border: 1px solid #d9d9d9;
            border-radius: 6px;
        }

        .scrollable-table-container table {
            width: 100%;
            border-collapse: collapse;
        }

        .scrollable-table-container th,
        .scrollable-table-container td {
            white-space: nowrap;
            text-align: center;
            padding: 6px 8px;
            border-bottom: 1px solid #eeeeee;
        }

        .scrollable-table-container thead th {
            position: sticky;
            top: 0;
            z-index: 2;
            background-color: #f1f1f1;
        }

        .summary-card {
            padding: 12px 16px;
            margin: 8px 0 16px 0;
            border: 1px solid #e3e3e3;
            border-radius: 8px;
            background: #fafafa;
            font-weight: 600;
            line-height: 1.9;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Дашборд по продажам июля 2026")

try:
    data_mtime = DATA_FILE.stat().st_mtime
    df = load_data(str(DATA_FILE), data_mtime)
except Exception as exc:
    st.error("Не удалось загрузить данные.")
    st.exception(exc)
    st.stop()


st.sidebar.header("Фильтрация")
filtered_df = df.copy()

filter_columns = [
    ("Отдел", "Отдел"),
    ("Канал", "Канал"),
    ("Регион", "Регион"),
    ("Добавить в план", "Добавить в план"),
    ("Менеджер", "Менеджер"),
    ("Покупатель", "Покупатель"),
]

for column, label in filter_columns:
    if column in filtered_df.columns:
        options = sorted(
            filtered_df[column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected = multiselect_with_all(label, options)

        if selected:
            filtered_df = filtered_df[
                filtered_df[column].astype(str).isin(selected)
            ]
        else:
            filtered_df = filtered_df.iloc[0:0]


if filtered_df.empty:
    st.warning("⚠️ Нет данных для отображения — проверьте настройки фильтрации.")
    st.stop()

display_columns = [
    "Менеджер",
    "Код",
    "Покупатель",
    "ОП",
    "ОП План",
    "% ОП",
    "ВП",
    "ВП План",
    "% ВП",
    "ОП_ПГ",
]

available_columns = [
    column for column in display_columns if column in filtered_df.columns
]

df_result = filtered_df[available_columns].copy()
df_result.rename(
    columns={
        "ОП": "ОП Факт",
        "ВП": "ВП Факт",
    },
    inplace=True,
)

for column in [
    "ОП Факт",
    "ОП План",
    "ВП Факт",
    "ВП План",
    "ОП_ПГ",
]:
    if column not in df_result.columns:
        df_result[column] = 0

total_op = df_result["ОП Факт"].sum(min_count=1)
total_op_plan = df_result["ОП План"].sum(min_count=1)
total_vp = df_result["ВП Факт"].sum(min_count=1)
total_vp_plan = df_result["ВП План"].sum(min_count=1)
total_pg = df_result["ОП_ПГ"].sum(min_count=1)

percent_op_total = (
    total_op / total_op_plan
    if pd.notna(total_op_plan) and total_op_plan != 0
    else None
)

percent_vp_total = (
    total_vp / total_vp_plan
    if pd.notna(total_vp_plan) and total_vp_plan != 0
    else None
)

totals = {column: "" for column in df_result.columns}
totals.update(
    {
        "Менеджер": "ИТОГО",
        "ОП Факт": total_op,
        "ОП План": total_op_plan,
        "% ОП": percent_op_total,
        "ВП Факт": total_vp,
        "ВП План": total_vp_plan,
        "% ВП": percent_vp_total,
        "ОП_ПГ": total_pg,
    }
)

df_result = pd.concat(
    [df_result, pd.DataFrame([totals])],
    ignore_index=True,
)

color_op = (
    "#c6efce"
    if percent_op_total is not None and percent_op_total >= 1
    else "#ffc7ce"
)

color_vp = (
    "#c6efce"
    if percent_vp_total is not None and percent_vp_total >= 1
    else "#ffc7ce"
)

summary_html = f"""
<div class="summary-card">
    ОП Факт: {safe_number(total_op)}
    &nbsp; | &nbsp;
    ОП План: {safe_number(total_op_plan)}
    &nbsp; | &nbsp;
    <span style="background-color:{color_op}; padding:3px 7px; border-radius:4px;">
        % ОП: {safe_percent(percent_op_total)}
    </span>
    &nbsp; | &nbsp;
    ВП Факт: {safe_number(total_vp)}
    &nbsp; | &nbsp;
    ВП План: {safe_number(total_vp_plan)}
    &nbsp; | &nbsp;
    <span style="background-color:{color_vp}; padding:3px 7px; border-radius:4px;">
        % ВП: {safe_percent(percent_vp_total)}
    </span>
    &nbsp; | &nbsp;
    ОП_ПГ: {safe_number(total_pg)}
</div>
"""

st.subheader("Результаты на 14.07.2026")
st.markdown(summary_html, unsafe_allow_html=True)

styled_html = (
    df_result.style
    .format(
        {
            "ОП Факт": safe_number,
            "ОП План": safe_number,
            "% ОП": safe_percent,
            "ВП Факт": safe_number,
            "ВП План": safe_number,
            "% ВП": safe_percent,
            "ОП_ПГ": safe_number,
        }
    )
    .apply(highlight_percent_cols, axis=None)
    .hide(axis="index")
    .to_html()
)

st.markdown(
    f"""
    <div class="scrollable-table-container">
        {styled_html}
    </div>
    """,
    unsafe_allow_html=True,
)
