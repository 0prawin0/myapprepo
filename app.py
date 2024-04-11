import openai
import streamlit as st
from docx import Document
from google.cloud import storage
import os
import uuid
from docx.shared import Pt

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

st.title("🧑‍💻 Job Genius JD Creator")
st.write("""
Hi, I am your JD Creator🤖 
Let me help you create a job description that would suit your requirements.
""")
# Initialize the session state keys
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "The following is a conversation with an AI assistant helping to create a job description. The assistant collects the following data one by one by interacting with the user by asking questions to create the best job description: company_name, job_title, key_skills, soft_skills, location, desired_experience, preferred_experience, about_the_team."}
    ]

if "job_details" not in st.session_state:
    st.session_state["job_details"] = {
        "job_title": None,
        "designation": None,
        "company_name": None
    }

# Function to extract and set job details from user input
def set_job_details(prompt, last_assistant_message):
    if "What is the job title?" in last_assistant_message:
        st.session_state["job_details"]["job_title"] = prompt
    elif "What is the designation?" in last_assistant_message:
        st.session_state["job_details"]["designation"] = prompt
    elif "What is the company name?" in last_assistant_message:
        st.session_state["job_details"]["company_name"] = prompt

# Function to save JD to a Word file and upload to Google Cloud Storage
def save_jd_to_bucket(bucket_name, job_role, designation, company_name, jd_text):
    # Create a unique file name
    unique_id = str(uuid.uuid4())
    file_name = f"{job_role}-{designation}-{company_name}-{unique_id}.docx"

    # Create a Word document
    doc = Document()
    
    # Add company name in bold and larger font
    company_paragraph = doc.add_paragraph()
    company_run = company_paragraph.add_run(company_name + "\n")
    company_run.bold = True
    company_run.font.size = Pt(16)  # Change the font size as needed

    doc.add_paragraph()  # Add an empty line for spacing

    # Add job description content
    for line in jd_text.split('\n'):
        if line.strip():
            doc.add_paragraph(line)

    doc.save(file_name)

    # Upload to Google Cloud Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)

    # Remove the file after uploading
    os.remove(file_name)

    return f"Job description saved to {bucket_name}/{file_name}"

# Handle user input
if prompt := st.chat_input():
    # If there is user input and the last message was from the assistant, check for job details
    if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "assistant":
        set_job_details(prompt, st.session_state["messages"][-1]["content"])
    
    openai.api_key = openai_api_key
    st.session_state["messages"].append({"role": "user", "content": prompt})

    # Generate a response from OpenAI only if all job details are set
    if all(st.session_state["job_details"].values()):
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613", messages=st.session_state["messages"])
        msg = response.choices[0].message
        st.session_state["messages"].append(msg)
        st.chat_message("assistant").write(msg["content"])

# Button to submit the job description
if st.button('Submit'):
    job_title = st.session_state["job_details"]["job_title"] or "Unknown"
    designation = st.session_state["job_details"]["designation"] or "Unknown"
    company_name = st.session_state["job_details"]["company_name"] or "Unknown"
    # Start from the 'Company Name:' prompt to ensure only the JD is included
    jd_text = "\n".join([msg["content"] for msg in st.session_state["messages"] if msg["role"] == "assistant" and "Company Name:" in msg["content"]])
    if jd_text:
        result = save_jd_to_bucket('jd_storage_bucket', job_title, designation, company_name, jd_text)
        st.success(result)
    else:
        st.error("No job description found to save.")
