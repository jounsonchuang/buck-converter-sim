import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 設定網頁標題與說明
st.set_page_config(page_title="Buck Converter MOSFET Loss Simulation", layout="wide")
st.title("⚡ Buck Converter MOSFET 切換損耗模擬器")
st.markdown("此工具模擬切換頻率對 MOSFET 損耗與溫度的影響。請由左側欄位調整參數。")

# ==========================================
# 1. 側邊欄：參數設定 (Sidebar Inputs)
# ==========================================
st.sidebar.header("1. 系統參數 (System)")
V_in = st.sidebar.number_input("輸入電壓 Vin (V)", value=24.0, step=1.0)
V_out = st.sidebar.number_input("輸出電壓 Vout (V)", value=12.0, step=0.5)
V_drive = st.sidebar.number_input("驅動電壓 Vdrive (V)", value=10.0, step=0.5)
I_driver = st.sidebar.number_input("Driver 驅動電流能力 (A)", value=1.0, step=0.1)

st.sidebar.header("2. MOSFET 規格 (Datasheet)")
# 為了方便輸入，將單位換算一下
rdson_mOhm = st.sidebar.number_input("Rds(on) (mΩ)", value=10.0, step=1.0)
Rdson = rdson_mOhm / 1000.0

ciss_pF = st.sidebar.number_input("Input Capacitance Ciss (pF)", value=2000.0, step=100.0)
Ciss = ciss_pF * 1e-12

Rtha = st.sidebar.number_input("熱阻 Rth_ja (°C/W)", value=40.0, step=1.0)
Tamb = st.sidebar.number_input("環境溫度 Tamb (°C)", value=25.0, step=1.0)

st.sidebar.header("3. 模擬範圍設定")
f_start_khz = st.sidebar.slider("起始頻率 (kHz)", 50, 500, 100)
f_end_khz = st.sidebar.slider("結束頻率 (kHz)", 500, 2000, 1000)

# 負載電流情境 (讓使用者輸入多個電流值用逗號分隔，或直接用預設)
current_input = st.sidebar.text_input("測試負載電流 (A) [用逗號分隔]", "2, 5, 10")
try:
    i_out_list = [float(x.strip()) for x in current_input.split(',')]
except:
    st.sidebar.error("電流格式錯誤，請輸入數字並用逗號分隔")
    i_out_list = [2.0, 5.0, 10.0]

# ==========================================
# 2. 計算邏輯
# ==========================================

# 頻率範圍陣列
f_sw_range = np.linspace(f_start_khz * 1000, f_end_khz * 1000, 100)
D = V_out / V_in # Duty Cycle

# 建立圖表
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# 計算並繪圖
for I_out in i_out_list:
    P_total_list = []
    T_j_list = []
    
    for f in f_sw_range:
        # 導通損耗 P_cond = D * I^2 * R (High Side)
        P_cond = D * (I_out ** 2) * Rdson
        
        # 切換損耗 (簡易估算)
        t_sw_estimated = (Ciss * V_drive) / I_driver 
        P_sw = 0.5 * V_in * I_out * t_sw_estimated * f
        
        # Gate 驅動損耗 (雖然通常算在 Driver，但也算入總能量消耗參考)
        # P_gate = Qg * Vgs * f (近似 Ciss * Vgs^2 * f)
        P_gate = (Ciss * V_drive) * V_drive * f
        
        P_total = P_cond + P_sw
        P_total_list.append(P_total)
        
        T_j = Tamb + (P_total * Rtha)
        T_j_list.append(T_j)
    
    # 繪製 Power Loss
    ax1.plot(f_sw_range / 1000, P_total_list, label=f'Load = {I_out}A')
    # 繪製 Temperature
    ax2.plot(f_sw_range / 1000, T_j_list, label=f'Load = {I_out}A')

# 圖表 1 設定
ax1.set_title('MOSFET Total Power Loss vs. Frequency')
ax1.set_ylabel('Power Loss (W)')
ax1.set_xlabel('Frequency (kHz)')
ax1.grid(True, which='both', linestyle='--', alpha=0.6)
ax1.legend()

# 圖表 2 設定
ax2.set_title('Junction Temperature vs. Frequency')
ax2.set_ylabel('Temperature (°C)')
ax2.set_xlabel('Frequency (kHz)')
ax2.grid(True, which='both', linestyle='--', alpha=0.6)
ax2.axhline(y=150, color='r', linestyle='--', label='Max Tj (150°C)') # 安全線
ax2.legend()

plt.tight_layout()

# ==========================================
# 3. 顯示結果於網頁
# ==========================================
st.pyplot(fig)

# 顯示詳細數據表格 (選用)
st.markdown("---")
st.subheader("📊 重點數據快照 (以 500kHz 為例)")

# 建立一個簡單的表格來顯示 500kHz 時的數值
data = []
target_freq = 500000
for I_out in i_out_list:
    P_cond = D * (I_out ** 2) * Rdson
    t_sw = (Ciss * V_drive) / I_driver 
    P_sw = 0.5 * V_in * I_out * t_sw * target_freq
    P_tot = P_cond + P_sw
    T_j = Tamb + (P_tot * Rtha)
    
    data.append({
        "負載電流 (A)": I_out,
        "導通損耗 (W)": round(P_cond, 2),
        "切換損耗 (W)": round(P_sw, 2),
        "總損耗 (W)": round(P_tot, 2),
        "預估結溫 (°C)": round(T_j, 1)
    })

st.table(data)