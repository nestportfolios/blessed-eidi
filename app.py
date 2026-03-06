import streamlit as st
import random
import io
import time
import base64
import json
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

# Set page config
st.set_page_config(page_title="Blessed Eidi AI", page_icon="💸", layout="centered")

# Initialize Session State
if "step" not in st.session_state:
    st.session_state.step = 0

# Handle Navigation via Query Params
if st.query_params.get("start") == "true":
    st.session_state.step = 1
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

# Chat Agent Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_phase" not in st.session_state:
    st.session_state.agent_phase = "greeting"
if "collected_data" not in st.session_state:
    st.session_state.collected_data = {"sender": "", "names": [], "budget": 0}
if "receipt_generated" not in st.session_state:
    st.session_state.receipt_generated = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Colors
NEON_PURPLE = "#C77DFF"
NEON_GREEN = "#39FF14"
PURE_WHITE = "#FFFFFF"
DEEP_BLACK = "#0D0D0D"
GLASS_WHITE = "rgba(255, 255, 255, 0.85)"

# --- OpenAI Agent Setup ---
SYSTEM_PROMPT = """You are "Blessed Eidi AI" 🌙, a warm and festive Eidi distribution assistant.
Talk in Roman Urdu mixed with English. Be friendly, fun, and use emojis.

Your job is to collect information step by step:
1. FIRST: Ask the user's name (who is GIVING Eidi)
2. SECOND: Ask how many people they want to give Eidi to, and their names (max 15)
3. THIRD: Ask their total budget in PKR

IMPORTANT RULES:
- Collect ONE piece of info at a time
- Keep responses SHORT (2-3 lines max)
- When you have the sender name, call set_sender
- When you have ALL recipient names, call set_recipients
- When you have the budget, call set_budget
- After budget is set, call distribute_eidi. This handles the math.
- **CRITICAL**: AFTER distributing Eidi, ask the user clearly: "Kya aap inki receipt generate kar ke dikhaun?" (Do you want me to generate the receipt?)
- Wait for the user to say yes. IF they say yes, call the tool `generate_receipt`.
- NEVER make up data. Only use what the user tells you.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "set_sender",
            "description": "Set the name of the person who is giving Eidi",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Sender's name"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_recipients",
            "description": "Set the list of people who will receive Eidi",
            "parameters": {
                "type": "object",
                "properties": {
                    "names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of recipient names"
                    }
                },
                "required": ["names"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_budget",
            "description": "Set the total budget in PKR for Eidi distribution",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "integer", "description": "Total budget in PKR"}
                },
                "required": ["amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "distribute_eidi",
            "description": "Distribute the Eidi among recipients randomly. Call this after sender, recipients, and budget are all set.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_receipt",
            "description": "Generate and display the final Eidi receipt. Call this ONLY AFTER the user explicitly says YES to wanting a receipt.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def handle_tool_call(tool_name, args):
    """Process function calls from OpenAI and return results."""
    if tool_name == "set_sender":
        st.session_state.collected_data["sender"] = args["name"]
        st.session_state.user_name = args["name"]
        return f"Sender set to: {args['name']}"
    
    elif tool_name == "set_recipients":
        names = args["names"][:15]  # Max 15
        st.session_state.collected_data["names"] = names
        st.session_state.person_names = names
        st.session_state.num_of_persons = len(names)
        return f"Recipients set: {', '.join(names)}"
    
    elif tool_name == "set_budget":
        amount = max(1, args["amount"])
        st.session_state.collected_data["budget"] = amount
        st.session_state.budget = amount
        return f"Budget set to: {amount} PKR"
    
    elif tool_name == "distribute_eidi":
        n = len(st.session_state.collected_data["names"])
        budget = st.session_state.collected_data["budget"]
        if n == 0 or budget == 0:
            return "Error: Need recipients and budget first"
        if budget < n:
            return f"Error: Budget must be at least {n} PKR"
        rem = budget - n
        if n == 1:
            allocs = [budget]
        else:
            cuts = sorted([random.randint(0, rem) for _ in range(n - 1)])
            allocs = [cuts[0] + 1] + [cuts[i+1] - cuts[i] + 1 for i in range(n - 2)] + [rem - cuts[-1] + 1]
            random.shuffle(allocs)
        st.session_state.allocations = list(zip(st.session_state.collected_data["names"], allocs))
        result_lines = [f"{name}: {amt} PKR" for name, amt in st.session_state.allocations]
        return "EIDI DISTRIBUTED! \n" + "\n".join(result_lines) + "\n\nNow explicitly ask the user if they want to generate a receipt."
        
    elif tool_name == "generate_receipt":
        return "[RECEIPT_IMAGE] Receipt generation triggered successfully. Tell the user it's ready!"
    
    return "Unknown function"

def chat_with_agent(user_message):
    """Send message to OpenAI and process response with tool calling."""
    client = OpenAI(api_key=st.session_state.api_key)
    
    # Build messages
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in st.session_state.messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    
    msg = response.choices[0].message
    
    # Handle tool calls
    if msg.tool_calls:
        # Process each tool call
        tool_results = []
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            result = handle_tool_call(fn_name, fn_args)
            tool_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "content": result
            })
        
        # If we just generated the receipt, append its special message directly
        receipt_text = None
        for res in tool_results:
            if "[RECEIPT_IMAGE]" in res["content"]:
                receipt_text = res["content"]
                
        if receipt_text:
            return receipt_text
            
        # Send results back to get final response
        api_messages.append(msg.model_dump())
        api_messages.extend(tool_results)
        
        follow_up = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        follow_msg = follow_up.choices[0].message
        
        # Handle any chained tool calls
        if follow_msg.tool_calls:
            for tool_call in follow_msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                handle_tool_call(fn_name, fn_args)
            api_messages.append(follow_msg.model_dump())
            for tc in follow_msg.tool_calls:
                api_messages.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "content": handle_tool_call(tc.function.name, json.loads(tc.function.arguments))
                })
            final = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,
                tools=TOOLS,
                tool_choice="auto"
            )
            return final.choices[0].message.content or "✅"
        
        return follow_msg.content or "✅"
    
    return msg.content or "✅"


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
            /* Let Streamlit handle base background color */
            transition: background-color 0.3s ease, color 0.3s ease;
        }}

        
        /* Exceptions for elements that need specific colors */
        .whatsapp-footer span, .whatsapp-footer a {{
            color: {NEON_GREEN} !important;
        }}

        h1, h2, h3 {{
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
            border-radius: 8px !important;
            font-weight: 700;
            padding: 4px 12px;
            width: auto;
            min-width: 100px;
            min-height: 32px;
            font-size: 0.85rem;
            transition: all 0.3s ease;
            margin: 0 !important;
        }}
        .stButton>button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.15);
        }}

        div[data-testid="stInfo"] {{
            background: transparent !important;
            border-left: 8px solid {NEON_GREEN} !important;
            border-radius: 16px;
            padding: 20px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}

        .stProgress > div > div > div > div {{
            background: linear-gradient(90deg, {NEON_PURPLE}, {NEON_GREEN}) !important;
            height: 12px;
        }}

        .receipt-container {{
            background: {PURE_WHITE};
            color: {DEEP_BLACK}; /* Receipt should always look like white paper */
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
            text-align: center;
        }}

        [data-testid="stSidebar"] {{ display: none; }}

        /* WhatsApp Footer Styling */
        .whatsapp-footer {{
            position: fixed;
            left: 0;
            bottom: 0px;
            width: 100%;
            background: {DEEP_BLACK};
            color: {NEON_GREEN};
            overflow: hidden;
            padding: 4px 0;
            z-index: 1000;
            border-top: 1px solid {NEON_PURPLE};
            box-shadow: 0 -5px 10px rgba(0,0,0,0.2);
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
            font-size: 1rem;
            font-weight: 600;
        }}

        .whatsapp-footer a {{
            color: {NEON_GREEN} !important;
            text-decoration: none !important;
            border: 1px solid {NEON_GREEN};
            padding: 2px 10px;
            border-radius: 6px;
            transition: all 0.3s ease;
            display: inline-block;
            font-size: 0.85rem;
            font-weight: 600;
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
            background: rgba(128, 128, 128, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
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
            box-sizing: border-box;
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
        
        /* Padding for Main Content to avoid overlapping header and footer/chat input */
        .main .block-container {{
            padding-top: 40px;
            padding-bottom: 50px; /* Reduced to basic padding, physical spacer handles the rest */
        }}


        /* Chat input position adjustment */
        .stChatInput {{
            position: fixed !important;
            bottom: 110px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: 85% !important;
            max-width: 800px !important;
            margin: 0 !important;
            z-index: 100;
        }}

        .voice-btn.recording {{
            animation: pulse 1s infinite;
            background: linear-gradient(90deg, #ff4444, #ff6666) !important;
        }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(255,68,68,0.7); }}
            70% {{ box-shadow: 0 0 0 15px rgba(255,68,68,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255,68,68,0); }}
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
        font_path = "bahnschrift.ttf"
        font_large = ImageFont.truetype(font_path, size=85)
        
        giver_len = len(giver)
        gf_size = 35
        if giver_len > 12: gf_size = max(28, 55 - (giver_len - 12) * 2)
        font_giver = ImageFont.truetype(font_path, size=gf_size)
        
        list_f_size = 32
        if n > 10: list_f_size = 26
        if n > 15: list_f_size = 20
        font_small = ImageFont.truetype(font_path, size=list_f_size)
        
        font_med = ImageFont.truetype(font_path, size=55)
        font_tiny = ImageFont.truetype(font_path, size=28)
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

# --- STEP 1: AI CHAT AGENT ---
elif st.session_state.step == 1:
    col1, col2 = st.columns([5, 2])
    with col1:
        st.markdown("<h3 style='margin:0; padding:4px 0 0 0; font-size:1.2rem;'>🤖 Blessed Eidi AI Agent</h3>", unsafe_allow_html=True)
    with col2:
        if st.button("🔄 Reset Chat"):
            st.session_state.messages = []
            st.session_state.agent_phase = "greeting"
            st.session_state.collected_data = {"sender": "", "names": [], "budget": 0}
            st.session_state.distribution_done = False
            st.session_state.receipt_generated = False
            st.session_state.allocations = []
            st.rerun()
    
    # API Key set in backend securely
    if not st.session_state.api_key:
        try:
            st.session_state.api_key = st.secrets["OPENAI_API_KEY"]
        except Exception:
            st.error("API Key not found in .streamlit/secrets.toml!")
            st.stop()
    
    # Show greeting if no messages yet
    if not st.session_state.messages:
        greeting = "Assalam-o-Alaikum! 🌙✨ Main hoon aapka Blessed Eidi AI assistant. Aayein shuru kartay hain!\n\n**Pehle batayein, EIDI kaun de raha hai? Apna naam batayein!** 😊"
        st.session_state.messages.append({"role": "assistant", "content": greeting})
    
    # Display chat history
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if "[RECEIPT_IMAGE]" in msg["content"]:
                # Clean the message text
                clean_msg = msg["content"].replace("[RECEIPT_IMAGE]", "").strip()
                if clean_msg:
                    st.markdown(clean_msg)
                
                # Render the receipt immediately after
                with st.spinner("Receipt generate ho rahi hai... 🎨"):
                    byte_im = generate_classic_receipt(
                        st.session_state.user_name,
                        st.session_state.budget,
                        st.session_state.allocations
                    )
                    st.markdown('<div class="receipt-container">', unsafe_allow_html=True)
                    st.image(byte_im, width="stretch")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.download_button(
                        label="📥 DOWNLOAD RECEIPT (IMAGE)",
                        data=byte_im,
                        file_name=f"EIDI_Receipt_{st.session_state.user_name}_{idx}.png",
                        mime="image/png",
                        key=f"download_receipt_{idx}"
                    )
                    
                    # Portfolio promotion under each receipt
                    promo = "\n\n💼 **Agar aap ek professional Portfolio Website bnwana chahte hein to neeche SAMPLES check karein aur NestPortfolio ko contact karein!** Sirf 2500 PKR mein premium portfolio! 🚀"
                    st.markdown(promo)
            else:
                st.markdown(msg["content"])
            
    # Spacer to prevent chat hiding behind fixed input
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)

    
    # Chat text input
    user_input = None
    typed_input = st.chat_input("Type your message...")
    if typed_input:
        user_input = typed_input
    
    # Process user input (from either voice or typing)
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.spinner("Soch raha hoon... 🤔"):
            try:
                response = chat_with_agent(user_input)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                with st.chat_message("assistant"):
                    st.markdown(response)
                
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
                # Remove the user message since it failed
                st.session_state.messages.pop()


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
