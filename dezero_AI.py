import streamlit as st
import numpy as np
from dezero import Variable
import graphviz
from io import BytesIO

def plot_dot_graph(output):
    dot = graphviz.Digraph(format='png')
    funcs = []
    seen_set = set()

    def add_func(f):
        if f not in seen_set:
            funcs.append(f)
            seen_set.add(f)

    def add_var(var):
        name = str(id(var))
        label = f'{var.name}\nshape: {var.shape}' if hasattr(var, 'name') and var.name else f'shape: {var.shape}'
        dot.node(name, label=label)
        if var.creator is not None:
            add_func(var.creator)
            dot.edge(str(id(var.creator)), name)

    add_var(output)
    while funcs:
        func = funcs.pop()
        func_name = str(id(func))
        dot.node(func_name, label=func.__class__.__name__, shape='box')
        for x in func.inputs:
            add_var(x)
            dot.edge(str(id(x)), func_name)
        for y in func.outputs:
            dot.edge(func_name, str(id(y())))
    return dot

st.markdown("""
<style>
/* 배경색과 폰트톤 */
body {
    background-color: #f5f7fa;
    color: #34495e;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 입력 박스 스타일 */
.stNumberInput > div > input {
    font-size: 1rem;
    padding: 0.4rem;
    border-radius: 8px;
    border: 1.5px solid black;
    max-width: 110px;
}

/* 선택박스 스타일 */
.stSelectbox > div > div {
    font-size: 1rem;
    border-radius: 8px;
    border: 1.5px solid black;
    max-width: 180px;
}

/* 그래프 박스 */
.graph-box {
 background-color: #fff4e5;       /* 부드러운 크림색 느낌 */
 border-left: 5px solid #ff8c42;  /* 따뜻한 오렌지 계열 포인트 */
 padding: 0.8rem 1.2rem;
 border-radius: 6px;
 font-size: 0.9rem;
 line-height: 1.4;
 color: #6b4c00;                 /* 진한 갈색 텍스트 색상 */
 white-space: pre-line;
}

/* 계산 과정 박스 */
.calc-box {
    background-color: #eaf2f8;
    border-left: 5px solid #2980b9;
    padding: 0.8rem 1.2rem;
    border-radius: 6px;
    font-size: 0.9rem;
    line-height: 1.4;
    color: #2c3e50;
    white-space: pre-line;
}

/* 제목 스타일 */
h1 {
    color: #2c3e50;
    font-weight: 700;
    margin-bottom: 0.2rem;
    font-size: 1.8rem;
}

h2 {
    color: #2c3e50;
    margin-bottom: 0.8rem;
    font-size: 1.3rem;
}

/* 이미지 최대 높이 제한 */
img {
    max-height: 400px;
    width: auto !important;
}

/* 최대 너비 제한 및 중앙 정렬 */
section.main > div.block-container {
    max-width: 1000px;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)



st.markdown("""
<h1 style='font-size: 2.1rem; font-weight: 700; color: #2c3e50;'>
Graph-first Dezero: 실시간 연산 그래프 시각화
</h1>
""", unsafe_allow_html=True)

st.write("### 실시간으로 계산 그래프와 계산 과정을 확인하세요!")


x_val = st.number_input("x 값 입력", value=4.0, step=0.1, format="%.3f")
operation = st.selectbox("연산 선택", ["x² + x", "x³ + 2x", "sin(x) + x"])

x = Variable(np.array(x_val), name='x')

# 컬럼 비율을 좀 더 그래프쪽이 작게 조정
col1, col2 = st.columns([1.5, 3.5])

with col1:
    if operation == "x² + x":
        y = x ** 2 + x
        formula = r"x^2 + x"
    elif operation == "x³ + 2x":
        y = x ** 3 + 2 * x
        formula = r"x^3 + 2x"
    elif operation == "sin(x) + x":
        from dezero.functions import sin
        y = sin(x) + x
        formula = r"\sin(x) + x"

    y.backward()
    dot = plot_dot_graph(y)

    img_bytes = dot.pipe(format='png')

    st.markdown('<div class="graph-box"><h2 style="font-size:1.5rem; margin-bottom:0.5rem;">연산 그래프</h2></div>', unsafe_allow_html=True)

    if img_bytes:
        st.image(BytesIO(img_bytes), use_container_width=True)
    else:
        st.error("그래프 생성 실패")

with col2:
    st.markdown('<div class="calc-box"><h2 style="font-size:1.5rem; margin-bottom:0.5rem;">계산 과정</h2></div>', unsafe_allow_html=True)

    st.markdown(f"- 입력 변수 **x**: `{x.data:.3f}`")
    st.markdown(f"- 계산식: $$ {formula} $$")

    if operation == "x² + x":
        st.markdown(f"- 계산 과정:<br> 1) $$x^2 = {x.data ** 2:.4f}$$<br> 2) $$x^2 + x = {(x.data ** 2 + x.data):.4f}$$", unsafe_allow_html=True)
    elif operation == "x³ + 2x":
        st.markdown(f"- 계산 과정:<br> 1) $$x^3 = {x.data ** 3:.4f}$$<br> 2) $$2x = {(2 * x.data):.4f}$$<br> 3) $$x^3 + 2x = {(x.data ** 3 + 2 * x.data):.4f}$$", unsafe_allow_html=True)
    elif operation == "sin(x) + x":
        import math
        sin_val = math.sin(x.data)
        st.markdown(f"- 계산 과정:<br> 1) $$\\sin(x) = {sin_val:.4f}$$<br> 2) $$\\sin(x) + x = {(sin_val + x.data):.4f}$$", unsafe_allow_html=True)

    st.markdown(f"""
<div style="
    background-color: #d6f5d6;  /* 연한 초록 배경 */
    border: 2px solid #4CAF50; /* 초록색 테두리 */
    border-radius: 8px;
    padding: 15px;
    margin-top: 20px;
    font-size: 1.5rem;
    font-weight: 700;
    color: #2e7d32;
    text-align: center;
">
    답: <span style="color:#145214;">{y.data:.4f}</span>
</div>
""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
