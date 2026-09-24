import streamlit as st
import pandas as pd
import io
import datetime
import requests
from supabase import create_client, Client
from streamlit_lottie import st_lottie

# ============================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================
st.set_page_config(
    page_title="Accounts Pro | Finance Management",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="auto",
)

# ------------------------------------------------------------
# GITHUB RAW PATHS FOR LOTTIE ANIMATIONS
# ------------------------------------------------------------
GITHUB_USER = "smyemon-bd"
GITHUB_REPO = "accounts-pro"
GITHUB_BRANCH = "main"

LOTTIE_LOADING_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/Loading%20Lottie%20animation.json"
LOTTIE_ERROR_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/404%20error%20page%20with%20cat.json"

@st.cache_data(show_spinner=False)
def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

loading_animation = load_lottie_url(LOTTIE_LOADING_URL)
error_animation = load_lottie_url(LOTTIE_ERROR_URL)

SUPABASE_URL = "https://bfmuxznusdblznvepumi.supabase.co"
SUPABASE_KEY = "sb_secret_EpoVYmvPa6VK3IOzeYRnwQ_OZx3-dVQ"

db_connected = True

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase.table("users").select("username").limit(1).execute()
except Exception as e:
    db_connected = False

APP_NAME = "Accounts Pro"
APP_SUBTITLE = "Finance Management System"

# ============================================================
# MOBILE-OPTIMIZED THEME SYSTEM (CSS)
# ============================================================
def apply_theme():
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC !important;
            color: #1E293B !important;
        }
        [data-testid="stAppViewContainer"] { background-color: #F8FAFC !important; }
        [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0 !important; }
        [data-testid="stSidebar"] * { color: #334155 !important; }
        [data-testid="stSidebar"] [role="radiogroup"] label { padding: 10px 14px !important; border-radius: 8px !important; margin-bottom: 6px !important; }
        .block-container { padding: 1rem !important; max-width: 100% !important; }
        .metric-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .metric-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); }
        .metric-label { color: #64748B; font-size: 13px; font-weight: 500; }
        .metric-value { color: #0F172A; font-size: 20px; font-weight: 700; margin-top: 6px; word-break: break-all; }
        .page-header { background: #FFFFFF; padding: 16px; border: 1px solid #E2E8F0; border-radius: 12px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 8px; }
        @media (min-width: 600px) { .page-header { flex-direction: row; justify-content: space-between; align-items: center; } }
        .page-header-title { font-size: 20px; font-weight: 700; color: #0F172A; }
        .page-header-subtitle { color: #64748B; font-size: 12px; margin-top: 2px; }
        .section-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 16px; overflow-x: auto; }
        .login-wrapper { display: flex; justify-content: center; align-items: center; width: 100%; padding: 20px 0; }
        .animated-logo-container { text-align: center; margin-bottom: 20px; padding: 12px; background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; }
        .animated-logo-text { font-size: 28px; font-weight: 800; color: #0F172A; margin: 0; }
        .login-title { font-size: 20px; font-weight: 700; color: #0F172A; text-align: center; margin-bottom: 4px; }
        .login-subtitle { color: #64748B; font-size: 12px; text-align: center; margin-bottom: 20px; }
        .stButton > button, .stDownloadButton > button { border-radius: 8px !important; font-weight: 500 !important; min-height: 42px !important; width: 100% !important; }
        .user-chip { background: #F1F5F9; border-radius: 20px; padding: 4px 12px; color: #334155; font-size: 12px; font-weight: 500; align-self: flex-start; }
        div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_theme()

# ============================================================
# SECURITY / AUTH HELPERS & USER SYNC
# ============================================================
def hash_password(password: str, salt: bytes | None = None) -> str:
    import hashlib, secrets, base64
    if salt is None: salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256$200000\${base64.b64encode(salt).decode()}\${base64.b64encode(digest).decode()}"

def verify_password(password: str, stored_hash: str) -> bool:
    import hashlib, hmac, base64
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256": return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception: return False

def load_users():
    if db_connected:
        try:
            response = supabase.table("users").select("*").execute()
            if response.data:
                users = {}
                for row in response.data:
                    users[str(row["username"])] = {
                        "name": row.get("name", ""),
                        "role": row.get("role", "User"),
                        "password_hash": row.get("password_hash", ""),
                        "active": bool(row.get("active", True)),
                        "created_at": str(row.get("created_at", "")),
                    }
                return users
        except Exception: pass
    return {
        "admin": {
            "name": "System Administrator",
            "role": "Admin",
            "password_hash": hash_password("password123"),
            "active": True,
            "created_at": str(datetime.date.today()),
        }
    }

def save_users(users):
    if db_connected:
        try:
            for uname, data in users.items():
                row = {
                    "username": uname,
                    "name": data["name"],
                    "role": data["role"],
                    "password_hash": data["password_hash"],
                    "active": data["active"],
                    "created_at": str(data["created_at"]),
                }
                supabase.table("users").upsert(row).execute()
        except Exception as e:
            st.error(f"User failed to sync with Cloud Database: {e}")

def validate_password(password):
    errors = []
    if len(password) < 8: errors.append("পাসওয়ার্ড অবশ্যই কমপক্ষে ৮ অক্ষরের হতে হবে।")
    if not any(c.isupper() for c in password): errors.append("কমপক্ষে একটি বড় হাতের অক্ষর (A-Z) থাকতে হবে।")
    if not any(c.islower() for c in password): errors.append("কমপক্ষে একটি ছোট হাতের অক্ষর (a-z) থাকতে হবে।")
    if not any(c.isdigit() for c in password): errors.append("কমপক্ষে একটি সংখ্যা (0-9) থাকতে হবে।")
    return errors

def validate_username(username):
    if not username: return "ইউজারনেম প্রয়োজন।"
    if len(username) < 3: return "ইউজারনেম কমপক্ষে ৩ অক্ষরের হতে হবে।"
    if " " in username: return "ইউজারনেমে স্পেস ব্যবহার করা যাবে না।"
    return None

def current_user(): return st.session_state.get("username")
def is_admin():
    username = current_user()
    users = load_users()
    return bool(username and username in users and users[username].get("role") == "Admin")

# ============================================================
# SUPABASE DATA CLOUD FUNCTIONS
# ============================================================
def load_data():
    if db_connected:
        try:
            res_sales = supabase.table("sales").select("*").execute()
            if res_sales.data:
                df = pd.DataFrame(res_sales.data)
                rename_map = {k: k.capitalize() for k in df.columns}
                if "invoice_id" in df.columns: rename_map["invoice_id"] = "Invoice_ID"
                df.rename(columns=rename_map, inplace=True)
                st.session_state.sales = df
            else:
                st.session_state.sales = pd.DataFrame(columns=["Invoice_ID", "Date", "Customer", "Service", "Amount", "Received", "Due"])

            res_exp = supabase.table("expenses").select("*").execute()
            if res_exp.data:
                df = pd.DataFrame(res_exp.data)
                df.rename(columns={k: k.capitalize() for k in df.columns}, inplace=True)
                st.session_state.expenses = df[["Date", "Head", "Amount"]]
            else:
                st.session_state.expenses = pd.DataFrame(columns=["Date", "Head", "Amount"])

            res_loans = supabase.table("loans").select("*").execute()
            if res_loans.data:
                df = pd.DataFrame(res_loans.data)
                df.rename(columns={k: k.capitalize() for k in df.columns}, inplace=True)
                st.session_state.loans = df[["Date", "Provider", "Type", "Amount"]]
            else:
                st.session_state.loans = pd.DataFrame(columns=["Date", "Provider", "Type", "Amount"])

            res_serv = supabase.table("services").select("service_name").execute()
            if res_serv.data: st.session_state.services = pd.DataFrame(res_serv.data).rename(columns={"service_name": "Service Name"})
            else: st.session_state.services = pd.DataFrame({"Service Name": ["Computer & Hardware", "Barcode Paper & Ribbon", "Printer", "CC Camera"]})

            res_cust = supabase.table("customers").select("customer_name").execute()
            if res_cust.data: st.session_state.customers = pd.DataFrame(res_cust.data).rename(columns={"customer_name": "Customer Name"})
            else: st.session_state.customers = pd.DataFrame({"Customer Name": ["Default Customer"]})

            res_heads = supabase.table("expense_heads").select("head_name").execute()
            if res_heads.data: st.session_state.expense_heads = pd.DataFrame(res_heads.data).rename(columns={"head_name": "Head Name"})
            else: st.session_state.expense_heads = pd.DataFrame({"Head Name": ["Office Rent", "Utility Bill", "Salary", "Marketing", "Other"]})

            res_comp = supabase.table("company_info").select("*").eq("id", 1).execute()
            if res_comp.data:
                c = res_comp.data[0]
                st.session_state.company_info = {
                    "Company Name": c.get("company_name", "My Business Ltd."),
                    "Mobile": c.get("mobile", "017XXXXXXXX"),
                    "Address": c.get("address", "Dhaka, Bangladesh"),
                    "Invoice Prefix": c.get("invoice_prefix", "INV")
                }
            else:
                st.session_state.company_info = {"Company Name": "My Business Ltd.", "Mobile": "017XXXXXXXX", "Address": "Dhaka, Bangladesh", "Invoice Prefix": "INV"}
            return
        except Exception as e:
            pass

    if "sales" not in st.session_state: st.session_state.sales = pd.DataFrame(columns=["Invoice_ID", "Date", "Customer", "Service", "Amount", "Received", "Due"])
    if "expenses" not in st.session_state: st.session_state.expenses = pd.DataFrame(columns=["Date", "Head", "Amount"])
    if "loans" not in st.session_state: st.session_state.loans = pd.DataFrame(columns=["Date", "Provider", "Type", "Amount"])
    if "services" not in st.session_state: st.session_state.services = pd.DataFrame({"Service Name": ["Computer & Hardware"]})
    if "customers" not in st.session_state: st.session_state.customers = pd.DataFrame({"Customer Name": ["Default Customer"]})
    if "expense_heads" not in st.session_state: st.session_state.expense_heads = pd.DataFrame({"Head Name": ["Office Rent", "Other"]})
    if "company_info" not in st.session_state: st.session_state.company_info = {"Company Name": "My Business Ltd.", "Mobile": "017XXXXXXXX", "Address": "Dhaka", "Invoice Prefix": "INV"}

def sync_row_to_supabase(table_name: str, payload: dict):
    if db_connected:
        try:
            if loading_animation:
                with st.spinner("ডাটা ক্লাউডে সিঙ্ক হচ্ছে..."):
                    st_lottie(loading_animation, height=80, key=f"sync_load_{datetime.datetime.now().timestamp()}")
            supabase.table(table_name).insert(payload).execute()
            return True
        except Exception as e:
            st.error(f"ক্লাউডে ডাটা রেকর্ড করা সম্ভব হয়নি: {e}")
            return False
    else:
        st.error("ডাটাবেজ কানেকশন উপলব্ধ না থাকায় ডাটা সেভ করা সম্ভব হয়নি।")
        return False

def export_to_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        st.session_state.sales.to_excel(writer, sheet_name="Sales", index=False)
        st.session_state.expenses.to_excel(writer, sheet_name="Expenses", index=False)
        st.session_state.loans.to_excel(writer, sheet_name="Loans", index=False)
        st.session_state.services.to_excel(writer, sheet_name="Services", index=False)
        st.session_state.customers.to_excel(writer, sheet_name="Customers", index=False)
        st.session_state.expense_heads.to_excel(writer, sheet_name="ExpenseHeads", index=False)
        pd.DataFrame([st.session_state.company_info]).to_excel(writer, sheet_name="CompanyInfo", index=False)
    return output.getvalue()

def page_header(title, subtitle=""):
    st.markdown(
        f"""
        <div class="page-header">
            <div>
                <div class="page-header-title">{title}</div>
                <div class="page-header-subtitle">{subtitle}</div>
            </div>
            <div class="user-chip">👤 {current_user()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# LOGIN & SESSIONS
# ============================================================
defaults = {"logged_in": False, "username": None, "previous_menu": "Dashboard"}
for key, value in defaults.items():
    if key not in st.session_state: st.session_state[key] = value

def render_login():
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="animated-logo-container"><h1 class="animated-logo-text">Accounts Pro</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Sign In</div>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="e.g. admin")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
        
        if submitted:
            u_clean = username.strip().lower()
            
            # Master Emergency Login Credentials
            MASTER_USER = "supperadmin"
            MASTER_PASS = "Emergency@2026"
            
            if not username or not password:
                st.error("দয়া করে ইউজারনেম এবং পাসওয়ার্ড দুটিই ইনপুট দিন।")
            elif u_clean == MASTER_USER and password == MASTER_PASS:
                st.session_state.logged_in = True
                st.session_state.username = MASTER_USER
                st.success("মাস্টার রিকভারি লগইন সফল হয়েছে!")
                st.rerun()
            else:
                users = load_users()
                user = users.get(u_clean)
                if not user or not user.get("active", True) or not verify_password(password, user["password_hash"]):
                    st.error("ভুল ইউজারনেম অথবা পাসওয়ার্ড!")
                else:
                    st.session_state.logged_in = True
                    st.session_state.username = u_clean
                    st.rerun()

# ============================================================
# MAIN APPLICATION ENGINE
# ============================================================
def render_main_app():
    load_data()
    
    if "Invoice_ID" not in st.session_state.sales.columns:
        st.session_state.sales.insert(0, "Invoice_ID", [f"TRX-{1000+i}" for i in range(len(st.session_state.sales))])
        
    with st.sidebar:
        st.markdown(f"""<div style='padding:5px 0;'><h2 style='margin:0;'>💼 {APP_NAME}</h2></div>""", unsafe_allow_html=True)
        
        menu_items = ["Dashboard", "Services", "Customers", "Company & Invoice", "Sales & Customer Ledger", "Invoice Generator", "Expenses & Loans", "Profit & Loss", "Profile & Security"]
        if is_admin() or current_user() == "supperadmin": menu_items.append("User Management")
            
        menu = st.radio("Navigation", menu_items, label_visibility="collapsed")
        
        if "previous_menu" in st.session_state and st.session_state.previous_menu != menu:
            st.session_state.previous_menu = menu
            if loading_animation:
                st_lottie(loading_animation, height=100, speed=1.8, key=f"menu_switch_{menu}")
            
        st.markdown("---")
        excel_data = export_to_excel()
        st.download_button("Download Excel Backup", data=excel_data, file_name=f"financial_backup_{datetime.date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        if st.button("Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
            
    if not db_connected:
        st.error("GitHub, Supabase অথবা Streamlit নেটওয়ার্ক কানেকশন সমস্যা! ক্লাউডের সাথে যোগাযোগ বিচ্ছিন্ন হয়েছে।")
        if error_animation:
            st_lottie(error_animation, height=180, key="network_error_cat_anim")
            
    if menu == "Dashboard":
        page_header("Dashboard", "Financial parameters overview.")
        total_sales = pd.to_numeric(st.session_state.sales["Amount"], errors="coerce").fillna(0).sum()
        total_received = pd.to_numeric(st.session_state.sales["Received"], errors="coerce").fillna(0).sum()
        total_due = pd.to_numeric(st.session_state.sales["Due"], errors="coerce").fillna(0).sum()
        total_expense = pd.to_numeric(st.session_state.expenses["Amount"], errors="coerce").fillna(0).sum()
        
        loan_df = st.session_state.loans
        loan_taken = pd.to_numeric(loan_df[loan_df["Type"] == "Loan Taken"]["Amount"], errors="coerce").fillna(0).sum() if not loan_df.empty else 0
        loan_paid = pd.to_numeric(loan_df[loan_df["Type"] == "Loan Paid"]["Amount"], errors="coerce").fillna(0).sum() if not loan_df.empty else 0
        current_loan_due = loan_taken - loan_paid
        available_cash = (total_received + loan_taken) - (total_expense + loan_paid)
        
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-card"><div class="metric-label">Total Sales</div><div class="metric-value">{total_sales:,.2f} ৳</div></div>
                <div class="metric-card"><div class="metric-label">Cash Received</div><div class="metric-value">{total_received:,.2f} ৳</div></div>
                <div class="metric-card"><div class="metric-label">Outstanding Due</div><div class="metric-value">{total_due:,.2f} ৳</div></div>
                <div class="metric-card"><div class="metric-label">Total Expenses</div><div class="metric-value">{total_expense:,.2f} ৳</div></div>
                <div class="metric-card" style="background:#F0FDF4; border-color:#BBF7D0;"><div class="metric-label" style="color:#166534;">Available Cash</div><div class="metric-value" style="color:#166534;">{available_cash:,.2f} ৳</div></div>
            </div>
            """, unsafe_allow_html=True
        )
        st.subheader("Recent Activity Ledger")
        st.dataframe(st.session_state.sales.tail(10), use_container_width=True, hide_index=True)
            
    elif menu == "Services":
        page_header("Services Directory")
        with st.form("service_form", clear_on_submit=True):
            new_service = st.text_input("Service name")
            if st.form_submit_button("Add Service", type="primary"):
                if new_service.strip() and not (new_service.strip() in st.session_state.services["Service Name"].values):
                    if sync_row_to_supabase("services", {"service_name": new_service.strip()}):
                        st.success("Sync Complete.")
                        st.rerun()
        st.dataframe(st.session_state.services, use_container_width=True, hide_index=True)
        
    elif menu == "Customers":
        page_header("Customers Directory")
        with st.form("customer_form", clear_on_submit=True):
            new_customer = st.text_input("Customer name")
            if st.form_submit_button("Add Customer", type="primary"):
                if new_customer.strip() and not (new_customer.strip() in st.session_state.customers["Customer Name"].values):
                    if sync_row_to_supabase("customers", {"customer_name": new_customer.strip()}):
                        st.success("Customer Registered.")
                        st.rerun()
        st.dataframe(st.session_state.customers, use_container_width=True, hide_index=True)
        
    elif menu == "Company & Invoice":
        page_header("Company & Invoice Config")
        with st.form("company_form"):
            c_name = st.text_input("Company name", st.session_state.company_info.get("Company Name"))
            c_phone = st.text_input("Mobile number", st.session_state.company_info.get("Mobile"))
            c_address = st.text_area("Address", st.session_state.company_info.get("Address"))
            c_prefix = st.text_input("Invoice prefix", st.session_state.company_info.get("Invoice Prefix"))
            
            if st.form_submit_button("Update Configuration", type="primary"):
                payload = {"id": 1, "company_name": c_name.strip(), "mobile": c_phone.strip(), "address": c_address.strip(), "invoice_prefix": c_prefix.strip()}
                if db_connected:
                    try:
                        supabase.table("company_info").upsert(payload).execute()
                        st.success("Configurations updated cloud-side.")
                        st.rerun()
                    except Exception as e: st.error(f"Cloud write error: {e}")
                    
    elif menu == "Sales & Customer Ledger":
        page_header("Sales & Customer Ledger")
        tab_new, tab_due = st.tabs(["New Sale", "Due Collection"])
        
        with tab_new:
            with st.form("sales_form", clear_on_submit=True):
                date = st.date_input("Date", datetime.date.today())
                customer = st.selectbox("Customer Lookup", st.session_state.customers["Customer Name"].tolist())
                service = st.selectbox("Service Head", st.session_state.services["Service Name"].tolist())
                amount = st.number_input("Sale Value", min_value=0.0, step=100.0)
                received = st.number_input("Cash Collected", min_value=0.0, step=100.0)
                
                if st.form_submit_button("Commit Entry", type="primary"):
                    if amount >= received > 0 or amount > 0:
                        due = amount - received
                        prefix = st.session_state.company_info.get("Invoice Prefix", "INV")
                        inv_id = f"{prefix}-{datetime.date.today().strftime('%y%m%d')}-{len(st.session_state.sales)+101}"
                        
                        payload = {"invoice_id": inv_id, "date": str(date), "customer": customer, "service": service, "amount": float(amount), "received": float(received), "due": float(due)}
                        if sync_row_to_supabase("sales", payload):
                            st.success("Transactional ledger saved.")
                            st.rerun()
                            
        with tab_due:
            sales_df = st.session_state.sales
            if not sales_df.empty:
                due_customers = [c for c in sales_df["Customer"].unique() if (pd.to_numeric(sales_df[sales_df["Customer"] == c]["Amount"], errors='coerce').sum() - pd.to_numeric(sales_df[sales_df["Customer"] == c]["Received"], errors='coerce').sum()) > 0]
                if due_customers:
                    selected_customer = st.selectbox("Select Customer to Clear Due", due_customers)
                    cust_data = sales_df[sales_df["Customer"] == selected_customer]
                    current_due = pd.to_numeric(cust_data["Amount"], errors="coerce").sum() - pd.to_numeric(cust_data["Received"], errors="coerce").sum()
                    st.warning(f"Total Outstanding: {current_due:,.2f} ৳")
                    
                    with st.form("due_payment_form", clear_on_submit=True):
                        pay_date = st.date_input("Collection Date")
                        pay_amount = st.number_input("Collected Amount", min_value=0.0, max_value=float(current_due), step=500.0)
                        
                        if st.form_submit_button("Record Recovery", type="primary"):
                            inv_id = f"PAY-{datetime.date.today().strftime('%y%m%d')}-{len(sales_df)+101}"
                            payload = {"invoice_id": inv_id, "date": str(pay_date), "customer": selected_customer, "service": "Due Collection", "amount": 0.0, "received": float(pay_amount), "due": float(-pay_amount)}
                            if sync_row_to_supabase("sales", payload):
                                st.success("Recovery Committed.")
                                st.rerun()
                                st.dataframe(st.session_state.sales, use_container_width=True, hide_index=True)
        
    elif menu == "Invoice Generator":
        page_header("Invoice Engine")
        if not st.session_state.sales.empty:
            inv_list = st.session_state.sales["Invoice_ID"].tolist()[::-1]
            selected_inv = st.selectbox("Memo Tracker", inv_list)
            inv_data = st.session_state.sales[st.session_state.sales["Invoice_ID"] == selected_inv].iloc[0]
            
            customer_name = inv_data["Customer"]
            all_cust_data = st.session_state.sales[st.session_state.sales["Customer"] == customer_name]
            ledger_due = pd.to_numeric(all_cust_data["Amount"], errors="coerce").sum() - pd.to_numeric(all_cust_data["Received"], errors="coerce").sum()
            comp = st.session_state.company_info
            
            st.markdown(
                f"""
                <div class="section-card">
                    <h4>{comp.get("Company Name")}</h4>
                    <p style="font-size:13px; margin:4px 0;"><b>Invoice No:</b> {selected_inv} | <b>Date:</b> {inv_data["Date"]}</p>
                    <p style="font-size:13px; margin:4px 0;"><b>Client:</b> {customer_name} | <b>Allocation:</b> {inv_data["Service"]}</p>
                </div>
                """, unsafe_allow_html=True
            )

    elif menu == "Expenses & Loans":
        page_header("Expenses & Loans Manager")
        t1, t2, t3 = st.tabs(["Expenses Entry", "Borrowings/Loans", "Directory Setup"])
        with t1:
            with st.form("exp_f", clear_on_submit=True):
                e_date = st.date_input("Expense Date")
                e_head = st.selectbox("Allocation Stream", st.session_state.expense_heads["Head Name"].tolist())
                e_amt = st.number_input("Value", min_value=0.0, step=100.0)
                if st.form_submit_button("Record Outflow", type="primary") and e_amt > 0:
                    if sync_row_to_supabase("expenses", {"date": str(e_date), "head": e_head, "amount": float(e_amt)}):
                        st.success("Expense synced.")
                        st.rerun()
            st.dataframe(st.session_state.expenses, use_container_width=True, hide_index=True)

    elif menu == "Profit & Loss":
        page_header("Performance Ledger Reports")
        t_sales = pd.to_numeric(st.session_state.sales["Amount"], errors="coerce").fillna(0).sum()
        t_rec = pd.to_numeric(st.session_state.sales["Received"], errors="coerce").fillna(0).sum()
        t_exp = pd.to_numeric(st.session_state.expenses["Amount"], errors="coerce").fillna(0).sum()
        n_profit = t_sales - t_exp
        
        st.markdown(
            f"""
            <div class="metric-container">
                <div class="metric-card"><div class="metric-label">Gross Billing Volume</div><div class="metric-value">{t_sales:,.2f} ৳</div></div>
                <div class="metric-card" style="background:#F0FDF4;"><div class="metric-label" style="color:#166534;">Net Yield Stream</div><div class="metric-value" style="color:#166534;">{n_profit:,.2f} ৳</div></div>
            </div>
            """, unsafe_allow_html=True
        )

if not st.session_state.logged_in:
    render_login()
else:
    render_main_app()
