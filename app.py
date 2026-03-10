import streamlit as st
import pandas as pd
import os
import math

# 1. PAGE CONFIG & MASTER DATA
st.set_page_config(page_title="ระบบถอด BOQ", layout="wide")

w_map = {
    "RB6": 0.222, "RB9": 0.499, "RB12": 0.888, 
    "DB12": 0.888, "DB16": 1.578, "DB20": 2.470, 
    "DB22": 2.987, "DB25": 3.853, "DB28": 4.843, "DB32": 6.313
}
hook_90_map = {
    "DB12": 0.200, "DB16": 0.260, "DB20": 0.320, 
    "DB22": 0.350, "DB25": 0.400, "DB28": 0.550, "DB32": 0.620
}
waste_options = [0, 5, 7, 9, 11, 13, 15]
sizes = list(w_map.keys())

# 2. STATE MANAGEMENT
if "page" not in st.session_state: st.session_state.page = "home"
if "display_name" not in st.session_state: st.session_state.display_name = "หน้าหลัก"
if "calc_note" not in st.session_state: st.session_state.calc_note = ""
if "calc_csv" not in st.session_state: st.session_state.calc_csv = ""
if "breakdown_data" not in st.session_state: st.session_state.breakdown_data = []
if "breakdown_title" not in st.session_state: st.session_state.breakdown_title = ""
# ===== Project Info =====
if "proj_name"     not in st.session_state: st.session_state.proj_name     = ""
if "proj_location" not in st.session_state: st.session_state.proj_location = ""
if "proj_type"     not in st.session_state: st.session_state.proj_type     = ""
if "proj_area"     not in st.session_state: st.session_state.proj_area     = ""
if "proj_drawing"  not in st.session_state: st.session_state.proj_drawing  = ""
if "proj_item"     not in st.session_state: st.session_state.proj_item     = "งานโครงสร้าง"
if "proj_owner"    not in st.session_state: st.session_state.proj_owner    = ""
if "proj_address"  not in st.session_state: st.session_state.proj_address  = ""
if "proj_consult"  not in st.session_state: st.session_state.proj_consult  = ""
if "proj_coord"    not in st.session_state: st.session_state.proj_coord    = ""
if "proj_by"       not in st.session_state: st.session_state.proj_by       = "PROJECT PLAN"
if "proj_date"     not in st.session_state: st.session_state.proj_date     = ""
if "proj_note"     not in st.session_state: st.session_state.proj_note     = "-"
if "proj_logo"     not in st.session_state: st.session_state.proj_logo     = None

# ===== BOQ Table =====
if "boq_rows"      not in st.session_state: st.session_state.boq_rows      = []  # list of dicts

# ===== ฐานข้อมูลราคาวัสดุ (บาท/หน่วย) =====
# key = ชื่อรายการวัสดุ, value = {"unit": str, "mat": float, "labor": float}
DEFAULT_PRICES = {
    "งานดินขุด":           {"unit": "ลบ.ม.", "mat": 0,     "labor": 150},
    "ดินถม":               {"unit": "ลบ.ม.", "mat": 0,     "labor": 150},
    "ทรายหยาบ (หนา 0.05m)":{"unit": "ลบ.ม.", "mat": 600,   "labor": 200},
    "คอนกรีตหยาบ (หนา 0.05m)":{"unit":"ลบ.ม.","mat":2000,  "labor": 450},
    "คอนกรีตโครงสร้าง":    {"unit": "ลบ.ม.", "mat": 2250,  "labor": 550},
    "ไม้แบบฐานราก":        {"unit": "ตร.ม.", "mat": 200,   "labor": 100},
    "ไม้แบบตอม่อ":          {"unit": "ตร.ม.", "mat": 200,   "labor": 100},
    "RB6":  {"unit":"กก.","mat":22,"labor":5},
    "RB9":  {"unit":"กก.","mat":22,"labor":5},
    "DB10": {"unit":"กก.","mat":23,"labor":5},
    "DB12": {"unit":"กก.","mat":24,"labor":5},
    "DB16": {"unit":"กก.","mat":24,"labor":5},
    "DB20": {"unit":"กก.","mat":25,"labor":5},
    "DB25": {"unit":"กก.","mat":25,"labor":5},
    "DB28": {"unit":"กก.","mat":26,"labor":5},
    "DB32": {"unit":"กก.","mat":26,"labor":5},
    "ลวดผูกเหล็กฐานราก":   {"unit":"กก.","mat":45,"labor":0},
    "ลวดผูกเหล็กตอม่อ":    {"unit":"กก.","mat":45,"labor":0},
}
if "price_db" not in st.session_state:
    st.session_state.price_db = DEFAULT_PRICES.copy()

def go(page_key, display_name):
    st.session_state.page = page_key
    st.session_state.display_name = display_name
    st.rerun()

# 3. LAYOUT & SIDEBAR
left, center = st.columns([1, 4], gap="large")
with left:
    # ===== PEQ Logo / Title =====
    st.markdown("""
    <div style="
        background:linear-gradient(160deg,#0d3b6e,#1565a8);
        border-radius:12px; padding:14px 10px 10px 10px;
        text-align:center; margin-bottom:8px;
        box-shadow:0 3px 10px rgba(0,0,0,0.25);">
        <div style="font-size:28px;">🏗️</div>
        <div style="color:#FFD700; font-weight:900; font-size:15px; letter-spacing:2px; margin:2px 0;">PEQ</div>
        <div style="color:#cce4ff; font-size:9px; letter-spacing:0.5px; line-height:1.4;">
            Precision Engineering<br>Quantifier
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== เมนูหลัก =====
    menu_items = [
        ("home",       "🏠", "หน้าหลัก"),
        ("project",    "📋", "รายละเอียดโครงการ"),
        ("database",   "🗄️", "ฐานข้อมูลวัสดุและราคา"),
        ("boq_table",  "📊", "ตาราง BOQ"),
        ("graphs",     "📈", "ข้อมูลกราฟ"),
        ("analysis",   "🔍", "วิเคราะห์วัสดุ"),
    ]
    for page_key, icon, label in menu_items:
        is_active = st.session_state.page == page_key
        btn_style = "primary" if is_active else "secondary"
        if st.button(f"{icon} {label}", use_container_width=True,
                     type=btn_style, key=f"nav_{page_key}"):
            go(page_key, label)

    st.markdown('<hr style="margin:10px 0;border-color:#dde;">', unsafe_allow_html=True)

    # ===== Export =====
    st.markdown("""
    <div style="font-size:12px;font-weight:700;color:#555;
                letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">
        📤 Export
    </div>""", unsafe_allow_html=True)
    if st.session_state.calc_note:
        if st.button("📋 Calculation Breakdown", use_container_width=True, type="primary"):
            go("calc_breakdown", "รายละเอียดที่มาของการคำนวณ")
    else:
        st.markdown('<p style="font-size:11px;color:#999;text-align:center;">กรอกข้อมูลและกด<br>\'บันทึกลง BOQ\'<br>เพื่อเปิดปุ่ม Export</p>', unsafe_allow_html=True)

    st.markdown('<hr style="margin:10px 0;border-color:#dde;">', unsafe_allow_html=True)

with center:
    if st.session_state.page == "home":
        st.markdown('## 🏠 เลือกหมวดหมู่เริ่มต้น')
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🧱 งาน (โครงสร้าง)", use_container_width=True): go("struct_menu", "หมวดงานโครงสร้าง")
        if c2.button("🏠 งาน (สถาปัตย์)", use_container_width=True): go("arch_menu", "หมวดงานสถาปัตย์")
        if c3.button("⚡ งาน (ไฟฟ้า)", use_container_width=True): go("elec_menu", "หมวดงานไฟฟ้า")
        if c4.button("🚰 งาน (สุขาภิบาล)", use_container_width=True): go("sani_menu", "หมวดงานสุขาภิบาล")

    elif st.session_state.page == "struct_menu":
        st.markdown("### 🧱 เลือกส่วนประกอบโครงสร้าง")
        items = ["ฐานราก", "เสา คสล.", "คาน คสล.", "พื้น คสล.", "บันได คสล.", "เสาตอม่อ"]
        cols = st.columns(3)
        for i, item in enumerate(items):
            if cols[i % 3].button(item, use_container_width=True):
                if item == "ฐานราก": go("footing_menu", "เลือกประเภทฐานราก")
                else: go("generic_input", f"งาน{item}")
        if st.button("⬅️ กลับ"): go("home", "หน้าหลัก")

    elif st.session_state.page == "footing_menu":
        st.markdown("### 🦶 เลือกประเภทฐานราก")
        if st.button("🦶 ฐานรากแผ่", use_container_width=True): go("spread_calc", "เครื่องคำนวณฐานรากแผ่")
        if st.button("⬅️ กลับ"): go("struct_menu", "หมวดงานโครงสร้าง")

    elif st.session_state.page == "spread_calc":
        st.markdown(f"## 📐 {st.session_state.display_name}")
        col_img, col_res = st.columns([2.5, 1.5], gap="medium")
        
        with col_img:
            view = st.radio("มุมมอง:", ["รูปตัดฐานแผ่", "topview", "รูปตัดตอม่อ", "Topviewตอม่อ", "ตารางปลอกเสาทั้ง6แบบ"], horizontal=True)
            img_file = f"{view}.png"
            if os.path.exists(img_file): st.image(img_file, use_container_width=True)
            else: st.warning(f"⚠️ ไม่พบไฟล์ภาพ: {img_file}")

        st.markdown("---")
        st.subheader("📊 กรอกข้อมูล (Input ใต้ภาพ)")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.info("📏 ขนาดโครงสร้าง")
            A, B, C = st.number_input("A: กว้างฐาน (ม.)", 1.0), st.number_input("B: ยาวฐาน (ม.)", 1.0), st.number_input("C: หนาฐาน (ม.)", 0.3)
            is_round = st.checkbox("เสาตอม่อกลม")
            if is_round:
                dia_p = st.number_input("D: เส้นผ่าศูนย์กลางเสา (ม.)", 0.20)
                cw, cl = dia_p, dia_p
            else:
                cw, cl = st.number_input("กว้างเสา (ม.)", 0.2), st.number_input("ยาวเสา (ม.)", 0.2)
            ch = st.number_input("สูงเสา (ม.)", 1.0)
            num = st.number_input("จำนวนฐาน (ชุด)", 1)

        with c2:
            st.info("🚜 งานดิน & เผื่อคอนกรีต")
            vG, vGp = st.number_input("G: ลึกดินขุด (ม.)", 1.5), st.number_input("G': ระยะขุดเผื่อ (ม.)", 0.3)
            vD = st.number_input("ระยะหุ้ม (ม.)", 0.075, format="%.3f")
            waste_conc = st.selectbox("% เผื่อคอนกรีต", [0, 3, 5, 7, 10], index=2)

        footing_steel, pedestal_steel = {}, {}

        # ===== ระยะงอปลายเหล็กตะแกรง =====
        # จากแบบก่อสร้าง: เหล็กงอลงตามความหนาฐานราก (C) หักระยะหุ้ม
        # ยาว 1 เส้น = ระยะสุทธิ + งอ 2 ปลาย = (ด้านที่วิ่ง − 2×cover) + 2×(C − cover)
        hook_f = 2 * (C - vD)   # งอลง 2 ปลาย ตามความหนาฐานราก

        with c3:
            st.info("⛓️ ตะแกรงล่าง & ตะแกรงบน")

            ms_s, ms_w = st.selectbox("เหล็กหลักล่าง", sizes[3:], key="ms"), st.selectbox("% เผื่อหลักล่าง", waste_options, key="msw")

            ms_m = st.radio("วิธีป้อนหลักล่าง:", ["ระยะ @", "จำนวนเส้น"], key="msm")
            nm_sp = st.number_input("ระยะ @หลัก (ม.)", value=0.15, min_value=0.05, key="msp")
            nm = math.ceil((B-(vD*2))/nm_sp)+1 if ms_m=="ระยะ @" else st.number_input("จำนวนหลักล่าง", 1, value=5, key="mc")
            # ยาว 1 เส้น = ระยะสุทธิแนว A + งอลง 2 ปลาย (C−cover)×2
            l_ms = (A - (vD*2)) + hook_f
            wm = nm * l_ms * w_map[ms_s] * num * (1+ms_w/100)
            footing_steel[ms_s] = footing_steel.get(ms_s, 0) + wm
            st.caption(f"📐 ยาว/เส้น = ({A}−2×{vD}) + 2×({C}−{vD}) = **{l_ms:.3f} ม.**")

            ss_s, ss_w = st.selectbox("เหล็กรองล่าง", sizes[3:], key="ss"), st.selectbox("% เผื่อรองล่าง", waste_options, key="ssw")

            ss_m = st.radio("วิธีป้อนรองล่าง:", ["ระยะ @", "จำนวนเส้น"], key="ssm")
            ns_sp = st.number_input("ระยะ @รอง (ม.)", value=0.15, min_value=0.05, key="ssp")
            ns = math.ceil((A-(vD*2))/ns_sp)+1 if ss_m=="ระยะ @" else st.number_input("จำนวนรองล่าง", 1, value=5, key="sc")
            # ยาว 1 เส้น = ระยะสุทธิแนว B + งอลง 2 ปลาย
            # งอลงแต่ละปลาย = (C − cover − ∅ตะแกรงหลัก) เพราะวางบนตะแกรงหลัก
            ms_dia_mm = int(''.join(filter(str.isdigit, ms_s)))
            ms_dia_m  = ms_dia_mm / 1000
            hook_f_sub = 2 * (C - vD - ms_dia_m)
            l_ss = (B - (vD*2)) + hook_f_sub
            ws = ns * l_ss * w_map[ss_s] * num * (1+ss_w/100)
            footing_steel[ss_s] = footing_steel.get(ss_s, 0) + ws
            st.caption(f"📐 ยาว/เส้น = ({B}−2×{vD}) + 2×({C}−{vD}−∅หลัก{ms_dia_mm}mm) = **{l_ss:.3f} ม.**")

            if st.checkbox("มีตะแกรงบน"):
                tm_s, tm_w = st.selectbox("เหล็กหลักบน", sizes[3:], key="tms"), st.selectbox("% เผื่อหลักบน", waste_options, key="tmw")
                tnm_sp = st.number_input("ระยะ @หลักบน (ม.)", value=0.15, min_value=0.05, key="tmsp")
                tnm = math.ceil((B-(vD*2))/tnm_sp)+1
                l_tm = (A - (vD*2)) + hook_f
                wtm = tnm * l_tm * w_map[tm_s] * num * (1+tm_w/100)
                footing_steel[tm_s] = footing_steel.get(tm_s, 0) + wtm
                st.caption(f"📐 หลักบน ยาว/เส้น = **{l_tm:.3f} ม.**")

                ts_s, ts_w = st.selectbox("เหล็กรองบน", sizes[3:], key="tss"), st.selectbox("% เผื่อรองบน", waste_options, key="tsw")
                tns_sp = st.number_input("ระยะ @รองบน (ม.)", value=0.15, min_value=0.05, key="tssp")
                tns = math.ceil((A-(vD*2))/tns_sp)+1
                # ตะแกรงรองบนวางบนตะแกรงหลักบน → หัก ∅หลักบน ออกจากระยะงอทั้ง 2 ปลาย
                tm_dia_mm = int(''.join(filter(str.isdigit, tm_s)))
                tm_dia_m  = tm_dia_mm / 1000
                hook_f_ts = 2 * (C - vD - tm_dia_m)
                l_ts = (B - (vD*2)) + hook_f_ts
                wts = tns * l_ts * w_map[ts_s] * num * (1+ts_w/100)
                footing_steel[ts_s] = footing_steel.get(ts_s, 0) + wts
                st.caption(f"📐 รองบน ยาว/เส้น = ({B}−2×{vD}) + 2×({C}−{vD}−∅หลักบน{tm_dia_mm}mm) = **{l_ts:.3f} ม.**")

            if st.checkbox("มีเหล็กรัดรอบ"):
                tie_s, tie_w = st.selectbox("ขนาดเหล็กรัดรอบ", sizes[:5], key="ties"), st.selectbox("% เผื่อรัดรอบ", waste_options, key="tiew")
                n_tie_wrap = st.number_input("รัดรอบกี่เส้น", 1, 10, 2)
                # ความยาวเหล็กรัดรอบ = เส้นรอบรูปสุทธิ (หักระยะหุ้ม 2 ด้านทุกด้าน)
                l_wrap = ((A-(vD*2)) + (B-(vD*2))) * 2
                wtie = l_wrap * n_tie_wrap * w_map[tie_s] * num * (1+tie_w/100)
                footing_steel[tie_s] = footing_steel.get(tie_s, 0) + wtie
                st.caption(f"📐 รัดรอบ ยาว/เส้น = **{l_wrap:.3f} ม.**")

        with c4:
            st.info("⛓️ เหล็กเสริมตอม่อ")
            p_ms, p_mw = st.selectbox("เหล็กแกนตอม่อ", list(hook_90_map.keys()), key="pms"), st.selectbox("% เผื่อเหล็กแกน", waste_options, key="pmw")

            # ===== งอ 90° ที่ตีนเสา (Standard Hook) =====
            p_dia_mm = int(''.join(filter(str.isdigit, p_ms)))
            hook_90 = 12 * p_dia_mm / 1000   # งอ 90° = 12d (ACI 318 / วสท.)

            # ===== ระยะต่อทาบขึ้นชั้น 1 ตาม มยผ. 1103-52 =====
            st.markdown("**📏 ระยะต่อทาบขึ้นชั้น 1**")
            lap_mode = st.radio("วิธีกำหนดระยะต่อทาบ:", ["เลือกตามเกรดเหล็ก (มยผ.1103-52)", "กรอกเองเป็นเมตร"], key="lap_mode", horizontal=True)

            if lap_mode == "เลือกตามเกรดเหล็ก (มยผ.1103-52)":
                steel_grade = st.radio(
                    "เกรดเหล็ก:",
                    ["SD40 (ทาบ 36d)", "SD50 (ทาบ 45d)", "SR24 (ทาบ 40d)"],
                    key="steel_grade", horizontal=True
                )
                lap_multiplier = {"SD40 (ทาบ 36d)": 36, "SD50 (ทาบ 45d)": 45, "SR24 (ทาบ 40d)": 40}[steel_grade]
                lap_splice = lap_multiplier * p_dia_mm / 1000
                st.caption(f"📐 ต่อทาบ = {lap_multiplier}d = {lap_multiplier}×{p_dia_mm}mm = **{lap_splice*100:.1f} ซม.**")
            else:
                lap_splice = st.number_input("ระยะต่อทาบ (ม.)", value=round(36 * p_dia_mm / 1000, 3), min_value=0.10, step=0.05, key="lap_custom")
                st.caption(f"📐 ต่อทาบที่กรอก = **{lap_splice*100:.1f} ซม.**")

            # ===== ความยาวรวมเหล็กแกนตอม่อ =====
            # เหล็กแกนตอม่อวางบนตะแกรง 2 ชั้น (หลัก + รอง)
            # Top ตอม่อ → จุดงอ J = ch + C − cover − ∅ตะแกรงรอง − ∅ตะแกรงหลัก
            bot_main_dia_mm = int(''.join(filter(str.isdigit, ms_s)))   # ∅ตะแกรงหลักล่าง
            bot_sub_dia_mm  = int(''.join(filter(str.isdigit, ss_s)))   # ∅ตะแกรงรองล่าง
            bot_main_dia_m  = bot_main_dia_mm / 1000
            bot_sub_dia_m   = bot_sub_dia_mm  / 1000

            l_pedestal = ch + C - vD - bot_sub_dia_m - bot_main_dia_m
            l_main = l_pedestal + hook_90 + lap_splice

            st.caption(
                f"📐 ยาว/เส้น = ({ch}+{C}−cover{vD*100:.0f}ซม."
                f"−∅รอง{bot_sub_dia_mm}mm−∅หลัก{bot_main_dia_mm}mm) "
                f"+ งอ90°({hook_90*100:.1f}ซม.) + ทาบ({lap_splice*100:.1f}ซม.) = **{l_main:.3f} ม.**"
            )
            pmn_val = st.number_input("จำนวนแกน (เส้น)", 4)
            wp_main = pmn_val * l_main * w_map[p_ms] * num * (1 + p_mw/100)
            pedestal_steel[p_ms] = pedestal_steel.get(p_ms, 0) + wp_main

            st.write("---")
            t_type = st.selectbox("รูปแบบปลอก", ["แบบที่ 6"] if is_round else ["แบบที่ 1", "แบบที่ 2", "แบบที่ 3", "แบบที่ 4", "แบบที่ 5"])
            p_ts, p_tw = st.selectbox("เหล็กปลอก", ["RB6", "RB9", "DB12"], key="pts"), st.selectbox("% เผื่อปลอก", waste_options, key="ptw")
            p_sp = st.number_input("ระยะ @ปลอก (ม.)", value=0.15, min_value=0.05, step=0.01, key="ptsp")
            
            cw_eff = cw - (vD * 2)  # ความกว้างสุทธิ (หักระยะหุ้ม 2 ด้าน)
            cl_eff = cl - (vD * 2)  # ความยาวสุทธิ (หักระยะหุ้ม 2 ด้าน)

            # ===== ระยะงอปลาย 135° ตามมาตรฐาน มยผ. / ACI 318 =====
            # งอ 135° = 6d (ขั้นต่ำ) หรือ 10d สำหรับโซนแผ่นดินไหว
            # ดึงขนาดเส้นผ่าศูนย์กลางจากชื่อเหล็ก เช่น RB6 = 6mm, DB12 = 12mm
            tie_dia_mm = int(''.join(filter(str.isdigit, p_ts)))  # ดึงตัวเลขจากชื่อ
            tie_dia_m = tie_dia_mm / 1000                         # แปลงเป็นเมตร
            h_135 = max(10 * tie_dia_m, 0.075)  # งอ 10d ≥ 75mm (ตามมาตรฐานแผ่นดินไหว)

            # ===== คำนวณความยาวปลอกแต่ละแบบ (ถูกต้องตามหลักวิศวกรรม) =====
            # ทุกแบบ: งอ 135° ครบ 2 ปลาย (Seismic Hook) ตาม มยผ.1301

            if is_round or t_type == "แบบที่ 6":
                # แบบที่ 6: ปลอกกลม — เส้นรอบวง + งอ 135° 2 ปลาย
                l_tie = (math.pi * cw_eff) + (h_135 * 2)

            elif t_type == "แบบที่ 1":
                # แบบที่ 1: ปลอกหลักสี่เหลี่ยม
                # = เส้นรอบรูป (2กว้าง + 2ยาว) + งอ 135° 2 ปลาย
                l_tie = (cw_eff * 2) + (cl_eff * 2) + (h_135 * 2)

            elif t_type == "แบบที่ 2":
                # แบบที่ 2: ปลอกหลัก + ปลอกรอง U-bar 1 ชุด (วิ่งแนวยาว cl_eff)
                # ปลอกหลัก = เส้นรอบรูป + งอ 135° 2 ปลาย
                l_main_tie = (cw_eff * 2) + (cl_eff * 2) + (h_135 * 2)
                # ปลอกรอง U-bar = cl_eff + งอ 135° 2 ปลาย
                l_sub_tie = cl_eff + (h_135 * 2)
                l_tie = l_main_tie + l_sub_tie

            elif t_type == "แบบที่ 3":
                # แบบที่ 3: ปลอกหลัก + ปลอกรอง U-bar 2 ชุด (วิ่งขนานแนวยาว)
                # ปลอกหลัก = เส้นรอบรูป + งอ 135° 2 ปลาย
                l_main_tie = (cw_eff * 2) + (cl_eff * 2) + (h_135 * 2)
                # ปลอกรอง U-bar 2 ชุด = (cl_eff + งอ 135° 2 ปลาย) × 2
                l_sub_tie = (cl_eff + (h_135 * 2)) * 2
                l_tie = l_main_tie + l_sub_tie

            elif t_type == "แบบที่ 4":
                # แบบที่ 4: ปลอกหลัก + ปลอกเพชร (Diamond stirrup)
                # ปลอกหลัก = เส้นรอบรูป + งอ 135° 2 ปลาย
                l_main_tie = (cw_eff * 2) + (cl_eff * 2) + (h_135 * 2)
                # ปลอกเพชร = 4 ด้าน (พีทาโกรัส) + งอ 135° 2 ปลาย
                side_dia = math.sqrt((cw_eff / 2) ** 2 + (cl_eff / 2) ** 2)
                l_diamond = (side_dia * 4) + (h_135 * 2)
                l_tie = l_main_tie + l_diamond

            elif t_type == "แบบที่ 5":
                # แบบที่ 5: ปลอกหลัก + U-bar hair pin 2 ชุด (ครอบเหล็กแกนสองฝั่ง)
                # ปลอกหลัก = เส้นรอบรูป + งอ 135° 2 ปลาย
                l_main_tie = (cw_eff * 2) + (cl_eff * 2) + (h_135 * 2)
                # U-bar hair pin แต่ละชุด = cl_eff + งอ 135° 2 ปลาย (มี 2 ชุด)
                l_ubar = (cl_eff + (h_135 * 2)) * 2
                l_tie = l_main_tie + l_ubar

            n_tie = math.ceil(ch / p_sp) + 1
            wp_tie = n_tie * l_tie * w_map[p_ts] * num * (1 + p_tw/100)
            pedestal_steel[p_ts] = pedestal_steel.get(p_ts, 0) + wp_tie

            # แสดงสูตรที่ใช้คำนวณเพื่อตรวจสอบ
            with st.expander("🔍 ดูรายละเอียดการคำนวณปลอก"):
                st.write(f"**ขนาดเสาสุทธิ (หักหุ้ม):** กว้าง {cw_eff:.3f} ม. × ยาว {cl_eff:.3f} ม.")
                st.write(f"**ระยะงอ 135° (10d):** {h_135*100:.1f} ซม. (d={tie_dia_mm} มม.)")
                st.write(f"**ความยาวปลอก/ชุด:** {l_tie:.3f} ม.")
                st.write(f"**จำนวนปลอก:** {n_tie} ชุด × {num} ฐาน = {n_tie*num} ชุด")
                st.write(f"**น้ำหนักรวม:** {wp_tie:.2f} กก.")

        # LOGIC FOR RESULT & EXPORT
        vol_f  = (A * B * C) * num
        vol_p  = (math.pi * (cw/2)**2 * ch) * num if is_round else (cw * cl * ch) * num
        vol_dig = (A + vGp*2) * (B + vGp*2) * vG * num

        # ===== ดินถม =====
        # ดินถม = ดินขุด − (คอนกรีตฐาน + คอนกรีตตอม่อ + ทรายหยาบ + คอนกรีตหยาบ)
        vol_sand    = (A + 0.2) * (B + 0.2) * 0.05 * num   # ทรายหยาบ หนา 5 ซม.
        vol_lean    = (A + 0.2) * (B + 0.2) * 0.05 * num   # คอนกรีตหยาบ หนา 5 ซม.
        vol_fill    = vol_dig - vol_f - vol_p - vol_sand - vol_lean
        vol_fill    = max(vol_fill, 0)   # ไม่ให้ติดลบ
        
        # บันทึก calc_note ลง session_state ตลอดเวลา (ไม่ต้องรอกดปุ่ม)
        calc_note = f"""รายการคำนวณแบบละเอียด: {st.session_state.display_name}
1. งานดินขุด: {((A+(vGp*2))*(B+(vGp*2))*vG)*num:.2f} ลบ.ม.
2. งานคอนกรีตฐาน: {vol_f:.2f} ลบ.ม. (เผื่อ {waste_conc}% = {vol_f*(1+waste_conc/100):.2f})
3. งานคอนกรีตตอม่อ: {vol_p:.2f} ลบ.ม. (เผื่อ {waste_conc}% = {vol_p*(1+waste_conc/100):.2f})
4. เหล็กแกนตอม่อ {p_ms}: ยาว {l_main:.2f} ม./เส้น (รวมงอ J), จำนวน {pmn_val*num} เส้น
5. เหล็กปลอก {p_ts}: {t_type}, ยาว {l_tie:.3f} ม./ชุด, จำนวน {n_tie*num} ชุด
   - น้ำหนักปลอกรวม: {wp_tie:.2f} กก.
"""
        # สร้าง CSV
        csv_rows = [
            "รายการ,สูตร,ปริมาณรวม,หน่วย",
            f"งานดินขุด,({A+vGp*2:.2f}x{B+vGp*2:.2f}x{vG}) x {num} ฐาน,{((A+(vGp*2))*(B+(vGp*2))*vG)*num:.2f},ลบ.ม.",
            f"คอนกรีตฐานราก,{A}x{B}x{C} x {num} ฐาน (เผื่อ {waste_conc}%),{vol_f*(1+waste_conc/100):.2f},ลบ.ม.",
            f"คอนกรีตตอม่อ,{cw}x{cl}x{ch} x {num} ฐาน (เผื่อ {waste_conc}%),{vol_p*(1+waste_conc/100):.2f},ลบ.ม.",
        ]
        for sz, kg in footing_steel.items():
            csv_rows.append(f"เหล็กฐานราก {sz},,{kg:.2f},กก.")
        for sz, kg in pedestal_steel.items():
            csv_rows.append(f"เหล็กตอม่อ {sz},,{kg:.2f},กก.")
        calc_csv = "\n".join(csv_rows)

        st.session_state.calc_note = calc_note
        st.session_state.calc_csv = calc_csv

        # ===== คำนวณลวดผูกเหล็ก =====
        # มาตรฐาน: ลวดผูกเหล็ก No.18 (∅1.2mm) หนัก ~90ม./กก.
        # แต่ละจุดผูกใช้ลวด 2 เส้น × ~25ซม. = 0.50ม./จุด
        WIRE_M_PER_KG = 90.0    # ม./กก.
        WIRE_PER_NODE = 0.50    # ม./จุด

        # --- ลวดผูกฐานราก ---
        # จุดผูกตะแกรงล่าง = เหล็กหลักล่าง × เหล็กรองล่าง
        wire_f_nodes = nm * ns
        # ถ้ามีตะแกรงบน — ดึงค่าจาก session หรือใช้ 0 ถ้าไม่มี
        wire_f_nodes_top = 0
        try:
            wire_f_nodes_top = tnm * tns  # จะ error ถ้าไม่ได้ tick ตะแกรงบน
        except:
            wire_f_nodes_top = 0
        wire_f_total_nodes = (wire_f_nodes + wire_f_nodes_top) * int(num)
        wire_f_kg  = wire_f_total_nodes * WIRE_PER_NODE / WIRE_M_PER_KG
        wire_f_roll = math.ceil(wire_f_kg)

        # --- ลวดผูกตอม่อ ---
        # จุดผูก = จำนวนแกน × จำนวนปลอก × จำนวนฐาน
        wire_p_total_nodes = int(pmn_val) * n_tie * int(num)
        wire_p_kg  = wire_p_total_nodes * WIRE_PER_NODE / WIRE_M_PER_KG
        wire_p_roll = math.ceil(wire_p_kg)

        with col_res:
            st.subheader("📈 ผลลัพธ์แยกรายการ")
            with st.container(border=True):
                st.write(f"🚜 **งานดินขุด:** {vol_dig:.2f} ลบ.ม.")
                st.write(f"♻️ **ดินถม:** {vol_fill:.2f} ลบ.ม.")
                st.write(f"🧱 **คอนกรีตฐาน:** {vol_f*(1+waste_conc/100):.2f} ลบ.ม.")
                st.write(f"🏛️ **คอนกรีตตอม่อ:** {vol_p*(1+waste_conc/100):.2f} ลบ.ม.")
                st.divider()
                st.write("🦶 **เหล็กฐานราก:**")
                for sz, kg in footing_steel.items():
                    st.write(f"- {sz}: {kg:.2f} กก.")
                st.write(f"🪢 **ลวดผูกฐานราก:** {wire_f_kg:.2f} กก.")
                st.divider()
                st.write("🏛️ **เหล็กตอม่อ:**")
                for sz, kg in pedestal_steel.items():
                    st.write(f"- {sz}: {kg:.2f} กก.")
                st.write(f"🪢 **ลวดผูกตอม่อ:** {wire_p_kg:.2f} กก.")
                st.caption("📋 ดูที่มาสูตรทั้งหมดได้ที่ Calculation Breakdown")

            st.markdown("---")
            st.markdown("**📌 ตั้งชื่อ Mark สำหรับบันทึกลง BOQ**")
            mc1, mc2 = st.columns(2)
            with mc1:
                boq_mark_name = st.text_input(
                    "ชื่อ Mark ฐานราก (เช่น F1, F2, ฐานแผ่)",
                    value=st.session_state.get("_boq_mark_name", "F1"),
                    key="boq_mark_input"
                )
                st.session_state._boq_mark_name = boq_mark_name
            with mc2:
                boq_mark_ped = st.text_input(
                    "ชื่อ Mark เสาตอม่อ (เช่น C1, เสาตอม่อ)",
                    value=st.session_state.get("_boq_mark_ped", "C1"),
                    key="boq_ped_input"
                )
                st.session_state._boq_mark_ped = boq_mark_ped

            if st.button("💾 บันทึกลง BOQ", use_container_width=True, type="primary"):
                st.session_state._do_save_boq = True
                st.rerun()

        # สร้างข้อมูลตาราง breakdown แล้วเก็บใน session_state
        mark_name = "F1"
        footing_label = f"ฐานราก ({int(num)})"
        breakdown_rows = []

        breakdown_rows.append({"Mark / ชั้น / หมวด": "1. หมวดงานฐานราก", "รายการวัสดุ": "", "สูตรการคำนวณ (ที่มา)": "", "ปริมาณรวม": "", "หน่วย": ""})
        vol_dig = (A + vGp*2) * (B + vGp*2) * vG * num
        breakdown_rows.append({"Mark / ชั้น / หมวด": f"{mark_name}\n{footing_label}", "รายการวัสดุ": "งานดินขุด (เผื่อ 0.3m)", "สูตรการคำนวณ (ที่มา)": f"({A}+{vGp*2}) x ({B}+{vGp*2}) x ลึก {vG} x {int(num)} ฐาน", "ปริมาณรวม": f"{vol_dig:.2f}", "หน่วย": "ลบ.ม."})
        breakdown_rows.append({
            "Mark / ชั้น / หมวด": "",
            "รายการวัสดุ": "ดินถม",
            "สูตรการคำนวณ (ที่มา)": (
                f"ดินขุด({vol_dig:.2f}) − ฐาน({vol_f:.2f}) − ตอม่อ({vol_p:.2f})"
                f" − ทราย({vol_sand:.2f}) − คอนกรีตหยาบ({vol_lean:.2f})"
            ),
            "ปริมาณรวม": f"{vol_fill:.2f}", "หน่วย": "ลบ.ม."
        })
        breakdown_rows.append({"Mark / ชั้น / หมวด": "", "รายการวัสดุ": "คอนกรีตโครงสร้าง", "สูตรการคำนวณ (ที่มา)": f"กว้าง {A} x ยาว {B} x หนา {C} x {int(num)} ฐาน", "ปริมาณรวม": f"{vol_f*(1+waste_conc/100):.2f}", "หน่วย": "ลบ.ม."})
        breakdown_rows.append({"Mark / ชั้น / หมวด": "", "รายการวัสดุ": "ทรายหยาบ (หนา 0.05m)", "สูตรการคำนวณ (ที่มา)": f"({A}+0.2) x ({B}+0.2) x หนา 0.05 x {int(num)} ฐาน", "ปริมาณรวม": f"{(A+0.2)*(B+0.2)*0.05*num:.2f}", "หน่วย": "ลบ.ม."})
        breakdown_rows.append({"Mark / ชั้น / หมวด": "", "รายการวัสดุ": "คอนกรีตหยาบ (หนา 0.05m)", "สูตรการคำนวณ (ที่มา)": f"({A}+0.2) x ({B}+0.2) x หนา 0.05 x {int(num)} ฐาน", "ปริมาณรวม": f"{(A+0.2)*(B+0.2)*0.05*num:.2f}", "หน่วย": "ลบ.ม."})
        formwork_f = ((A + B) * 2) * C * num
        breakdown_rows.append({"Mark / ชั้น / หมวด": "", "รายการวัสดุ": "ไม้แบบฐานราก", "สูตรการคำนวณ (ที่มา)": f"((กว้าง {A} + ยาว {B}) x 2) x หนา {C} x {int(num)} ฐาน", "ปริมาณรวม": f"{formwork_f:.2f}", "หน่วย": "ตร.ม."})
        for sz, kg in footing_steel.items():
            breakdown_rows.append({
                "Mark / ชั้น / หมวด": "",
                "รายการวัสดุ": f"เหล็กเสริม {sz} (งอตามหนาฐาน)",
                "สูตรการคำนวณ (ที่มา)": f"จำนวนเส้น x (ระยะสุทธิ + 2×({C}−{vD})={hook_f:.3f}ม.) x {w_map[sz]} กก./ม. x {int(num)} ฐาน",
                "ปริมาณรวม": f"{kg:.2f}", "หน่วย": "กก."
            })
        # ลวดผูกฐานราก
        top_note = f" + บน {tnm}×{tns}={wire_f_nodes_top}จุด" if wire_f_nodes_top > 0 else ""
        breakdown_rows.append({
            "Mark / ชั้น / หมวด": "",
            "รายการวัสดุ": "ลวดผูกเหล็กฐานราก",
            "สูตรการคำนวณ (ที่มา)": (
                f"({nm}×{ns}={wire_f_nodes}จุดล่าง{top_note}) × {int(num)}ฐาน"
                f" × {WIRE_PER_NODE}ม./จุด ÷ {WIRE_M_PER_KG}ม./กก."
            ),
            "ปริมาณรวม": f"{wire_f_kg:.2f}", "หน่วย": "กก."
        })

        breakdown_rows.append({"Mark / ชั้น / หมวด": "2. หมวดงานตอม่อ", "รายการวัสดุ": "", "สูตรการคำนวณ (ที่มา)": "", "ปริมาณรวม": "", "หน่วย": ""})
        breakdown_rows.append({"Mark / ชั้น / หมวด": f"{mark_name}\n{footing_label}", "รายการวัสดุ": "คอนกรีตตอม่อ", "สูตรการคำนวณ (ที่มา)": (f"π x ({cw/2:.3f})² x สูง {ch} x {int(num)} ฐาน" if is_round else f"กว้าง {cw} x ยาว {cl} x สูง {ch} x {int(num)} ฐาน"), "ปริมาณรวม": f"{vol_p*(1+waste_conc/100):.2f}", "หน่วย": "ลบ.ม."})
        formwork_p = math.pi * cw * ch * num if is_round else (cw + cl) * 2 * ch * num
        breakdown_rows.append({"Mark / ชั้น / หมวด": "", "รายการวัสดุ": "ไม้แบบตอม่อ", "สูตรการคำนวณ (ที่มา)": (f"π x เส้นผ่าศูนย์กลาง {cw} x สูง {ch} x {int(num)} ฐาน" if is_round else f"({cw}+{cl}) x 2 x สูง {ch} x {int(num)} ฐาน"), "ปริมาณรวม": f"{formwork_p:.2f}", "หน่วย": "ตร.ม."})
        breakdown_rows.append({
            "Mark / ชั้น / หมวด": "",
            "รายการวัสดุ": f"เหล็กแกนตอม่อ {p_ms}",
            "สูตรการคำนวณ (ที่มา)": (
                f"{int(pmn_val)} ท่อน x "
                f"[({ch}+{C}−cover{vD*100:.0f}ซม.−∅รอง{bot_sub_dia_mm}mm−∅หลัก{bot_main_dia_mm}mm) "
                f"+ งอ90°({hook_90*100:.1f}ซม.) + ทาบ({lap_splice*100:.1f}ซม.)] "
                f"= {l_main:.3f}ม. x {w_map[p_ms]} กก./ม. x {int(num)} ฐาน"
            ),
            "ปริมาณรวม": f"{wp_main:.2f}", "หน่วย": "กก."
        })
        breakdown_rows.append({"Mark / ชั้น / หมวด": "", "รายการวัสดุ": f"เหล็กปลอก {p_ts} ({t_type})", "สูตรการคำนวณ (ที่มา)": f"{n_tie} ชุด x ยาว {l_tie:.3f} ม. x น้ำหนัก {w_map[p_ts]} x {int(num)} ฐาน", "ปริมาณรวม": f"{wp_tie:.2f}", "หน่วย": "กก."})
        # ลวดผูกตอม่อ
        breakdown_rows.append({
            "Mark / ชั้น / หมวด": "",
            "รายการวัสดุ": "ลวดผูกเหล็กตอม่อ",
            "สูตรการคำนวณ (ที่มา)": (
                f"แกน {int(pmn_val)} เส้น × ปลอก {n_tie} ชุด × {int(num)} ฐาน"
                f" × {WIRE_PER_NODE}ม./จุด ÷ {WIRE_M_PER_KG}ม./กก."
            ),
            "ปริมาณรวม": f"{wire_p_kg:.2f}", "หน่วย": "กก."
        })

        # บันทึกลง session_state
        st.session_state.breakdown_data  = breakdown_rows
        st.session_state.breakdown_title = st.session_state.display_name

        # ===== push เข้า BOQ Table เมื่อกดบันทึก =====
        if st.session_state.get("_do_save_boq"):
            st.session_state._do_save_boq = False

            f_mark = st.session_state.get("_boq_mark_name", "F1").strip() or "F1"
            p_mark = st.session_state.get("_boq_mark_ped",  "C1").strip() or "C1"

            # unique key สำหรับ replace ถ้าบันทึกซ้ำ = f_mark + p_mark
            mark_key = f"{f_mark}|{p_mark}"
            st.session_state.boq_rows = [r for r in st.session_state.boq_rows
                                         if r.get("_mark") != mark_key]

            # รายการฐานราก (section 1.1) และเสาตอม่อ (section 1.2)
            FOOTING_ITEMS  = {"งานดินขุด", "ดินถม", "ทรายหยาบ (หนา 0.05m)",
                               "คอนกรีตหยาบ (หนา 0.05m)", "คอนกรีตโครงสร้าง",
                               "ไม้แบบฐานราก", "ลวดผูกเหล็กฐานราก"}
            PEDESTAL_ITEMS = {"คอนกรีตตอม่อ", "ไม้แบบตอม่อ", "ลวดผูกเหล็กตอม่อ"}

            def _is_footing(item):
                if item in FOOTING_ITEMS: return True
                if "เหล็กเสริม" in item: return True   # เหล็กตะแกรงฐาน
                return False

            def _is_pedestal(item):
                if item in PEDESTAL_ITEMS: return True
                if "เหล็กแกนตอม่อ" in item or "เหล็กปลอก" in item: return True
                return False

            footing_rows_boq  = []
            pedestal_rows_boq = []

            for row in breakdown_rows:
                item    = row.get("รายการวัสดุ", "").strip()
                unit    = row.get("หน่วย", "").strip()
                qty_str = row.get("ปริมาณรวม", "")
                if not item or not qty_str:
                    continue
                try:
                    qty = float(qty_str)
                except:
                    continue

                entry = {"_mark": mark_key, "รายละเอียด": item,
                         "หน่วย": unit, "ปริมาณ": qty}

                if _is_pedestal(item):
                    pedestal_rows_boq.append(entry)
                else:
                    footing_rows_boq.append(entry)

            def _sec(label, row_type="section"):
                """สร้าง header row"""
                return {"_mark": mark_key, "_row_type": row_type,
                        "รายละเอียด": label, "หน่วย": "", "ปริมาณ": ""}

            new_rows = []
            if footing_rows_boq:
                new_rows.append(_sec("1. หมวดงานโครงสร้าง",  "main_header"))
                new_rows.append(_sec("1.1 หมวดงานฐานราก",    "sub_header"))
                new_rows.append(_sec(f_mark,                   "mark_header"))
                new_rows.extend(footing_rows_boq)
            if pedestal_rows_boq:
                if not footing_rows_boq:
                    new_rows.append(_sec("1. หมวดงานโครงสร้าง", "main_header"))
                new_rows.append(_sec("1.2 หมวดงานเสาตอม่อ",  "sub_header"))
                new_rows.append(_sec(p_mark,                   "mark_header"))
                new_rows.extend(pedestal_rows_boq)

            st.session_state.boq_rows.extend(new_rows)
            st.success(f"✅ บันทึก {f_mark} / {p_mark} ลง BOQ เรียบร้อย! ดูได้ที่เมนู ตาราง BOQ")


    elif st.session_state.page == "calc_breakdown":
        # ===== หน้า Calculation Breakdown =====
        st.markdown("### 📋 รายละเอียดที่มาของการคำนวณ (Calculation Breakdown)")
        st.caption(f"โครงการ: {st.session_state.breakdown_title}")

        if not st.session_state.breakdown_data:
            st.warning("⚠️ ยังไม่มีข้อมูล กรุณากรอกข้อมูลและบันทึกก่อนครับ")
            if st.button("⬅️ กลับไปกรอกข้อมูล"): go("spread_calc", "เครื่องคำนวณฐานรากแผ่")
        else:
            df_breakdown = pd.DataFrame(st.session_state.breakdown_data)

            def highlight_header(row):
                is_header = str(row["รายการวัสดุ"]) == "" and str(row["Mark / ชั้น / หมวด"]).startswith(("1.", "2.", "3.", "4.", "5.", "6."))
                if is_header:
                    return ["background-color: #dbeafe; font-weight: bold; color: #1e3a5f"] * len(row)
                return [""] * len(row)

            def highlight_qty(val):
                try:
                    float(val)
                    return "color: #1d4ed8; font-weight: bold;"
                except:
                    return ""

            styled_df = (
                df_breakdown.style
                .apply(highlight_header, axis=1)
                .applymap(highlight_qty, subset=["ปริมาณรวม"])
                .set_properties(**{"text-align": "left", "font-size": "13px", "white-space": "pre-wrap"})
                .set_table_styles([
                    {"selector": "th", "props": [("background-color", "#1e3a5f"), ("color", "white"), ("font-weight", "bold"), ("text-align", "center")]},
                    {"selector": "td", "props": [("border", "1px solid #e0e0e0"), ("padding", "6px 10px")]},
                ])
            )
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            st.markdown("---")

            # ===== สร้างไฟล์ Export จากข้อมูล breakdown จริง =====
            title = st.session_state.breakdown_title

            # 1. Excel (.csv) — ข้อมูลจาก breakdown table
            csv_data = df_breakdown.to_csv(index=False, encoding="utf-8-sig")

            # 2. Word (.html ที่เปิดใน Word ได้) — ตารางสวยงาม
            html_rows = ""
            for _, row in df_breakdown.iterrows():
                is_hdr = str(row["รายการวัสดุ"]) == "" and str(row["Mark / ชั้น / หมวด"]).startswith(("1.", "2.", "3.", "4.", "5.", "6."))
                bg = '#dbeafe' if is_hdr else 'white'
                fw = 'bold' if is_hdr else 'normal'
                qty_color = '#1d4ed8' if row["ปริมาณรวม"] not in ("", None) else 'black'
                try:
                    float(row["ปริมาณรวม"])
                    qty_style = f'color:{qty_color}; font-weight:bold;'
                except:
                    qty_style = ''
                html_rows += f"""<tr style="background:{bg}; font-weight:{fw};">
                    <td>{row["Mark / ชั้น / หมวด"]}</td>
                    <td>{row["รายการวัสดุ"]}</td>
                    <td>{row["สูตรการคำนวณ (ที่มา)"]}</td>
                    <td style="{qty_style} text-align:right;">{row["ปริมาณรวม"]}</td>
                    <td style="text-align:center;">{row["หน่วย"]}</td>
                </tr>"""

            word_html = f"""<html><head><meta charset="utf-8">
            <style>
                body {{ font-family: 'TH Sarabun New', Sarabun, sans-serif; font-size: 14pt; margin: 2cm; }}
                h2 {{ color: #1e3a5f; border-bottom: 2px solid #1e3a5f; padding-bottom: 6px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
                th {{ background: #1e3a5f; color: white; padding: 8px; text-align: center; font-size: 13pt; }}
                td {{ border: 1px solid #ccc; padding: 6px 10px; font-size: 12pt; }}
            </style></head><body>
            <h2>📋 รายละเอียดที่มาของการคำนวณ (Calculation Breakdown)</h2>
            <p><strong>โครงการ:</strong> {title}</p>
            <table>
                <thead><tr>
                    <th>Mark / ชั้น / หมวด</th>
                    <th>รายการวัสดุ</th>
                    <th>สูตรการคำนวณ (ที่มา)</th>
                    <th>ปริมาณรวม</th>
                    <th>หน่วย</th>
                </tr></thead>
                <tbody>{html_rows}</tbody>
            </table>
            </body></html>"""

            # 3. PDF-ready HTML (ใช้ print dialog)
            print_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
            <title>BOQ - {title}</title>
            <style>
                @page {{ margin: 1.5cm; }}
                body {{ font-family: 'TH Sarabun New', Sarabun, sans-serif; font-size: 13pt; }}
                h2 {{ color: #1e3a5f; border-bottom: 2px solid #1e3a5f; padding-bottom: 4px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                th {{ background: #1e3a5f; color: white; padding: 6px 8px; text-align: center; }}
                td {{ border: 1px solid #ccc; padding: 5px 8px; }}
                .hdr {{ background: #dbeafe; font-weight: bold; }}
                .qty {{ color: #1d4ed8; font-weight: bold; text-align: right; }}
            </style></head><body>
            <h2>📋 รายละเอียดที่มาของการคำนวณ (Calculation Breakdown)</h2>
            <p><strong>โครงการ:</strong> {title}</p>
            <table>
                <thead><tr>
                    <th>Mark / ชั้น / หมวด</th><th>รายการวัสดุ</th>
                    <th>สูตรการคำนวณ (ที่มา)</th><th>ปริมาณรวม</th><th>หน่วย</th>
                </tr></thead><tbody>
            """
            for _, row in df_breakdown.iterrows():
                is_hdr = str(row["รายการวัสดุ"]) == "" and str(row["Mark / ชั้น / หมวด"]).startswith(("1.", "2.", "3.", "4.", "5.", "6."))
                row_cls = "hdr" if is_hdr else ""
                try:
                    float(row["ปริมาณรวม"])
                    qty_cls = "qty"
                except:
                    qty_cls = ""
                print_html += f"""<tr class="{row_cls}">
                    <td>{row["Mark / ชั้น / หมวด"]}</td>
                    <td>{row["รายการวัสดุ"]}</td>
                    <td>{row["สูตรการคำนวณ (ที่มา)"]}</td>
                    <td class="{qty_cls}">{row["ปริมาณรวม"]}</td>
                    <td style="text-align:center;">{row["หน่วย"]}</td>
                </tr>"""
            print_html += """</tbody></table>
            <script>window.onload = function(){ window.print(); }</script>
            </body></html>"""

            # ===== ปุ่ม Export =====
            st.markdown("#### 📤 ดาวน์โหลด / Export")
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

            with col1:
                st.download_button(
                    "📗 Excel (.csv)",
                    data=csv_data,
                    file_name=f"BOQ_{title}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    "📘 Word (.html)",
                    data=word_html.encode("utf-8"),
                    file_name=f"BOQ_{title}.doc",
                    mime="application/msword",
                    use_container_width=True
                )
            with col3:
                st.download_button(
                    "📄 PDF (HTML)",
                    data=print_html.encode("utf-8"),
                    file_name=f"BOQ_{title}.html",
                    mime="text/html",
                    use_container_width=True
                )
            with col4:
                # ปุ่มปริ้น — เปิด HTML แล้วสั่งปริ้นอัตโนมัติ
                st.download_button(
                    "🖨️ พิมพ์ (เปิดแล้วปริ้นเลย)",
                    data=print_html.encode("utf-8"),
                    file_name=f"Print_BOQ_{title}.html",
                    mime="text/html",
                    use_container_width=True,
                    help="ดาวน์โหลดแล้วเปิดไฟล์ เบราว์เซอร์จะสั่งพิมพ์อัตโนมัติเลยครับ"
                )
            with col5:
                if st.button("⬅️ กลับ", use_container_width=True):
                    go("spread_calc", "เครื่องคำนวณฐานรากแผ่")

    elif st.session_state.page == "project":
        import base64, datetime, io

        st.markdown("## 📋 รายละเอียดโครงการ")

        # ===== แถวบน: แบนเนอร์โล่ง + โลโก้มุมขวา =====
        col_banner, col_logo = st.columns([4, 1], gap="small")
        with col_banner:
            st.markdown("""
            <div style="
                background:linear-gradient(135deg,#0a2d55 0%,#1565a8 60%,#1e88c8 100%);
                border-radius:10px; height:110px;
                box-shadow:0 4px 12px rgba(0,0,0,0.3);
                border-bottom:4px solid #FFD700;">
            </div>""", unsafe_allow_html=True)

        with col_logo:
            uploaded_logo = st.file_uploader(
                "📷 อัปโหลดโลโก้", type=["png","jpg","jpeg","webp"],
                key="logo_uploader", label_visibility="visible"
            )
            if uploaded_logo:
                from PIL import Image
                img = Image.open(uploaded_logo)
                img.thumbnail((220, 110), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.session_state.proj_logo = base64.b64encode(buf.getvalue()).decode()
            if st.session_state.proj_logo:
                st.markdown(
                    f'<div style="border:2px solid #1565a8;border-radius:8px;padding:6px;'
                    f'background:white;text-align:center;">'
                    f'<img src="data:image/png;base64,{st.session_state.proj_logo}" '
                    f'style="max-width:100%;max-height:90px;object-fit:contain;"></div>',
                    unsafe_allow_html=True)
                if st.button("🗑️ ลบโลโก้", use_container_width=True):
                    st.session_state.proj_logo = None
                    st.rerun()
            else:
                st.markdown(
                    '<div style="border:2px dashed #1565a8;border-radius:8px;padding:20px 8px;'
                    'text-align:center;color:#888;font-size:12px;background:#f5f9ff;">'
                    '📷<br>โลโก้บริษัท</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ===== ฟอร์มกรอกข้อมูล =====
        st.markdown("### ✏️ กรอกข้อมูลโครงการ")
        fa, fb = st.columns(2, gap="large")
        with fa:
            st.session_state.proj_name     = st.text_input("โครงการ",                value=st.session_state.proj_name)
            st.session_state.proj_location = st.text_input("สถานที่ก่อสร้าง",        value=st.session_state.proj_location)
            st.session_state.proj_type     = st.text_input("ประเภทของงานก่อสร้าง",   value=st.session_state.proj_type)
            st.session_state.proj_area     = st.text_input("พื้นที่อาคาร (ตร.ม.)",   value=st.session_state.proj_area)
            st.session_state.proj_drawing  = st.text_input("แบบเลขที่",              value=st.session_state.proj_drawing)
            st.session_state.proj_item     = st.text_input("รายการที่",              value=st.session_state.proj_item)
        with fb:
            st.session_state.proj_owner    = st.text_input("เจ้าของโครงการ",         value=st.session_state.proj_owner)
            st.session_state.proj_address  = st.text_input("ที่อยู่",                value=st.session_state.proj_address)
            st.session_state.proj_consult  = st.text_input("ที่ปรึกษาบริหารโครงการ", value=st.session_state.proj_consult)
            st.session_state.proj_coord    = st.text_input("ผู้ประสานงาน",           value=st.session_state.proj_coord)
            st.session_state.proj_by       = st.text_input("ประมาณการโดย",           value=st.session_state.proj_by)
            st.session_state.proj_date     = st.text_input("วันที่",                 value=st.session_state.proj_date or datetime.date.today().strftime("%d/%m/%Y"))
            st.session_state.proj_note     = st.text_input("อื่น ๆ",                value=st.session_state.proj_note)

        st.markdown("---")
        st.markdown("### 👁️ ตัวอย่างหน้ารายละเอียดโครงการ")

        logo_html = (
            f'<img src="data:image/png;base64,{st.session_state.proj_logo}" '
            f'style="max-height:80px;max-width:180px;object-fit:contain;">'
            if st.session_state.proj_logo else
            '<div style="border:2px dashed #ccc;padding:10px 20px;color:#bbb;font-size:12px;border-radius:6px;">LOGO</div>'
        )

        preview_html = f"""
        <style>
          .pv{{font-family:'TH Sarabun New',Sarabun,Arial,sans-serif;width:100%;}}
          .pv-top{{
            background:linear-gradient(135deg,#0a2d55 0%,#1565a8 60%,#1e88c8 100%);
            border-radius:10px 10px 0 0; height:120px;
            display:flex;align-items:center;justify-content:flex-end;
            padding:0 24px; border-bottom:5px solid #FFD700;
            box-shadow:0 4px 12px rgba(0,0,0,0.25);
          }}
          .pv-logo-box{{
            background:white;border-radius:8px;
            padding:8px 16px;min-width:160px;min-height:75px;
            display:flex;align-items:center;justify-content:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.2);
          }}
          .pv-table{{width:100%;border-collapse:collapse;font-size:16px;}}
          .pv-table .title-row td{{
            background:#b8d4f0;color:#0a2d55;
            font-size:24px;font-weight:900;text-align:center;
            padding:16px;border:1px solid #7aa3c8;letter-spacing:2px;
          }}
          .pv-table th{{
            background:#ddeeff;color:#0a2d55;font-weight:700;
            padding:10px 14px;border:1px solid #7aa3c8;width:22%;font-size:15px;
          }}
          .pv-table td{{
            padding:10px 14px;border:1px solid #b0c4de;
            color:#c0392b;font-weight:700;font-size:15px;
          }}
        </style>
        <div class="pv">
          <div class="pv-top">
            <div class="pv-logo-box">{logo_html}</div>
          </div>
          <table class="pv-table">
            <tr><td colspan="4" class="title-row">รายละเอียดโครงการ</td></tr>
            <tr><th>โครงการ</th><td colspan="3">{st.session_state.proj_name}</td></tr>
            <tr><th>สถานที่ก่อสร้าง</th><td colspan="3">{st.session_state.proj_location}</td></tr>
            <tr><th>ประเภทของงานก่อสร้าง</th><td colspan="3">{st.session_state.proj_type}</td></tr>
            <tr><th>พื้นที่อาคาร</th><td colspan="3">{st.session_state.proj_area} ตร.ม.</td></tr>
            <tr><th>แบบเลขที่</th><td colspan="3">{st.session_state.proj_drawing}</td></tr>
            <tr><th>รายการที่</th><td colspan="3">{st.session_state.proj_item}</td></tr>
            <tr>
              <th>เจ้าของโครงการ</th><td>{st.session_state.proj_owner}</td>
              <th>ที่อยู่</th><td>{st.session_state.proj_address}</td>
            </tr>
            <tr>
              <th>ที่ปรึกษาบริหารโครงการ</th><td>{st.session_state.proj_consult}</td>
              <th>ผู้ประสานงาน</th><td>{st.session_state.proj_coord}</td>
            </tr>
            <tr>
              <th>ประมาณการโดย</th><td>{st.session_state.proj_by}</td>
              <th>วันที่</th><td>{st.session_state.proj_date}</td>
            </tr>
            <tr><th>อื่น ๆ</th><td colspan="3">{st.session_state.proj_note}</td></tr>
          </table>
        </div>"""
        st.markdown(preview_html, unsafe_allow_html=True)
        st.markdown("---")
        if st.button("⬅️ กลับหน้าหลัก"): go("home", "หน้าหลัก")

    elif st.session_state.page == "boq_table":
        import pandas as pd
        st.markdown("## 📊 ตาราง BOQ — รายการสรุปตามหมวดงาน")

        raw_rows = st.session_state.boq_rows
        price_db = st.session_state.price_db

        # ===== โหมดราคา =====
        price_mode = st.radio(
            "💰 โหมดราคา:",
            ["🤖 ใช้ราคาจากฐานข้อมูล (AI)", "✏️ กรอกราคาเองในตาราง"],
            horizontal=True, key="boq_price_mode"
        )
        if price_mode == "🤖 ใช้ราคาจากฐานข้อมูล (AI)":
            ref = st.session_state.get("price_ref_date", "ปีงบประมาณ 2569")
            src = st.session_state.get("price_source", "กรมบัญชีกลาง")
            st.caption(f"📌 อ้างอิง: {src} — {ref} (แก้ไขได้ที่ 🗄️ ฐานข้อมูลวัสดุและราคา)")

        # ===== lookup ราคา =====
        def lookup_price(item):
            if item in price_db: return price_db[item]
            for k in price_db:
                if k in item: return price_db[k]
            return {"mat": 0, "labor": 0}

        # ===== Header โครงการ =====
        try:
            area_num = float(st.session_state.proj_area or 0)
        except:
            area_num = 0.0

        # คำนวณยอดรวมจาก data rows เท่านั้น
        data_only = [r for r in raw_rows if not r.get("_row_type")]
        total_mat   = sum(r["ปริมาณ"] * lookup_price(r["รายละเอียด"]).get("mat",   0) for r in data_only)
        total_labor = sum(r["ปริมาณ"] * lookup_price(r["รายละเอียด"]).get("labor", 0) for r in data_only)
        total_all   = total_mat + total_labor

        hc1, hc2, hc3 = st.columns([2, 2, 2])
        with hc1:
            st.markdown(f"**โครงการ:** {st.session_state.proj_name or '-'}")
            st.markdown(f"**เจ้าของโครงการ:** {st.session_state.proj_owner or '-'}")
            st.markdown(f"**ประมาณการโดย:** {st.session_state.proj_by or '-'}")
        with hc2:
            area_display = f"{area_num:,.2f} m²" if area_num else "-"
            st.markdown(f"""<div style="background:#455;color:#ff8a80;font-weight:bold;
                padding:10px 18px;border-radius:8px;display:inline-block;font-size:15px;
                border:2px solid #666;">Area &nbsp;{area_display}</div>""",
                unsafe_allow_html=True)
        with hc3:
            if total_all > 0:
                st.markdown(f"""
                <div style="text-align:right;font-size:13px;line-height:2.2;
                    background:#f8f9ff;border-radius:8px;padding:8px 14px;border:1px solid #dde;">
                    รวมค่าวัสดุ &nbsp;<b style="color:#c0392b">{total_mat:,.2f} บาท</b><br>
                    รวมค่าแรง &nbsp;<b style="color:#c0392b">{total_labor:,.2f} บาท</b><br>
                    <span style="font-size:14px;">รวมทั้งสิ้น &nbsp;
                    <b style="color:#0d3b6e;font-size:15px;">{total_all:,.2f} บาท</b></span>
                </div>""", unsafe_allow_html=True)
            else:
                st.caption("⚠️ ยังไม่มีราคา — กรอกราคาในฐานข้อมูล หรือเลือกโหมดกรอกเอง")

        st.markdown("---")

        if not raw_rows:
            st.info("ยังไม่มีข้อมูล — กรอกข้อมูลฐานรากแล้วกด **💾 บันทึกลง BOQ** ก่อนครับ")
        else:
            if price_mode == "🤖 ใช้ราคาจากฐานข้อมูล (AI)":
                # ===== render HTML table มีหัวข้อหลัก/รอง/Mark =====
                STYLE = """
                <style>
                .boq-wrap{font-family:'TH Sarabun New',Sarabun,Arial,sans-serif;width:100%;font-size:15px;}
                .boq-wrap table{width:100%;border-collapse:collapse;}
                .boq-wrap th{background:#0d3b6e;color:white;padding:9px 12px;text-align:center;font-size:15px;}
                .boq-wrap td{border:1px solid #ccd;padding:7px 12px;}
                .row-main{background:#1565a8;color:white;font-weight:900;font-size:16px;}
                .row-main td{border-color:#1565a8;padding:9px 14px;}
                .row-sub{background:#ddeeff;color:#0a2d55;font-weight:700;font-size:15px;}
                .row-sub td{border-color:#aac;}
                .row-mark{background:#eef5ff;color:#1565a8;font-weight:700;font-style:italic;}
                .row-mark td{border-color:#bbd;}
                .row-data td{background:#fff;}
                .row-data td:nth-child(4){text-align:right;}
                .row-data td:nth-child(5),.row-data td:nth-child(6){text-align:right;}
                .row-data td:nth-child(7),.row-data td:nth-child(8),.row-data td:nth-child(9){text-align:right;color:#c0392b;font-weight:600;}
                .num{text-align:right;}
                </style>"""

                thead = """<thead><tr>
                    <th>หมวดงาน</th><th>รายละเอียด</th><th>หน่วย</th>
                    <th>ปริมาณ</th><th>ค่าวัสดุ</th><th>ค่าแรง</th>
                    <th>รวมค่าวัสดุ</th><th>รวมค่าแรง</th><th>รวมทั้งสิ้น</th>
                </tr></thead>"""

                tbody = "<tbody>"
                for r in raw_rows:
                    rt = r.get("_row_type", "")
                    label = r.get("รายละเอียด", "")
                    if rt == "main_header":
                        tbody += f'<tr class="row-main"><td colspan="9">{label}</td></tr>'
                    elif rt == "sub_header":
                        tbody += f'<tr class="row-sub"><td colspan="9">&nbsp;&nbsp;&nbsp;{label}</td></tr>'
                    elif rt == "mark_header":
                        tbody += f'<tr class="row-mark"><td colspan="9">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▶ {label}</td></tr>'
                    else:
                        item    = r["รายละเอียด"]
                        qty     = r["ปริมาณ"]
                        p       = lookup_price(item)
                        mat_u   = p.get("mat",   0)
                        labor_u = p.get("labor", 0)
                        mat_t   = qty * mat_u
                        labor_t = qty * labor_u
                        total_t = mat_t + labor_t
                        qty_s    = f"{qty:,.2f}"
                        mat_u_s  = f"{mat_u:,.2f}"   if mat_u   > 0 else "-"
                        lab_u_s  = f"{labor_u:,.2f}" if labor_u > 0 else "-"
                        mat_t_s  = f"{mat_t:,.2f}"   if mat_t   > 0 else "-"
                        lab_t_s  = f"{labor_t:,.2f}" if labor_t > 0 else "-"
                        tot_s    = f"{total_t:,.2f}"  if total_t > 0 else "-"
                        tbody += (f'<tr class="row-data"><td></td><td>{item}</td>'
                                  f'<td style="text-align:center">{r["หน่วย"]}</td>'
                                  f'<td class="num">{qty_s}</td>'
                                  f'<td class="num">{mat_u_s}</td>'
                                  f'<td class="num">{lab_u_s}</td>'
                                  f'<td class="num">{mat_t_s}</td>'
                                  f'<td class="num">{lab_t_s}</td>'
                                  f'<td class="num">{tot_s}</td></tr>')
                tbody += "</tbody>"
                st.markdown(
                    f'<div class="boq-wrap"><table>{thead}{tbody}</table></div>',
                    unsafe_allow_html=True)

            else:
                # ===== โหมดกรอกราคาเอง — data_editor เฉพาะ data rows =====
                st.info("✏️ กรอกราคาค่าวัสดุและค่าแรงในช่องที่ต้องการ แล้วกด **💾 บันทึกราคา**")
                edit_rows = []
                for r in raw_rows:
                    if r.get("_row_type"): continue
                    item = r["รายละเอียด"]
                    p    = lookup_price(item)
                    edit_rows.append({
                        "รายละเอียด": item,
                        "หน่วย":      r["หน่วย"],
                        "ปริมาณ":     r["ปริมาณ"],
                        "ค่าวัสดุ":   p.get("mat",   0),
                        "ค่าแรง":     p.get("labor", 0),
                    })
                edited_boq = st.data_editor(
                    pd.DataFrame(edit_rows),
                    use_container_width=True, hide_index=True,
                    column_config={
                        "รายละเอียด": st.column_config.TextColumn(disabled=True, width="large"),
                        "หน่วย":      st.column_config.TextColumn(disabled=True, width="small"),
                        "ปริมาณ":     st.column_config.NumberColumn(disabled=True, format="%.2f"),
                        "ค่าวัสดุ":   st.column_config.NumberColumn("ค่าวัสดุ (บาท/หน่วย)", min_value=0, step=1, format="%.2f"),
                        "ค่าแรง":     st.column_config.NumberColumn("ค่าแรง (บาท/หน่วย)",   min_value=0, step=1, format="%.2f"),
                    }
                )
                if st.button("💾 บันทึกราคา → อัปเดตฐานข้อมูล", type="primary", use_container_width=True):
                    new_db = st.session_state.price_db.copy()
                    for _, row in edited_boq.iterrows():
                        k = str(row["รายละเอียด"]).strip()
                        if k:
                            new_db[k] = {"unit": str(row["หน่วย"]),
                                         "mat":  float(row["ค่าวัสดุ"]),
                                         "labor":float(row["ค่าแรง"])}
                    st.session_state.price_db = new_db
                    st.success("✅ อัปเดตราคาเข้าฐานข้อมูลเรียบร้อย")
                    st.rerun()

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                # Export CSV จาก data rows เท่านั้น
                csv_rows = []
                for r in raw_rows:
                    if r.get("_row_type"): continue
                    item = r["รายละเอียด"]; qty = r["ปริมาณ"]
                    p    = lookup_price(item)
                    mat_u = p.get("mat",0); lab_u = p.get("labor",0)
                    csv_rows.append({
                        "รายละเอียด": item, "หน่วย": r["หน่วย"], "ปริมาณ": qty,
                        "ค่าวัสดุ": mat_u, "ค่าแรง": lab_u,
                        "รวมค่าวัสดุ": qty*mat_u, "รวมค่าแรง": qty*lab_u,
                        "รวมทั้งสิ้น": qty*mat_u+qty*lab_u
                    })
                csv_out = pd.DataFrame(csv_rows).to_csv(index=False, encoding="utf-8-sig")
                st.download_button("📗 Export CSV", data=csv_out.encode("utf-8-sig"),
                                   file_name="BOQ_Table.csv", mime="text/csv",
                                   use_container_width=True)
            with col_b:
                if st.button("🗑️ ล้างตาราง BOQ ทั้งหมด", use_container_width=True):
                    st.session_state.boq_rows = []
                    st.rerun()

    elif st.session_state.page == "database":
        import pandas as pd
        st.markdown("## 🗄️ ฐานข้อมูลวัสดุและราคา")

        # ===== คำเตือนและแหล่งที่มา =====
        st.warning(
            "⚠️ **ราคา default เป็นราคาโดยประมาณอ้างอิงจากบัญชีราคากลางกรมบัญชีกลาง ปี 2569**  \n"
            "ราคาจริงอาจแตกต่างตามภาค/จังหวัด และเปลี่ยนแปลงตามช่วงเวลา  \n"
            "กรุณา verify ราคาที่ **[cgd.go.th](https://www.cgd.go.th)** ก่อนใช้งานจริงทุกครั้ง"
        )

        src_col1, src_col2 = st.columns(2)
        with src_col1:
            if "price_source" not in st.session_state:
                st.session_state.price_source = "บัญชีราคากลาง กรมบัญชีกลาง"
            st.session_state.price_source = st.text_input(
                "📌 แหล่งที่มาของราคา", value=st.session_state.price_source)
        with src_col2:
            if "price_ref_date" not in st.session_state:
                st.session_state.price_ref_date = "ปีงบประมาณ 2569"
            st.session_state.price_ref_date = st.text_input(
                "📅 อ้างอิงวันที่/ปี", value=st.session_state.price_ref_date)

        st.markdown("---")

        # ===== ตารางราคา =====
        st.markdown("### 💰 ตารางราคาค่าวัสดุและค่าแรง")
        st.caption("แก้ไขราคาได้โดยตรงในตาราง แล้วกด 💾 บันทึก — ราคาจะถูกนำไปคำนวณใน ตาราง BOQ อัตโนมัติ")

        price_db = st.session_state.price_db

        # จัดกลุ่มแสดงผล
        GROUPS = {
            "🚜 งานดิน": ["งานดินขุด", "ดินถม"],
            "🧱 งานคอนกรีต": ["ทรายหยาบ (หนา 0.05m)", "คอนกรีตหยาบ (หนา 0.05m)", "คอนกรีตโครงสร้าง"],
            "🪵 งานแบบหล่อ": ["ไม้แบบฐานราก", "ไม้แบบตอม่อ"],
            "⛓️ งานเหล็กเสริม": ["RB6","RB9","DB10","DB12","DB16","DB20","DB25","DB28","DB32"],
            "🪢 ลวดผูกเหล็ก": ["ลวดผูกเหล็กฐานราก", "ลวดผูกเหล็กตอม่อ"],
        }

        db_rows = []
        for grp, keys in GROUPS.items():
            for k in keys:
                v = price_db.get(k, {"unit": "-", "mat": 0, "labor": 0})
                db_rows.append({
                    "หมวด": grp,
                    "รายการวัสดุ": k,
                    "หน่วย": v["unit"],
                    "ค่าวัสดุ (บาท/หน่วย)": v["mat"],
                    "ค่าแรง (บาท/หน่วย)":   v["labor"],
                    "หมายเหตุ": "ราคา AI (โดยประมาณ)" if v["mat"] > 0 or v["labor"] > 0 else "ยังไม่มีราคา",
                })
        # รายการที่ไม่อยู่ในกลุ่ม
        known = [k for keys in GROUPS.values() for k in keys]
        for k, v in price_db.items():
            if k not in known:
                db_rows.append({
                    "หมวด": "อื่นๆ",
                    "รายการวัสดุ": k,
                    "หน่วย": v["unit"],
                    "ค่าวัสดุ (บาท/หน่วย)": v["mat"],
                    "ค่าแรง (บาท/หน่วย)":   v["labor"],
                    "หมายเหตุ": "",
                })

        df_db = pd.DataFrame(db_rows)
        edited = st.data_editor(
            df_db, use_container_width=True, hide_index=True,
            num_rows="dynamic",
            column_config={
                "หมวด":                 st.column_config.TextColumn("หมวด",       width="medium", disabled=True),
                "รายการวัสดุ":          st.column_config.TextColumn("รายการวัสดุ",width="large"),
                "หน่วย":                st.column_config.TextColumn("หน่วย",      width="small"),
                "ค่าวัสดุ (บาท/หน่วย)":st.column_config.NumberColumn("ค่าวัสดุ (บาท/หน่วย)", min_value=0, step=1, format="%.2f"),
                "ค่าแรง (บาท/หน่วย)":  st.column_config.NumberColumn("ค่าแรง (บาท/หน่วย)",   min_value=0, step=1, format="%.2f"),
                "หมายเหตุ":             st.column_config.TextColumn("หมายเหตุ",   width="medium"),
            }
        )

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("💾 บันทึกฐานข้อมูลราคา", type="primary", use_container_width=True):
                new_db = {}
                for _, row in edited.iterrows():
                    k = str(row["รายการวัสดุ"]).strip()
                    if k and k != "nan":
                        new_db[k] = {
                            "unit":  str(row["หน่วย"]),
                            "mat":   float(row["ค่าวัสดุ (บาท/หน่วย)"]),
                            "labor": float(row["ค่าแรง (บาท/หน่วย)"]),
                        }
                st.session_state.price_db = new_db
                st.success(f"✅ บันทึกราคา {len(new_db)} รายการเรียบร้อย — จะมีผลทันทีในตาราง BOQ ครับ")
        with bc2:
            if st.button("🔄 Reset กลับราคา default (AI)", use_container_width=True):
                st.session_state.price_db = DEFAULT_PRICES.copy()
                st.rerun()

        st.markdown("---")
        if st.button("⬅️ กลับ"): go("home", "หน้าหลัก")

    elif st.session_state.page in ["graphs", "analysis", "generic_input"]:
        st.markdown(f"## 📝 {st.session_state.display_name}")
        st.info("ส่วนการทำงานนี้อยู่ในแผนพัฒนาลำดับถัดไป")
        if st.button("⬅️ กลับ"): go("home", "หน้าหลัก")