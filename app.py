import psycopg2
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

# Database Connection
db_password = st.secrets.behaviourtracker.db_password
DATABASE_URL = f"postgresql://neondb_owner:{db_password}@ep-calm-bush-ablzp8fe-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL)

# Dummy user credentials
USER_CREDENTIALS = {
    "jonna": "1234",
    "mikael": "1234"
}


# Authentication Function
def authenticate(username, password):
    return USER_CREDENTIALS.get(username) == password


# Logout Function
def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.password = None
    st.rerun()


# User Login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Logga in")

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Användarnamn", placeholder="Skriv ditt användarnamn")
        password = st.text_input("Lösenord", type="password", placeholder="Skriv ditt lösenord")
        submitted = st.form_submit_button("Logga in")

    if submitted:
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.toast("✅ Inloggning lyckades!")
            st.rerun()
        else:
            st.error("❌ Fel användarnamn eller lösenord!")

else:
    # Logout button in a mobile-friendly way
    with st.container():
        if st.button("🚪 Logga ut", use_container_width=True):
            logout()


    # Ensure the table exists
    def create_table():
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL
                );
            """))


    def insert_event(date, description, severity):
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO events (date, description, severity) VALUES (:date, :desc, :sev)"),
                {"date": date, "desc": description, "sev": severity}
            )
            conn.commit()


    def get_events():
        with engine.connect() as conn:
            df = pd.read_sql("SELECT * FROM events ORDER BY date DESC", conn)
        return df


    create_table()

    st.title("Händelser")

    # Toggle between views (placed under the title for better mobile UX)
    view_chart = st.toggle("📈 Visa diagram istället för lista")

    # Add a new event
    with st.expander("➕ Logga en ny händelse"):
        with st.form("event_form"):
            date = st.date_input("📅 Datum", datetime.date.today())
            description = st.text_area("📝 Beskrivning", placeholder="Beskriv händelsen här...")
            severity = st.selectbox("⚠️ Allvarlighetsnivå", ["Låg", "Medel", "Hög"])
            save_event = st.form_submit_button("💾 Spara händelse")

        if save_event:
            insert_event(date, description, severity)
            st.toast("✅ Händelsen har sparats!")

    df = get_events()
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["count"] = 1

        if view_chart:
            event_counts = df.groupby("date")["count"].sum()

            fig, ax = plt.subplots(figsize=(6, 3))  # Adjust figure size for mobile
            ax.bar(event_counts.index, event_counts.values, color="#8884d8")
            ax.set_xlabel("Datum")
            ax.set_ylabel("Antal händelser")
            ax.set_title("Beteendehistorik över tid")
            plt.xticks(rotation=45, fontsize=8)  # Make date labels readable on mobile
            st.pyplot(fig)
        else:
            st.dataframe(df[["date", "description", "severity"]], use_container_width=True)
    else:
        st.info("ℹ️ Inga händelser registrerade än.")
