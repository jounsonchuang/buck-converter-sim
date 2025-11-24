import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 設定網頁
st.set_page_config(page_title="MOSFET Ciss Analysis", layout="wide")
st.title("⚡ Buck Converter: Ciss 對損耗之影響分析")
st.markdown("此模式固定 **負載電流**，觀察 **MOSFET 輸入電容 ($C_{iss}$)** 在不同切換頻率下對損耗與溫度的影響。")

# ==========================================
# 1. 側邊欄：參數設定
# ==========================================
st.sidebar.header("1. 系統參數")
V_in = st.sidebar.number_input("輸入電壓 Vin (V)", value=24.0, step=1.0)
V_out = st.sidebar.number_input("輸出電壓 Vout (V)", value=12.0, step=0.5)
V_drive = st.sidebar.number_input("驅動電壓 Vdrive (V)", value=10.0, step=0.5)
I_driver = st.sidebar.number_input("Driver 驅動電流能力 (A)", value=1.0, step=0.1)

st.sidebar.header("2. 固定條件")
I_out = st.sidebar.number_input("固定負載電流 I_out (A)", value=10.0, step=1.0)
rdson_mOhm = st.sidebar.number_input("MOSFET Rds(on) (mΩ)", value=10.0, step=1.0)
Rdson = rdson_mOhm / 1000.0
Rtha = st.sidebar.number_input("熱阻 Rth_ja (°C/W)", value=40.0, step=1.0)
Tamb = st.sidebar.number_input("環境溫度 Tamb (°C)", value=25.0, step=1.0)

st.sidebar.header("3. 模擬變數 (X軸: Ciss)")
ciss_start_pF = st.sidebar.slider("Ciss 起始值 (pF)", 500, 2000, 500)
ciss_end_pF = st.sidebar.slider("Ciss 結束值 (pF)", 2000, 10000, 5000)

# 頻率設定 (多條曲線)
freq_input = st.sidebar.text_input("比較頻率 (kHz) [用逗號分隔]", "100, 200, 300")
try:
    freq_list_khz = [float(x.strip()) for x in freq_input.split(',')]
except:
    st.sidebar.error("頻率格式錯誤")
    freq_list_khz = [100, 200, 300]

# ==========================================
# 2. 計算邏輯
# ==========================================

# 建立 X 軸資料: Ciss 範圍 (pF) -> 轉為 Farad 進行計算
ciss_range_pF = np.linspace(ciss_start_pF, ciss_end_pF, 100)
ciss_range_F = ciss_range_pF * 1e-12

D = V_out / V_in # Duty Cycle

# 準備繪圖
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# 針對每個頻率畫一條線
for f_khz in freq_list_khz:
    f_hz = f_khz * 1000
    
    P_total_list = []
    T_j_list = []
    
    # 導通損耗 (Conduction Loss) - 與 Ciss 無關，是定值 (因為 Rdson 固定)
    # P_cond = D * I^2 * R
    P_cond = D * (I_out ** 2) * Rdson
    
    # 針對 X 軸 (Ciss) 進行迴圈
    for Ciss in ciss_range_F:
        
        # 切換損耗 (Switching Loss) - 與 Ciss 成正比
        # 估算切換時間 t = Q / I ~= (Ciss * Vdrive) / Idriver
        t_sw_estimated = (Ciss * V_drive) / I_driver 
        P_sw = 0.5 * V_in * I_out * t_sw_estimated * f_hz
        
        # Gate 驅動損耗 - 與 Ciss 成正比
        P_gate = (Ciss * V_drive) * V_drive * f_hz
        
        P_total = P_cond + P_sw + P_gate
        P_total_list.append(P_total)
        
        T_j = Tamb + (P_total * Rtha)
        T_j_list.append(T_j)
        
    # 繪圖
    ax1.plot(ciss_range_pF, P_total_list, label=f'Freq = {f_khz} kHz')
    ax2.plot(ciss_range_pF, T_j_list, label=f'Freq = {f_khz} kHz')

# --- 圖表美化 ---
# 圖 1: 損耗
ax1.set_title(f'Total Power Loss vs. Input Capacitance (Ciss) @ Load={I_out}A')
ax1.set_ylabel('Power Loss (W)')
ax1.set_xlabel('Input Capacitance Ciss (pF)')
ax1.grid(True, which='both', linestyle='--', alpha=0.6)
ax1.legend()

# 圖 2: 溫度
ax2.set_title(f'Junction Temperature vs. Input Capacitance (Ciss) @ Load={I_out}A')
ax2.set_ylabel('Temperature (°C)')
ax2.set_xlabel('Input Capacitance Ciss (pF)')
ax2.grid(True, which='both', linestyle='--', alpha=0.6)
ax2.axhline(y=150, color='r', linestyle='--', label='Max Tj (150°C)')
ax2.legend()

plt.tight_layout()

# ==========================================
# 3. 顯示結果
# ==========================================
st.pyplot(fig)

# 顯示一段簡易結論
st.info(f"""
**物理意義說明：**
在此圖中，因為 $R_{{DS(on)}}$ 設為固定，所以導通損耗是固定的基底值。
斜率代表了 **切換損耗隨電容增加的速率**。
可以看到在較高頻率 (例如 300kHz) 時，斜率更陡，代表選用低 $C_{{iss}}$ 的 MOSFET 對散熱的幫助比在低頻時更顯著。
""")
