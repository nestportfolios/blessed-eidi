import streamlit as st
import random
import io
import time
import base64
from PIL import Image, ImageDraw, ImageFont

# Set page config
st.set_page_config(page_title="Blessed Eidi AI", page_icon="💸", layout="centered")

# Initialize Session State
if "step" not in st.session_state:
    st.session_state.step = 0

# Handle Navigation via Query Params (Direct button in card)
if st.query_params.get("start") == "true":
    st.session_state.step = 1
    # Clear query param to keep URL clean
    st.query_params.clear()
    st.rerun()
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "num_of_persons" not in st.session_state:
    st.session_state.num_of_persons = 1
if "person_names" not in st.session_state:
    st.session_state.person_names = [""]
if "budget" not in st.session_state:
    st.session_state.budget = 100
if "allocations" not in st.session_state:
    st.session_state.allocations = []
if "distribution_done" not in st.session_state:
    st.session_state.distribution_done = False
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# Colors
NEON_PURPLE = "#C77DFF"
NEON_GREEN = "#39FF14"
PURE_WHITE = "#FFFFFF"
DEEP_BLACK = "#0D0D0D"
GLASS_WHITE = "rgba(255, 255, 255, 0.85)"

# Navigation Functions
def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

def reset_app():
    st.session_state.step = 1
    st.session_state.distribution_done = False
    st.session_state.allocations = []
    st.session_state.user_name = ""
    st.session_state.num_of_persons = 1
    st.session_state.person_names = [""]
    st.session_state.budget = 100

# UX/UI Expert CSS
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&display=swap');
        
        * {{
            font-family: 'Outfit', sans-serif;
        }}

        .stApp {{
            background: radial-gradient(circle at 50% 50%, {PURE_WHITE} 40%, #f0f0f0 100%);
        }}

        h1, h2, h3 {{
            color: {DEEP_BLACK} !important;
            font-weight: 700 !important;
            letter-spacing: -1px;
        }}

        .stTextInput input, .stNumberInput input {{
            border-radius: 12px !important;
            border: 1px solid #ddd !important;
            padding: 12px !important;
        }}

        .stButton>button {{
            background: linear-gradient(90deg, {NEON_PURPLE} 0%, {NEON_GREEN} 100%) !important;
            color: {DEEP_BLACK} !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700;
            padding: 14px 28px;
            width: 100%;
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        }}

        div[data-testid="stInfo"] {{
            background: {GLASS_WHITE} !important;
            border-left: 8px solid {NEON_GREEN} !important;
            border-radius: 16px;
            padding: 20px !important;
        }}

        .stProgress > div > div > div > div {{
            background: linear-gradient(90deg, {NEON_PURPLE}, {NEON_GREEN}) !important;
            height: 12px;
        }}

        .receipt-container {{
            background: {PURE_WHITE};
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}

        [data-testid="stSidebar"] {{ display: none; }}

        /* WhatsApp Footer Styling */
        .whatsapp-footer {{
            position: fixed;
            left: 0;
            top: 70px;
            width: 100%;
            background: {DEEP_BLACK};
            color: {NEON_GREEN};
            overflow: hidden;
            padding: 15px 0;
            z-index: 1000;
            border-bottom: 2px solid {NEON_PURPLE};
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }}
        
        .marquee-content {{
            display: flex;
            align-items: center;
            gap: 50px;
            white-space: nowrap;
            animation: marquee 25s linear infinite;
            padding-left: 100%;
            width: fit-content;
        }}

        @keyframes marquee {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-100%); }}
        }}

        .marquee-content:hover {{
            animation-play-state: paused;
        }}

        .whatsapp-footer span {{
            font-size: 1.2rem;
            font-weight: 700;
        }}

        .whatsapp-footer a {{
            color: {NEON_GREEN} !important;
            text-decoration: none !important;
            border: 2px solid {NEON_GREEN};
            padding: 8px 20px;
            border-radius: 12px;
            transition: all 0.3s ease;
            display: inline-block;
            font-size: 1.1rem;
            font-weight: 700;
        }}
        .whatsapp-footer a.samples-btn {{
            background: {NEON_PURPLE};
            color: {DEEP_BLACK} !important;
            border-color: {NEON_PURPLE};
        }}
        .whatsapp-footer a:hover {{
            background: {NEON_GREEN};
            color: {DEEP_BLACK} !important;
            box-shadow: 0 0 20px {NEON_GREEN};
            transform: scale(1.05);
        }}
        .whatsapp-footer a.samples-btn:hover {{
            background: {PURE_WHITE};
            box-shadow: 0 0 20px {NEON_PURPLE};
        }}
        
        /* Preloader Central Card */
        .preloader-card {{
            background: {PURE_WHITE};
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.1);
            text-align: center;
            border: 1px solid rgba(199, 125, 255, 0.3);
            max-width: 500px;
            margin: 50px auto;
            animation: fadeInScale 0.8s ease-out;
            position: relative;
        }}
        @keyframes fadeInScale {{
            0% {{ opacity: 0; transform: scale(0.9); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}

        .distribute-btn-custom {{
            background: linear-gradient(90deg, {NEON_PURPLE} 0%, {NEON_GREEN} 100%) !important;
            color: {DEEP_BLACK} !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700;
            padding: 14px 28px;
            width: 100%;
            cursor: pointer;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            display: block;
            margin-top: 20px;
        }}
        .distribute-btn-custom:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
            text-decoration: none !important;
            color: {DEEP_BLACK} !important;
        }}
        
        .distribute-btn-custom:active {{
            transform: translateY(-1px);
        }}
        
        /* Padding for Main Content to avoid overlapping header and footer */
        .main .block-container {{
            padding-top: 100px;
            padding-bottom: 100px;
        }}

        /* Static Bottom Footer */
        .static-footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: {DEEP_BLACK};
            padding: 12px 0;
            text-align: center;
            z-index: 1000;
            border-top: 2px solid {NEON_PURPLE};
            box-shadow: 0 -10px 20px rgba(0,0,0,0.3);
        }}
        .static-footer a {{
            background: {NEON_PURPLE};
            color: {DEEP_BLACK} !important;
            text-decoration: none !important;
            border: none;
            padding: 10px 30px;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 700;
            transition: all 0.3s ease;
            display: inline-block;
        }}
        .static-footer a:hover {{
            background: {NEON_GREEN};
            box-shadow: 0 0 20px {NEON_GREEN};
            transform: scale(1.05);
        }}
    </style>
""", unsafe_allow_html=True)

# st.title("💸 Blessed Eidi AI")

# Progress Indicator (Only for Step 1+)
if st.session_state.step > 0:
    steps = ["Origin", "Squad", "Resources", "Mission Done"]
    st.progress(st.session_state.step / 4)
    st.write(f"**Step {st.session_state.step}: {steps[st.session_state.step-1]}**")
    st.divider()

# --- Local Receipt Generator (Neon UX) --- #
def generate_classic_receipt(giver, total, details):
    n = len(details)
    w = 800
    
    # Offsets
    y_header_end = 250
    y_giver_label = 340
    y_giver_val = y_giver_label + 55
    y_budget_label = y_giver_val + 80
    y_budget_val = y_budget_label + 50
    y_sep = y_budget_val + 80
    y_list_label = y_sep + 40
    y_list_start = y_list_label + 60
    
    line_h = 75
    if n > 8: line_h = max(45, 600 // n)
    
    list_total_h = n * line_h
    required_h = y_list_start + list_total_h + 180
    h = max(1150, required_h)
    
    p_white = (255, 255, 255)
    p_black = (13, 13, 13)
    p_purple = (199, 125, 255)
    p_green = (57, 255, 20)
    
    img = Image.new('RGB', (w + 60, h + 60), color=p_white)
    draw = ImageDraw.Draw(img)
    
    draw.rounded_rectangle([35, 35, w+15, h+15], radius=50, fill=(230, 230, 230))
    draw.rounded_rectangle([20, 20, w, h], radius=50, fill=p_white, outline=p_black, width=2)
    
    for i in range(20, w, 60): draw.line([i, 20, i, h], fill=(245, 245, 245), width=1)
    for i in range(20, h, 60): draw.line([20, i, w, i], fill=(245, 245, 245), width=1)

    draw.rounded_rectangle([20, 20, w, y_header_end], radius=50, fill=p_black)
    draw.rectangle([20, 150, w, y_header_end], fill=p_black)
    draw.line([20, y_header_end, w, y_header_end], fill=p_purple, width=5)
    
    try:
        font_large = ImageFont.load_default(size=90)
        giver_len = len(giver)
        gf_size = 35
        if giver_len > 12: gf_size = max(30, 55 - (giver_len - 12) * 2)
        font_giver = ImageFont.load_default(size=gf_size)
        list_f_size = 38
        if n > 10: list_f_size = 28
        if n > 15: list_f_size = 22
        font_small = ImageFont.load_default(size=list_f_size)
        font_med = ImageFont.load_default(size=55)
        font_tiny = ImageFont.load_default(size=30)
    except:
        font_large = font_giver = font_med = font_small = font_tiny = ImageFont.load_default()

    draw.text((w/2 + 20, 120), "EID MUBARKH", fill=p_green, anchor="mm", font=font_large)
    
    margin = 100
    draw.text((margin, y_giver_label), "EIDI Denay Walay", fill=p_black, font=font_small)
    draw.line([margin, y_giver_label+45, margin+240, y_giver_label+45], fill=p_black, width=2)
    draw.text((margin, y_giver_val), f"{giver}".upper(), fill=p_purple, font=font_giver)
    
    draw.text((margin, y_budget_label), "TOTAL BUDGET", fill=p_black, font=font_small)
    draw.line([margin, y_budget_label+45, margin+240, y_budget_label+45], fill=p_black, width=2)
    draw.text((margin, y_budget_val), f"{total} PKR", fill=p_purple, font=font_small)
    
    # draw.line([margin, y_sep, w-margin, y_sep], fill=(200, 200, 200), width=1)
    draw.text((margin, y_list_label), "EIDI Lenay Walay", fill=p_black, font=font_small)
    draw.line([margin, y_list_label+45, margin+240, y_list_label+45], fill=p_black, width=2)
    
    curr_y = y_list_start
    for i, (name, amount) in enumerate(details, 1):
        disp = (name if name else "MEMBER").upper()
        draw.text((margin + 20, curr_y), f"{i:02d}  {disp}", fill=p_purple, font=font_small)
        draw.text((w - margin, curr_y), f"{amount} PKR", fill=p_purple, font=font_small, anchor="ra")
        curr_y += line_h

    draw.rounded_rectangle([40, h-140, w-40, h-30], radius=20, fill=(250, 250, 250))
    draw.text((w/2 + 20, h-85), "YOUTUBE: HIMYANI", fill=p_green, anchor="mm", font=font_small)
    draw.text((60, h-115), "+", fill=p_green, font=font_med)
    draw.text((w-100, h-115), "+", fill=p_purple, font=font_med)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# --- STEP 0: PRELOADER ---
if st.session_state.step == 0:
    st.markdown(f"""
        <div class="preloader-card">
            <h1 style="font-size: 3rem; margin-bottom: 10px;">🌟</h1>
            <h2 style="margin-bottom: 20px;">💸 Blessed Eidi AI 💸</h2>
            <p style="color: #666; margin-bottom: 30px; font-size: 1.1rem;">
                Calculate and distribute your Eidi with our AI-powered tech agent.
            </p>
            <a href="/?start=true" target="_self" class="distribute-btn-custom" style="text-decoration: none;">
                🚀 Distribute EIDI
            </a>
        </div>
    """, unsafe_allow_html=True)

# --- STEP 1 ---
elif st.session_state.step == 1:
    st.header("👤 Who's Sending EIDI?")
    st.session_state.user_name = st.text_input("ENTER YOUR NAME", value=st.session_state.user_name, placeholder="e.g. John Doe")
    if st.button("PROCEED TO SQUAD ⚡"):
        if st.session_state.user_name: next_step(); st.rerun()
        else: st.warning("Identity Required.")

# --- STEP 2 ---
elif st.session_state.step == 2:
    st.header("👥 EIDI Lenay Walay")
    st.session_state.num_of_persons = st.number_input("How many persons do you want to give EIDI?", min_value=1, max_value=15, value=st.session_state.num_of_persons)
    p_names = []
    for i in range(int(st.session_state.num_of_persons)):
        saved = st.session_state.person_names[i] if i < len(st.session_state.person_names) else ""
        n = st.text_input(f"MEMBER {i+1}", value=saved, key=f"p_{i}", placeholder="Name")
        p_names.append(n.strip())
    st.session_state.person_names = p_names
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ PREV"): prev_step(); st.rerun()
    with col2:
        if st.button("CONFIRMED ⚡"):
            if all(st.session_state.person_names): next_step(); st.rerun()
            else: st.warning("Provide all names.")

# --- STEP 3 ---
elif st.session_state.step == 3:
    st.header("💰 Your Total Budget")
    st.session_state.budget = st.number_input("TOTAL PKR BUDGET", min_value=1, value=st.session_state.budget)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ PREV"): prev_step(); st.rerun()
    with col2:
        if st.button("DISTRIBUTE EIDI 🚀"):
            n = int(st.session_state.num_of_persons)
            if st.session_state.budget < n: st.error(f"Need {n} PKR")
            else:
                rem = st.session_state.budget-n
                if n==1: allocs=[st.session_state.budget]
                else:
                    cuts = sorted([random.randint(0,rem) for _ in range(n-1)])
                    cuts = [0]+cuts+[rem]; allocs=[(cuts[i+1]-cuts[i]+1) for i in range(n)]
                random.shuffle(allocs)
                st.session_state.allocations = list(zip(st.session_state.person_names, allocs))
                next_step(); st.snow(); st.rerun()

# --- STEP 4 ---
elif st.session_state.step == 4:
    st.header("✅ EIDI Distributed")
    st.success(f"PROCESSED FOR: {st.session_state.user_name.upper()}")
    ui_icons = ["💎", "🔋", "🦾", "📡", "🛸", "🧠", "🔥", "🚀"]
    for i, (name, amount) in enumerate(st.session_state.allocations, 1):
        ico = ui_icons[i % len(ui_icons)]
        st.info(f"**{i:02d} | {name.upper()} {ico} {amount} PKR**")
    st.divider()
    if st.button("GENERATE RECEIPT"):
        with st.spinner("Rendering technical artifact..."):
            byte_im = generate_classic_receipt(st.session_state.user_name, st.session_state.budget, st.session_state.allocations)
            st.markdown('<div class="receipt-container">', unsafe_allow_html=True)
            st.image(byte_im, width="stretch")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.download_button(
                label="📥 DOWNLOAD RECEIPT (IMAGE)",
                data=byte_im,
                file_name=f"EIDI_Receipt_{st.session_state.user_name}.png",
                mime="image/png"
            )
            st.balloons()
    if st.button("🔄 REBOOT SYSTEM"): reset_app(); st.rerun()

# --- Persistent WhatsApp Footer ---
def get_pdf_download_link(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f"data:application/pdf;base64,{b64}"

pdf_link = get_pdf_download_link("NestPortfolios.pdf")

# Calculate animation shift for persistence
duration = 25 # seconds
elapsed = time.time() - st.session_state.start_time
shift = (elapsed % duration) * 1000 # ms

st.markdown(f"""
    <div class="whatsapp-footer">
        <div class="marquee-content" id="marquee" style="animation-delay: -{shift}ms;">
            <span>Want to get DREAM JOB / SCHOLARSHIP / INCREASE YOUR CLIENTS 5X ? You need a portfolio website for just 2500 PKR! Contact us:</span>
            <a href="https://wa.me/923090757010?text=I%20want%20to%20get%20a%20portfolio%20website" target="_blank">
                💬 WhatsApps
            </a>
            <a href="{pdf_link}" download="NestPortfolios.pdf" class="samples-btn">
                📂 Check SAMPLES here
            </a>
            <span>&nbsp; &bull; &nbsp;</span>
            <span>Boost your career with a professional portfolio. Fast delivery & Premium Design!</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- Static Bottom Footer ---
st.markdown(f"""
    <div class="static-footer">
        <a href="{pdf_link}" download="NestPortfolios.pdf">
            📂 Check SAMPLES here
        </a>
    </div>
""", unsafe_allow_html=True)
