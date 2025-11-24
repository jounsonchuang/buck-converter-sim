import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="MOSFET Ciss Analysis with Slope", layout="wide")
st.title("⚡ Buck Converter: Ciss Loss Slope Analysis")
st.markdown("This tool visualizes the impact of **MOSFET Input Capacitance ($C_{iss}$)** on power loss and junction temperature. The **sensitivity slopes** are calculated and marked on the plot.")

# ==========================================
# 1. Sidebar: Parameter Settings
# ==========================================
st.sidebar.header("1. System Parameters")
V_in = st.sidebar.number_input("Input Voltage Vin (V)", value=24.0, step=1.0)
V_out = st.sidebar.number_input("Output Voltage Vout (V)", value=12.0, step=0.5)
V_drive = st.sidebar.number_input("Gate Drive Voltage Vdrive (V)", value=10.0, step=0.5)
I_driver = st.sidebar.number_input("Driver Current Capability (A)", value=1.0, step=0.1)

st.sidebar.header("2. Fixed Conditions")
I_out = st.sidebar.number_input("Fixed Load Current I_out (A)", value=10.0, step=1.0)
rdson_mOhm = st.sidebar.number_input("MOSFET Rds(on) (mΩ)", value=10.0, step=1.0)
Rdson = rdson_mOhm / 1000.0
Rtha = st.sidebar.number_input("Thermal Resistance Rth_ja (°C/W)", value=40.0, step=1.0)
Tamb = st.sidebar.number_input("Ambient Temperature Tamb (°C)", value=25.0, step=1.0)

st.sidebar.header("3. Simulation Variables (X-axis: Ciss)")
ciss_start_pF = st.sidebar.slider("Ciss Start (pF)", 500, 2000, 500)
ciss_end_pF = st.sidebar.slider("Ciss End (pF)", 2000, 10000, 5000)

# Frequency Settings
freq_input = st.sidebar.text_input("Comparison Frequencies (kHz)", "100, 200, 300")
try:
    freq_list_khz = [float(x.strip()) for x in freq_input.split(',')]
except:
    st.sidebar.error("Format error. Please enter numbers separated by commas.")
    freq_list_khz = [100, 200, 300]

# ==========================================
# 2. Calculation Logic
# ==========================================

ciss_range_pF = np.linspace(ciss_start_pF, ciss_end_pF, 100)
ciss_range_F = ciss_range_pF * 1e-12
D = V_out / V_in 

# Prepare Plots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

for f_khz in freq_list_khz:
    f_hz = f_khz * 1000
    
    P_total_list = []
    T_j_list = []
    
    # Conduction Loss (Fixed because Rdson and Load are fixed)
    P_cond = D * (I_out ** 2) * Rdson
    
    for Ciss in ciss_range_F:
        # Switching Loss Estimation
        t_sw_estimated = (Ciss * V_drive) / I_driver 
        P_sw = 0.5 * V_in * I_out * t_sw_estimated * f_hz
        
        # Gate Drive Loss
        P_gate = (Ciss * V_drive) * V_drive * f_hz
        
        P_total = P_cond + P_sw + P_gate
        P_total_list.append(P_total)
        
        T_j = Tamb + (P_total * Rtha)
        T_j_list.append(T_j)

    # --- Plotting & Labeling ---
    
    # 1. Plot lines
    line, = ax1.plot(ciss_range_pF, P_total_list, label=f'{f_khz} kHz')
    ax2.plot(ciss_range_pF, T_j_list, label=f'{f_khz} kHz')
    
    # 2. Calculate Slope
    # Slope = (Y_end - Y_start) / (X_end - X_start)
    # Convert unit to "per nF" (1 nF = 1000 pF)
    delta_P = P_total_list[-1] - P_total_list[0]
    delta_T = T_j_list[-1] - T_j_list[0]
    delta_C_pF = ciss_range_pF[-1] - ciss_range_pF[0]
    
    slope_P = (delta_P / delta_C_pF) * 1000 # Unit: W/nF
    slope_T = (delta_T / delta_C_pF) * 1000 # Unit: °C/nF
    
    # 3. Add Slope Text at the end of the line
    ax1.text(ciss_range_pF[-1] + 50, P_total_list[-1], 
             f'm={slope_P:.2f} W/nF', 
             color=line.get_color(), fontsize=10, fontweight='bold', va='center')
             
    ax2.text(ciss_range_pF[-1] + 50, T_j_list[-1], 
             f'm={slope_T:.1f} °C/nF', 
             color=line.get_color(), fontsize=10, fontweight='bold', va='center')

# --- Chart Styling ---

# Extend X-axis to make room for text labels
x_padding = (ciss_end_pF - ciss_start_pF) * 0.25 
ax1.set_xlim(ciss_start_pF, ciss_end_pF + x_padding)
ax2.set_xlim(ciss_start_pF, ciss_end_pF + x_padding)

# Graph 1: Power
ax1.set_title(f'Total Power Loss (Slope in W/nF) @ Load={I_out}A')
ax1.set_ylabel('Power Loss (W)')
ax1.set_xlabel('Input Capacitance Ciss (pF)')
ax1.grid(True, which='both', linestyle='--', alpha=0.6)
ax1.legend(loc='upper left')

# Graph 2: Temperature
ax2.set_title(f'Junction Temperature (Slope in °C/nF) @ Load={I_out}A')
ax2.set_ylabel('Temperature (°C)')
ax2.set_xlabel('Input Capacitance Ciss (pF)')
ax2.grid(True, which='both', linestyle='--', alpha=0.6)
ax2.axhline(y=150, color='r', linestyle='--', label='Max Tj (150°C)')
ax2.legend(loc='upper left')

plt.tight_layout()
st.pyplot(fig)

# Explanation Box
st.success("""
**Slope Interpretation (m):**
* **W/nF**: Represents the increase in power loss (Watts) for every **1 nF (1000 pF)** increase in $C_{iss}$.
* **Significance**: A steeper slope (higher value) at higher frequencies (e.g., 300kHz) indicates that selecting a low-$C_{iss}$ MOSFET provides a much greater benefit compared to lower frequencies.
""")
