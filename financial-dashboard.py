import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone
import json
from pathlib import Path
import hashlib
import pytz
import csv


# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Keuangan Organisasi",
    page_icon="💰",
    layout="wide"
)

# Custom CSS for responsive logo and sidebar layout
st.markdown("""
    <style>
    .sidebar-logo {
        width: 100%;
        max-width: 200px;
        height: auto;
        margin-bottom: 20px;
    }
    .sidebar-menu {
        margin-bottom: 40px;
    }
    .sidebar-logout {
        position: absolute;
        bottom: 20px;
        left: 20px;
        right: 20px;
    }
    </style>
""", unsafe_allow_html=True)


# Add logo with responsive class
st.sidebar.markdown(
    '<img src="https://github.com/Muhammadirfankarim/financial-dashboard-organization/raw/main/Himasisko.png" class="sidebar-logo">',
    unsafe_allow_html=True
)

# Inisialisasi session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'members' not in st.session_state:
    st.session_state.members = []
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# Function to hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Modify the users dictionary
users = {
    "bendahara": {"password": st.secrets["bendahara_password"], "role": "Bendahara"},
    "anggota": {"password": st.secrets["anggota_password"], "role": "Anggota"}
}

# Modify the login function
def login(username, password):
    if username in users:
        stored_password = users[username]["password"]
        if hash_password(password) == hash_password(stored_password):
            st.session_state.authenticated = True
            st.session_state.user_role = users[username]["role"]
            return True
    return False

# Login page
def show_login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(username, password):
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau password salah.")

def main_app():
    import csv
    # Add logout button to sidebar
    st.sidebar.markdown('<div class="sidebar-logout">', unsafe_allow_html=True)
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    def save_data():
        """Menyimpan data ke file CSV"""
        data_path = Path("financial_data")
        data_path.mkdir(exist_ok=True)
        
        # Save transactions
        transactions_file = data_path / "transactions.csv"
        try:
            with open(transactions_file, "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['source', 'amount', 'date', 'description', 'member'])
                writer.writeheader()
                for transaction in st.session_state.transactions:
                    transaction_copy = transaction.copy()
                    if isinstance(transaction_copy['date'], (pd.Timestamp, datetime)):
                        transaction_copy['date'] = transaction_copy['date'].isoformat()
                    writer.writerow(transaction_copy)
            print("Transactions saved successfully")
        except Exception as e:
            st.error(f"Error saving transactions: {str(e)}")

        # Save members
        members_file = data_path / "members.csv"
        try:
            with open(members_file, "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['name', 'position', 'contact'])
                writer.writeheader()
                for member in st.session_state.members:
                    writer.writerow(member)
            print("Members saved successfully")
        except Exception as e:
            st.error(f"Error saving members: {str(e)}")


    def load_data():
        """Memuat data dari file CSV"""
        data_path = Path("financial_data")
        
        # Load transactions
        transactions_file = data_path / "transactions.csv"
        if transactions_file.exists():
            try:
                with open(transactions_file, "r") as f:
                    reader = csv.DictReader(f)
                    transactions = list(reader)
                    for transaction in transactions:
                        transaction['amount'] = float(transaction['amount'])
                        # Parse the date string to datetime without localization first
                        parsed_date = pd.to_datetime(transaction['date'])
                        # If the date is not tz-aware, localize it to UTC
                        if parsed_date.tz is None:
                            transaction['date'] = parsed_date.tz_localize('UTC')
                        else:
                            transaction['date'] = parsed_date
                    st.session_state.transactions = transactions
            except Exception as e:
                st.error(f"Error loading transactions: {str(e)}")
                st.session_state.transactions = []

        # Load members
        members_file = data_path / "members.csv"
        if members_file.exists():
            try:
                with open(members_file, "r") as f:
                    reader = csv.DictReader(f)
                    st.session_state.members = list(reader)
            except Exception as e:
                st.error(f"Error loading members: {str(e)}")
                st.session_state.members = []

    # Memuat data yang ada
    load_data()

    # Format rupiah
    def format_rupiah(amount):
        return f"Rp {amount:,.0f}"

    # Sidebar untuk navigasi
    st.sidebar.markdown('<div class="sidebar-menu">', unsafe_allow_html=True)
    page = st.sidebar.radio("Menu", ["Dashboard", "Tambah Transaksi", "Manajemen Anggota"])
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    if page == "Dashboard":
        st.title("💰 Dashboard Keuangan")
        
        # Inisialisasi DataFrame
        df = pd.DataFrame(st.session_state.transactions, 
                        columns=['source', 'amount', 'date', 'description', 'member'])
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'], utc=True)
            df['amount'] = pd.to_numeric(df['amount'])
            
            # Split 'member' column into 'member_name' and 'member_role'
            df[['member_name', 'member_role']] = df['member'].str.split(' - ', expand=True)
            # Menghitung total berdasarkan sumber
            col1, col2, col3 = st.columns(3)
            
            member_total = df[df['source'] == 'Kas Anggota']['amount'].sum()
            proposal_total = df[df['source'] == 'Proposal']['amount'].sum()
            sponsor_total = df[df['source'] == 'Sponsor/Media']['amount'].sum()
            
            with col1:
                st.metric("Total Kas Anggota", format_rupiah(member_total))
            with col2:
                st.metric("Total dari Proposal", format_rupiah(proposal_total))
            with col3:
                st.metric("Total dari Sponsor", format_rupiah(sponsor_total))
            
            # Grafik tren bulanan
            st.subheader("Tren Pemasukan Bulanan")
            monthly_data = df.groupby([df['date'].dt.strftime('%Y-%m'), 'source'])['amount'].sum().reset_index()
            fig = px.line(monthly_data, x='date', y='amount', color='source',
                        title="Pemasukan Bulanan berdasarkan Sumber",
                        labels={'date': 'Bulan', 'amount': 'Jumlah (Rp)', 'source': 'Sumber'})
            fig.update_layout(
                xaxis_title="Bulan",
                yaxis_title="Jumlah (Rp)",
                legend_title="Sumber"
            )
            fig.update_traces(hovertemplate='Bulan: %{x}<br>Jumlah: Rp %{y:,.0f}<br>Sumber: %{fullData.name}')
            st.plotly_chart(fig, use_container_width=True)
            
            # Grafik distribusi pemasukan
            st.subheader("Distribusi Pemasukan")
            source_total = df.groupby('source')['amount'].sum()
            fig = px.pie(values=source_total.values, names=source_total.index,
                        title="Distribusi Pemasukan berdasarkan Sumber")
            fig.update_traces(hovertemplate='Sumber: %{label}<br>Jumlah: Rp %{value:,.0f}')
            st.plotly_chart(fig, use_container_width=True)
            
        # Riwayat transaksi dengan tombol hapus
                # Riwayat transaksi dengan tombol hapus
        st.subheader("Transaksi Terbaru")
        if len(st.session_state.transactions) > 0:
            recent_transactions = df.sort_values('date', ascending=False).head(10).copy()
            recent_transactions['transaction_id'] = range(len(recent_transactions))
            
            for _, row in recent_transactions.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 3, 1, 1])
                    col1.write(row['date'].tz_convert(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M:%S'))
                    col2.write(row['source'])
                    col3.write(format_rupiah(row['amount']))
                    col4.write(row['description'])
                    col5.write(row['member'] if 'member' in row else '-')
                    
                    if st.session_state.user_role == "Bendahara":
                        if col6.button('Hapus', key=f'delete_{row["transaction_id"]}'):
                            # Find the transaction to remove based on its unique attributes
                            transaction_to_remove = next(
                                (t for t in st.session_state.transactions 
                                 if t['source'] == row['source'] 
                                 and t['amount'] == row['amount'] 
                                 and t['description'] == row['description'] 
                                 and t['member'] == row['member']),
                                None
                            )
                            if transaction_to_remove:
                                st.session_state.transactions.remove(transaction_to_remove)
                                save_data()
                                st.rerun()
                            else:
                                st.error("Transaksi tidak ditemukan.")
                    st.divider()
        else:
            st.info("Belum ada transaksi tercatat. Silakan tambahkan transaksi untuk melihat daftar.")
        
        # New section for all transactions
        st.subheader("Semua Transaksi")
        if len(st.session_state.transactions) > 0:
            all_transactions = df.sort_values('date', ascending=False).copy()
            all_transactions['date'] = all_transactions['date'].dt.tz_convert(pytz.timezone('Asia/Jakarta')).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Reorder columns to show member_name and member_role separately
            columns_order = ['date', 'source', 'amount', 'description', 'member_name', 'member_role']
            all_transactions = all_transactions[columns_order]

            st.dataframe(all_transactions)
            # Export to CSV
            if st.session_state.user_role == "Bendahara":
                current_date = datetime.now().strftime("%Y-%m-%d")
                csv = all_transactions.to_csv(index=False)
                st.download_button(
                    label="Unduh sebagai CSV",
                    data=csv,
                    file_name=f"Transaksi_terakhir_{current_date}.csv",
                    mime="text/csv",
                )
        else:
            st.info("Belum ada transaksi tercatat.")

    elif page == "Tambah Transaksi":
        if st.session_state.user_role == "Bendahara":
            st.title("📝 Tambah Transaksi Baru")
        
            with st.form("transaction_form"):
                source = st.selectbox(
                    "Sumber Dana",
                    ["Kas Anggota", "Proposal", "Sponsor/Media"]
                )
                
                # Show different fields based on source selection
                if source == "Kas Anggota":
                    member_list = [f"{m['name']} - {m['position']}" for m in st.session_state.members]
                    if member_list:
                        member = st.selectbox("Anggota", member_list)
                    else:
                        st.warning("Belum ada anggota terdaftar. Silakan tambahkan anggota terlebih dahulu.")
                elif source == "Sponsor/Media":
                    member = st.text_input("Nama Sponsor/Media", help="Masukkan nama perusahaan atau media partner")
                else:  # Proposal
                    member = "-"  # No member field needed for proposals
                
                amount = st.number_input("Jumlah (Rp)", min_value=0.0, step=10000.0)
                date = st.date_input("Tanggal")
                description = st.text_area("Keterangan", 
                    placeholder="Masukkan detail tambahan tentang transaksi...")
                
                submitted = st.form_submit_button("Simpan Transaksi")
                
                if submitted:
                    if amount <= 0:
                        st.error("Mohon masukkan jumlah lebih dari nol.")
                    elif source == "Kas Anggota" and not member:
                        st.error("Silakan pilih anggota untuk transaksi Kas Anggota.")
                    elif source == "Sponsor/Media" and not member:
                        st.error("Silakan masukkan nama Sponsor/Media.")
                    else:
                        # get current time in user's timezone
                        current_time = datetime.now().time()
                        # Combine input date with current time
                        transaction_datetime = datetime.combine(date, current_time)
                        # Convert to UTC for storage
                        utc_datetime = pytz.timezone('Asia/Jakarta').localize(transaction_datetime).astimezone(pytz.UTC)
                        transaction = {
                            "source": source,
                            "amount": float(amount),
                            "date": utc_datetime.isoformat(),
                            "description": description,
                            "member": member
                        }
                        
                        st.session_state.transactions.append(transaction)
                        save_data()
                        st.success("Transaksi berhasil ditambahkan!")
                        st.balloons()
        else:
            st.warning("Anda tidak memiliki izin untuk menambah transaksi.")
    elif page == "Manajemen Anggota":
        if st.session_state.user_role == "Bendahara":
            st.title("👥 Manajemen Anggota")
        
            # Form tambah anggota
            with st.form("member_form"):
                st.subheader("Tambah Anggota Baru")
                name = st.text_input("Nama Lengkap")
                position = st.selectbox("Jabatan", [
                    "Ketua", "Wakil Ketua", "Sekretaris", "Bendahara", 
                    "Koordinator", "Kepala Dinas", "Wakil Kepala Dinas", "Anggota"
                ])
                contact = st.text_input("Kontak (No. HP/Email) *", help="Field ini wajib diisi")
                
                submitted = st.form_submit_button("Tambah Anggota")
                
                if submitted:
                    if not name:
                        st.error("Nama Lengkap harus diisi!")
                    elif not contact:
                        st.error("Kontak harus diisi!")
                    else:
                        new_member = {
                            "name": name,
                            "position": position,
                            "contact": contact
                        }
                        st.session_state.members.append(new_member)
                        save_data()
                        st.success("Anggota baru berhasil ditambahkan!")
                        st.balloons()
            
            # Daftar anggota
            st.subheader("Daftar Anggota")
            if st.session_state.members:
                for idx, member in enumerate(st.session_state.members):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 3, 1])
                        col1.write(member['name'])
                        col2.write(member['position'])
                        col3.write(member['contact'])
                        if col4.button('Hapus', key=f'delete_member_{idx}'):
                            st.session_state.members.pop(idx)
                            save_data()
                            st.rerun()
                        st.divider()
            else:
                st.info("Belum ada anggota terdaftar.")
        else:
            st.warning("Anda tidak memiliki izin untuk mengelola anggota.")
    
if not st.session_state.authenticated:
    show_login_page()
else:
    main_app()
# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
    </style>
    """, unsafe_allow_html=True)
