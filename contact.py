import streamlit as st
import re
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

def is_valid_email(email):
    # Basic regex pattern for email validation
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_pattern, email) is not None
def contact_form():

    PASSWORD = st.secrets["PASSWORD"]
    USERNAME = st.secrets["USERNAME"]
    EMAIL = st.secrets["EMAIL"]

    with st.form("contact_form", clear_on_submit=False):

        container_name = st.empty()
        container_email = st.empty()
        container_message = st.empty()

        name = container_name.text_input("First Name", max_chars=50, key="name_1")
        email = container_email.text_input("Email Address", max_chars=50, key="email_1")
        message = container_message.text_area("Your Message", max_chars=1000, key="message_1")

        submit_button = st.form_submit_button("Submit")

        if submit_button:

            if not name:
                st.error("Please provide your name.", icon="🧑")
                st.stop()

            if not email:
                st.error("Please provide your email address.", icon="📨")
                st.stop()

            if not is_valid_email(email):
                st.error("Please provide a valid email address.", icon="📧")
                st.stop()

            if not message:
                st.error("Please provide a message.", icon="💬")
                st.stop()

            data = {
                "email": email,
                "name": name,
                "message": message
            }

            # Email configuration
            smtp_server = 'smtp.gmail.com'  # Replace with your SMTP server
            smtp_port = 587  # For TLS
            username = USERNAME  # Your email address
            password = PASSWORD # Your email password

            # Create the email content
            sender_email = EMAIL
            receiver_email = EMAIL
            subject = 'yfinance App'
            body = json.dumps(data, indent=4)

            # Create a multipart email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = subject

            # Attach the body with the msg instance
            msg.attach(MIMEText(body, 'plain'))

            try:
                # Connect to the server
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()  # Upgrade the connection to secure
                    server.login(username, password)  # Login to your email account
                    server.sendmail(sender_email, receiver_email, msg.as_string())  # Send the email

                name = container_name.text_input("First Name", key="name_2")
                email = container_email.text_input("Email Address", key="email_2")
                message = container_message.text_area("Your Message", key="message_2")

                st.success("Your message has been sent successfully!")

                time.sleep(2)

                st.rerun()



            except Exception as e:
                print(f"Error: {e}")
