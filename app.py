import streamlit as st
from datetime import datetime, date, timedelta
from PIL import Image
import sqlite3
import smtplib
from email.mime.text import MIMEText
import streamlit.components.v1 as components
import time

# Page config
st.set_page_config(page_title="🎂 Ultimate Age Calculator", layout="centered")

# --- CSS and Styling ---
st.markdown("""
    <style>
    body {
        background: linear-gradient(to bottom right, #2c3e50, #1e1e2f);
        color: white;
    }
    h1, h2, h3, h4 {
        color: #FFD700;
    }
    .stApp {
        background-color: transparent;
    }
    </style>
""", unsafe_allow_html=True)

# --- Database ---
conn = sqlite3.connect('birthdays.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS birthdays (
        name TEXT,
        birth_date TEXT,
        email TEXT
    )
''')
conn.commit()

# --- Email Sending ---
def send_birthday_email(to_email, name, birth_date):
    from_email = st.secrets["EMAIL"]
    app_password = st.secrets["APP_PASSWORD"]

    subject = "🎉 Your Birthday is Tomorrow!"
    body = f"Hi {name},\n\nThis is your birthday reminder from the Age Calculator App!\n\nYour special day: {birth_date.strftime('%B %d')}\n\n🎂 Enjoy your celebration!\n\n- Ultimate Age Calculator"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(from_email, app_password)
            smtp.sendmail(from_email, to_email, msg.as_string())
        return True
    except Exception as e:
        return str(e)

# --- Header ---
st.title("🎂 Ultimate Age Calculator")
st.markdown("Upload your picture, calculate your age, and get reminded before your birthday!")

# --- Image Upload ---
st.subheader("🖼️ Upload Your Profile Picture")
uploaded_file = st.file_uploader("Choose a JPG/PNG file", type=["jpg", "jpeg", "png"])
if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Your Picture", use_column_width=True)

# --- Name and DOB ---
st.subheader("🧾 Enter Your Information")
name = st.text_input("👤 Your Name")
birth_date = st.date_input("🎂 Your Birthdate", min_value=date(1900, 1, 1), max_value=date.today(), value=date(2000, 1, 1))

# --- Email Optional ---
send_email = st.checkbox("📧 Remind me by email one day before my birthday")
email = st.text_input("✉️ Enter your email address") if send_email else None

# --- Calculate Button ---
if st.button("🎈 Calculate Age"):

    today = date.today()

    # Calculate age
    age_years = today.year - birth_date.year
    age_months = today.month - birth_date.month
    age_days = today.day - birth_date.day

    if age_days < 0:
        age_months -= 1
        age_days += (date(today.year, today.month, 1) - date(today.year, today.month - 1, 1)).days
    if age_months < 0:
        age_years -= 1
        age_months += 12

    st.success(f"🧓 {name}, you are {age_years} years, {age_months} months, and {age_days} days old.")

    # Next birthday
    next_birthday = birth_date.replace(year=today.year)
    if next_birthday < today:
        next_birthday = next_birthday.replace(year=today.year + 1)

    days_remaining = (next_birthday - today).days
    st.info(f"⏳ Your next birthday is in **{days_remaining} days**!")

    # Animation
    if days_remaining == 0:
        st.balloons()
    elif days_remaining <= 7:
        st.toast("🎉 Your birthday is coming soon!")
        components.html("""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
        <script>
        confetti({ particleCount: 200, spread: 100, origin: { y: 0.6 } });
        </script>
        """, height=0, width=0)

    # Email Reminder
    if send_email and email and days_remaining == 1:
        result = send_birthday_email(email, name, birth_date)
        if result == True:
            st.success("📬 Reminder email sent successfully!")
        else:
            st.error(f"Email failed: {result}")

    # Save to DB
    c.execute("INSERT INTO birthdays (name, birth_date, email) VALUES (?, ?, ?)", (name, str(birth_date), email))
    conn.commit()
    st.success("✅ Info saved!")

# --- Live Countdown Timer ---
st.subheader("⏳ Live Countdown to Your Next Birthday")

if name:
    now = datetime.now()
    next_birthday = birth_date.replace(year=now.year)
    if next_birthday < now.date():
        next_birthday = next_birthday.replace(year=now.year + 1)

    target_datetime = datetime.combine(next_birthday, datetime.min.time())
    seconds_left = int((target_datetime - now).total_seconds())
    timer = st.empty()

    while seconds_left > 0 and seconds_left <= 5:
        days = seconds_left // (24 * 3600)
        hours = (seconds_left % (24 * 3600)) // 3600
        minutes = (seconds_left % 3600) // 60
        seconds = seconds_left % 60
        timer.markdown(f"### ⏰ {days}d {hours}h {minutes}m {seconds}s")
        time.sleep(1)
        seconds_left -= 1

# --- Show Saved Users ---
st.subheader("📋 All Saved Birthdays (Local Only)")
c.execute("SELECT name, birth_date, email FROM birthdays")
for row in c.fetchall():
    st.write(f"👤 {row[0]} | 🎂 {row[1]} | 📧 {row[2] if row[2] else 'N/A'}")
