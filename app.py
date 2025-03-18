import psycopg2
import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

db_password = st.secrets.behaviourtracker.db_password
DATABASE_URL = f"postgresql://neondb_owner:{db_password}@ep-calm-bush-ablzp8fe-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(DATABASE_URL)

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
        conn.commit()  # Explicitly commit changes

def get_events():
    with engine.connect() as conn:  # Open a connection for this query
        df = pd.read_sql("SELECT * FROM events ORDER BY date DESC", conn)
    return df

# Ensure the table exists
create_table()


# Initialize session state for storing events
if "events" not in st.session_state:
    st.session_state.events = []

st.title("📊 Barnets Beteendehistorik")

# Toggle between views
view_chart = st.checkbox("Visa diagram istället för lista")

# Add a new event
with st.expander("➕ Logga en ny händelse"):
    # User input form
    date = st.date_input("Datum", datetime.date.today())
    description = st.text_area("Beskrivning")
    severity = st.selectbox("Allvarlighetsnivå", ["Låg", "Medel", "Hög"])

    if st.button("Spara händelse"):
        insert_event(date, description, severity)
        st.success("Händelsen har sparats!")

# Convert events to a DataFrame
#df = pd.DataFrame(st.session_state.events)
#st.header("📋 Lista över händelser")
df = get_events()
if not df.empty:
    df["date"] = pd.to_datetime(df["date"])
    df["count"] = 1  # For aggregation

    if view_chart:
        # Aggregate events per day
        event_counts = df.groupby("date")["count"].sum()

        # Plotting
        fig, ax = plt.subplots()
        ax.bar(event_counts.index, event_counts.values, color="#8884d8")
        ax.set_xlabel("Datum")
        ax.set_ylabel("Antal händelser")
        ax.set_title("Beteendehistorik över tid")
        st.pyplot(fig)
    else:
        # Display as table
        st.dataframe(df[["date", "description", "severity"]])
else:
    st.info("Inga händelser registrerade än.")

