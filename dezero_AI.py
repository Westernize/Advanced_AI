import streamlit as st
import numpy as np
from dezero import Variable
import graphviz
from io import BytesIO

# --- 스타일 추가 ---
st.markdown("""
<style>
body {
    background-color: #f5f7fa;
    color: #34495e;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.stNumberInput > div > input {
    font-size: 1rem;
    padding: 0.4rem;
    border-radius: 8px;
    border: 1.5px solid black;
    max-width: 110px;
}
.stTextInput > div > input {
    font-size: 1rem;
    padding: 0.4rem;
    border-radius: 8px;
    border: 1.5px solid black;
    max-width: 320px;
}
.graph-box {
 background-color: #fff4e5;
 border-left: 5px solid #ff8c42;
 padding: 0.8rem 1.2rem;
 border-radius: 6px;
 font-size: 0.9rem;
 line-height: 1.4;
 color: #6b4c00;
 white-space: pre-line;
}
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
img {
    max-height: 400px;
    width: auto !important;
}
section.main > div.block-container {
    max-width: 1000px;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)
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
        val = var.data if hasattr(var, 'data') else None
        # 값이 실수 또는 넘파이 배열이면 4자리로 포맷
        if isinstance(val, float):
            val_str = f"{val:.4f}"
        elif isinstance(val, np.ndarray) and val.size == 1:
            val_str = f"{val.item():.4f}"
        else:
            val_str = str(val)
        if hasattr(var, 'name') and var.name:
            label = f'{var.name}={val_str}\nshape: {var.shape}'
        else:
            label = f'값: {val_str}\nshape: {var.shape}'
        dot.node(name, label=label, shape='ellipse')
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
st.markdown("<h1 style='font-size:2.2rem; font-weight:700; color:#2c3e50;'>Graph-first Dezero: 실시간 연산 그래프 시각화</h1>", unsafe_allow_html=True)

st.markdown("""
<div style="background-color:#e8f5e9; border-left:5px solid #43a047; padding:1rem 1.2rem; border-radius:10px; margin-bottom:1.2rem; color:#205723;">
<strong>예시로 입력할 수 있는 수식:</strong><br>
<table style="border:none; background:none;">
  <tr>
    <td style="padding-right:32px;"><code>x**2 + x</code></td>
    <td><code>sin(x) + x</code></td>
  </tr>
  <tr>
    <td style="padding-right:32px;"><code>x**3 + 2*x</code></td>
    <td><code>exp(x) - x</code></td>
  </tr>
  <tr>
    <td style="padding-right:32px;"><code>log(x + 1)</code></td>
    <td><code>cos(x) + x</code></td>
  </tr>
  <tr>
    <td style="padding-right:32px;"><code>x**4 + 2*x**2 + 1</code></td>
    <td><code>x**2 - x + 1</code></td>
  </tr>
  <tr>
    <td style="padding-right:32px;"><code>sin(x) * cos(x)</code></td>
    <td><code>exp(x) + log(x + 1)</code></td>
  </tr>
  <tr>
    <td style="padding-right:32px;"><code>x**2 * sin(x)</code></td>
    <td></td>
  </tr>
</table>
<br>
<span style="color:#d32f2f; font-weight:600;">위 수식들은 계산 과정까지 상세히 출력됩니다.<br>
그 외의 수식은 계산 결과만 출력됩니다.</span>
</div>
""", unsafe_allow_html=True)

x_val = st.number_input("x 값 입력", value=4.0)
operation = st.text_input(
    "연산 수식 입력 (예: x**2 + x, sin(x) + x, exp(x) - x 등)",
    value="x**2 + x"
)
col1, col2 = st.columns([2, 3])

with col1:
    import math
    from dezero.functions import sin, cos, exp, log

    x = Variable(np.array(x_val), name='x')
    local_dict = {
        'x': x,
        'sin': sin,
        'cos': cos,
        'exp': exp,
        'log': log,
        'math': math,
        'np': np
    }
    try:
        y = eval(operation, {"__builtins__": {}}, local_dict)
        y.name = operation
        y.backward()
        dot = plot_dot_graph(y)
        img_bytes = dot.pipe(format='png')
        st.markdown('<div class="graph-box"><h2 style="font-size:1.5rem; margin-bottom:0.5rem;">연산 그래프</h2></div>', unsafe_allow_html=True)
        if img_bytes:
            st.image(BytesIO(img_bytes), use_container_width=True)
        else:
            st.error("그래프 생성 실패")
    except Exception as e:
        st.error(f"수식 오류: {e}")

with col2:
    st.markdown('<div class="calc-box"><h2 style="font-size:1.5rem; margin-bottom:0.5rem;">계산 과정</h2></div>', unsafe_allow_html=True)
    st.markdown(f"- 입력 변수 **x**: `{x_val}`")
    try:
        # ...existing code...
        if operation.replace(" ", "") == "x**2+x":
            x2 = x_val ** 2
            result = x2 + x_val
            st.markdown("- 계산식: \(x^2 + x\)")
            st.markdown(f"1) \(x^2 = {x2:.4f}\)")
            st.markdown(f"2) \(x^2 + x = {x2:.4f} + {x_val:.4f} = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
        elif operation.replace(" ", "") == "sin(x)+x":
            sinx = np.sin(x_val)
            result = sinx + x_val
            st.markdown("- 계산식: \(sin(x) + x\)")
            st.markdown(f"1) \(sin(x) = {sinx:.4f}\)")
            st.markdown(f"2) \(sin(x) + x = {sinx:.4f} + {x_val:.4f} = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
        elif operation.replace(" ", "") == "x**3+2*x":
            x3 = x_val ** 3
            x2x = 2 * x_val
            result = x3 + x2x
            st.markdown("- 계산식: \(x^3 + 2x\)")
            st.markdown(f"1) \(x^3 = {x3:.4f}\)")
            st.markdown(f"2) \(2x = {x2x:.4f}\)")
            st.markdown(f"3) \(x^3 + 2x = {x3:.4f} + {x2x:.4f} = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
        elif operation.replace(" ", "") == "exp(x)-x":
            expx = np.exp(x_val)
            result = expx - x_val
            st.markdown("- 계산식: \(exp(x) - x\)")
            st.markdown(f"1) \(exp(x) = {expx:.4f}\)")
            st.markdown(f"2) \(exp(x) - x = {expx:.4f} - {x_val:.4f} = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
        elif operation.replace(" ", "") == "log(x+1)":
            if x_val + 1 > 0:
                logx = np.log(x_val + 1)
                st.markdown("- 계산식: \(log(x + 1)\)")
                st.markdown(f"1) \(x + 1 = {x_val + 1:.4f}\)")
                st.markdown(f"2) \(log(x + 1) = {logx:.4f}\)")
                st.markdown(f"### 최종 결과값: {logx:.4f}")
            else:
                st.error("x + 1이 0보다 커야 log(x + 1)가 정의됩니다.")
        elif operation.replace(" ", "") == "cos(x)+x":
            cosx = np.cos(x_val)
            result = cosx + x_val
            st.markdown("- 계산식: \(cos(x) + x\)")
            st.markdown(f"1) \(cos(x) = {cosx:.4f}\)")
            st.markdown(f"2) \(cos(x) + x = {cosx:.4f} + {x_val:.4f} = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
        elif operation.replace(" ", "") == "x**4+2*x**2+1":
            x4 = x_val ** 4
            x2 = x_val ** 2
            result = x4 + 2 * x2 + 1
            st.markdown("- 계산식: \(x^4 + 2x^2 + 1\)")
            st.markdown(f"1) \(x^4 = {x4:.4f}\)")
            st.markdown(f"2) \(2x^2 = {2 * x2:.4f}\)")
            st.markdown(f"3) \(x^4 + 2x^2 + 1 = {x4:.4f} + {2 * x2:.4f} + 1 = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
        elif operation.replace(" ", "") == "x**2-x+1":
            x2 = x_val ** 2
            result = x2 - x_val + 1
            st.markdown("- 계산식: \(x^2 - x + 1\)")
            st.markdown(f"1) \(x^2 = {x2:.4f}\)")
            st.markdown(f"2) \(x^2 - x = {x2:.4f} - {x_val:.4f} = {(x2-x_val):.4f}\)")
            st.markdown(f"3) \(x^2 - x + 1 = {(x2-x_val):.4f} + 1 = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
        elif operation.replace(" ", "") == "sin(x)*cos(x)":
            sinx = np.sin(x_val)
            cosx = np.cos(x_val)
            result = sinx * cosx
            st.markdown("- 계산식: \(sin(x) \cdot cos(x)\)")
            st.markdown(f"1) \(sin(x) = {sinx:.4f}\)")
            st.markdown(f"2) \(cos(x) = {cosx:.4f}\)")
            st.markdown(f"3) \(sin(x) \cdot cos(x) = {sinx:.4f} \cdot {cosx:.4f} = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
        elif operation.replace(" ", "") == "exp(x)+log(x+1)":
            expx = np.exp(x_val)
            logx = np.log(x_val + 1) if x_val + 1 > 0 else None
            if logx is not None:
                result = expx + logx
                st.markdown("- 계산식: \(exp(x) + log(x + 1)\)")
                st.markdown(f"1) \(exp(x) = {expx:.4f}\)")
                st.markdown(f"2) \(log(x + 1) = {logx:.4f}\)")
                st.markdown(f"3) \(exp(x) + log(x + 1) = {expx:.4f} + {logx:.4f} = {result:.4f}\)")
                st.markdown(f"### 최종 결과값: {result:.4f}")
            else:
                st.error("x + 1이 0보다 커야 log(x + 1)가 정의됩니다.")
        elif operation.replace(" ", "") == "x**2*sin(x)":
            x2 = x_val ** 2
            sinx = np.sin(x_val)
            result = x2 * sinx
            st.markdown("- 계산식: \(x^2 \cdot sin(x)\)")
            st.markdown(f"1) \(x^2 = {x2:.4f}\)")
            st.markdown(f"2) \(sin(x) = {sinx:.4f}\)")
            st.markdown(f"3) \(x^2 \cdot sin(x) = {x2:.4f} \cdot {sinx:.4f} = {result:.4f}\)")
            st.markdown(f"### 최종 결과값: {result:.4f}")
# ...existing code...
        else:
            # 그 외에는 기본 결과만 출력
            result = eval(operation, {"__builtins__": {}}, {'x': x_val, 'sin': np.sin, 'cos': np.cos, 'exp': np.exp, 'log': np.log, 'math': math, 'np': np})
            st.markdown(f"- 계산식: `{operation}`")
            st.markdown(f"### 최종 결과값: {result}")
    except Exception as e:
        st.error(f"수식 오류: {e}")