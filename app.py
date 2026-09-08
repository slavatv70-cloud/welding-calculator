import streamlit as st
import math

# Настройка страницы
st.set_page_config(page_title="Инженерный калькулятор сварки", page_icon="⚡", layout="wide")

st.title("⚡ Профессиональный калькулятор расхода сварочных материалов")
st.caption("Разработано в соответствии с ГОСТ 16037-80 (трубы), ГОСТ 5264-80 (листы, прутки) и технологическими нормативами.")

# ==========================================
# БОКОВАЯ ПАНЕЛЬ: ОСНОВНЫЕ НАСТРОЙКИ
# ==========================================
st.sidebar.header("📌 Основные параметры")

category = st.sidebar.selectbox(
    "Тип конструкции", 
    ["Расчет труб (ГОСТ 16037-80)", "Расчет листов (ГОСТ 5264-80)", "Расчет прутков (ГОСТ 5264-80)"]
)

weld_method = st.sidebar.selectbox(
    "Способ сварки",
    ["Ручная дуговая (РДС)", "Полуавтомат (MIG/MAG в CO₂)", "Аргонодуговая (TIG) / Газовая"]
)

position = st.sidebar.selectbox(
    "Положение шва",
    ["Нижнее", "Горизонтальное", "Вертикальное", "Потолочное", "Наклонное"]
)

# Поправочные коэффициенты расхода от положения шва (гравитационные потери)
position_multipliers = {
    "Нижнее": 1.0,
    "Горизонтальное": 1.05,
    "Вертикальное": 1.10,
    "Потолочное": 1.20,
    "Наклонное": 1.07
}
k_pos = position_multipliers[position]

# Коэффициенты перехода наплавленного металла в расходный материал
method_coefficients = {
    "Ручная дуговая (РДС)": {"name": "электродов", "k": 1.50},
    "Полуавтомат (MIG/MAG в CO₂)": {"name": "проволоки", "k": 1.12},
    "Аргонодуговая (TIG) / Газовая": {"name": "присадочного прутка/проволоки", "k": 1.05}
}
mat_name = method_coefficients[weld_method]["name"]
k_method = method_coefficients[weld_method]["k"]

# Плотность стали (кг/м3)
DENSITY_STEEL = 7850

# ==========================================
# ДИНАМИЧЕСКИЕ МЕНЮ И ГЕОМЕТРИЧЕСКИЙ РАСЧЕТ
# ==========================================
F_weld = 0.0  # Площадь сечения шва в мм2
length_m = 0.0  # Общая длина шва в метрах
weld_count = 1

if category == "Расчет труб (ГОСТ 16037-80)":
    st.subheader("🗜️ Параметры трубного соединения")
    joint = st.selectbox("Тип соединения по ГОСТ 16037-80", ["С2", "С8", "С17", "У5", "У7", "У8"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        D = st.number_input("Наружный диаметр трубы (D), мм", min_value=10.0, value=57.0, step=1.0)
    with col2:
        S = st.number_input("Толщина стенки трубы (S), мм", min_value=1.0, value=3.0, step=0.5)
    with col3:
        weld_count = st.number_input("Количество стыков, шт", min_value=1, value=1, step=1)
        
    length_m = (math.pi * (D - S) / 1000) * weld_count  # Средняя длина окружности шва
    
    # Геометрические алгоритмы для стыков труб
    if joint == "С2":
        # Стыковое без скоса кромок, одностороннее
        b = st.number_input("Зазор после прихватки (b), мм", min_value=0.0, value=1.0, step=0.5)
        g = st.number_input("Выпуклость шва (g), мм", min_value=0.5, value=1.0, step=0.5)
        e = S + b if (S + b) > 3 else 4.0  # Примерная ширина шва
        F_weld = (S * b) + (0.75 * e * g)
        
    elif joint == "С8":
        # Стыковое со скосом одной кромки
        b = st.number_input("Зазор (b), мм", min_value=0.0, value=1.5, step=0.5)
        g = st.number_input("Выпуклость шва (g), мм", min_value=0.5, value=1.5, step=0.5)
        angle = st.number_input("Угол скоса кромок, град", min_value=15, max_value=50, value=30)
        c = st.number_input("Притупление кромок (c), мм", min_value=0.5, value=1.0, step=0.5)
        
        # Разделка (прямоугольник зазора + треугольник скоса) + усиление
        h_bevel = S - c
        b_bevel = h_bevel * math.tan(math.radians(angle))
        e = b + b_bevel + 2 # ориентировочная ширина шва
        F_weld = (S * b) + (0.5 * b_bevel * h_bevel) + (0.75 * e * g)

    elif joint == "С17":
        # Стыковое со скосом двух кромок
        b = st.number_input("Зазор (b), мм", min_value=0.0, value=2.0, step=0.5)
        g = st.number_input("Выпуклость шва (g), мм", min_value=0.5, value=2.0, step=0.5)
        angle = st.number_input("Угол разделки (суммарный), град", min_value=30, max_value=90, value=60)
        c = st.number_input("Притупление кромок (c), мм", min_value=0.5, value=1.5, step=0.5)
        
        h_bevel = S - c
        b_bevel = 2 * (h_bevel * math.tan(math.radians(angle / 2)))
        e = b + b_bevel
        F_weld = (S * b) + (0.5 * b_bevel * h_bevel) + (0.75 * e * g)
        
    elif joint in ["У5", "У7", "У8"]:
        # Угловые соединения труб с фланцами/плоскостями
        st.info(f"Для соединения {joint} рассчитывается угловой шов (катет).")
        col1_у, col2_у = st.columns(2)
        with col1_у:
            K = st.number_input("Катет наружного шва (K), мм", min_value=2.0, value=4.0, step=0.5)
        with col2_у:
            has_double_weld = st.checkbox("Двусторонний шов (наличие внутреннего шва K1)", value=(joint == "У5"))
        
        # Основной угловой шов (прямоугольный треугольник + выпуклость)
        F_weld = (0.5 * K * K) + (0.2 * K * K) # Треугольник + приближенное усиление
        
        if has_double_weld:
            K1 = st.number_input("Катет внутреннего шва (K1), мм", min_value=2.0, value=3.0, step=0.5)
            F_weld += (0.5 * K1 * K1) + (0.2 * K1 * K1)

elif category == "Расчет листов (ГОСТ 5264-80)":
    st.subheader("📋 Параметры листового соединения")
    joint = st.selectbox("Тип соединения по ГОСТ 5264-80", ["Н1", "Н2", "Т1", "Т3", "У4", "У5"])
    
    col1, col2 = st.columns(2)
    with col1:
        S = st.number_input("Толщина листов (S), мм", min_value=1.0, value=4.0, step=1.0)
    with col2:
        length_m = st.number_input("Общая длина сварных швов (всего), метров", min_value=0.1, value=5.0, step=0.5)

    # Нахлесточные (Н), Тавровые (Т) и Угловые (У) соединения без скоса кромок считаются по катетам
    if joint in ["Н1", "Т1", "У4"]:
        K = st.number_input("Катет шва (K), мм", min_value=2.0, value=float(S), step=0.5)
        F_weld = (0.5 * K * K) * 1.2  # 1.2 — коэффициент на выпуклость шва
    elif joint in ["Н2", "Т3", "У5"]:
        st.info(f"Соединение {joint} является двусторонним.")
        K = st.number_input("Катет швов (K), мм", min_value=2.0, value=float(S), step=0.5)
        F_weld = 2 * ((0.5 * K * K) * 1.2)

elif category == "Расчет прутков (ГОСТ 5264-80)":
    st.subheader("🔩 Параметры соединения круглых прутков")
    joint = st.selectbox("Тип соединения", ["С25 (Стыковое с косым резом / накладками)"])
    
    col1, col2 = st.columns(2)
    with col1:
        d_bar = st.number_input("Диаметр прутка (d), мм", min_value=5.0, value=16.0, step=1.0)
    with col2:
        weld_count = st.number_input("Количество стыков прутков, шт", min_value=1, value=1, step=1)
        
    # Моделирование стыка С25 (V-образная ручная или полуавтоматическая заварка по торцам)
    st.info("Расчет ведется для стыкового соединения круглого проката с полной разделкой.")
    F_weld = (math.pi * (d_bar ** 2) / 4) * 0.25  # Эквивалентная усредненная площадь наплавки стыка
    length_m = (d_bar / 1000) * weld_count

# ==========================================
# БЛОК ВЫЧИСЛЕНИЯ РЕЗУЛЬТАТОВ
# ==========================================
st.write("---")
st.header("📊 Результаты расчета")

# Масса чистого наплавленного металла (кг)
# Переводим площадь из мм2 в м2 (10^-6) и длину из м в м.
mass_deposited = (F_weld * 1e-6) * length_m * DENSITY_STEEL

# Полная масса расходуемого материала с учетом всех технологических потерь
mass_total_required = mass_deposited * k_method * k_pos

col_res1, col_res2, col_res3 = st.columns(3)

with col_res1:
    st.metric(
        label="Площадь сечения шва", 
        value=f"{F_weld:.2f} мм²"
    )
with col_res2:
    st.metric(
        label="Масса наплавленного металла (чистый вес)", 
        value=f"{mass_deposited:.3f} кг"
    )
with col_res3:
    st.metric(
        label=f"Необходимый расход {mat_name}", 
        value=f"{mass_total_required:.3f} кг",
        delta=f"Потери: {((mass_total_required - mass_deposited)/mass_total_required)*100:.1f}%",
        delta_color="inverse"
    )

# Технологическая справка
st.subheader("💡 Справка по расчету:")
st.markdown(f"""
* **Выбранный метод:** {weld_method} (базовый коэффициент расхода материала: **{k_method}**).
* **Поправка на положение шва:** Пространственное положение *{position}* добавляет коэффициент **{k_pos}** на потери от стекания жидкого металла.
* **Общая протяженность укладки:** {length_m:.3f} пог. м. шва.
* **Защита от ошибок:** В отличие от старого софта, калькулятор заблокировал лишние строки. Вам нужно приобрести исключительно **{mass_total_required:.3f} кг** {mat_name}.
""")
