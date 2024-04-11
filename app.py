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

if "job_title_asked" not in st.session_state:
    st.session_state["job_title_asked"] = False

# Ask for the job title if not asked before
if not st.session_state["job_title_asked"]:
    st.session_state["messages"].append({"role": "assistant", "content": "What is the job title?"})
    st.session_state["job_title_asked"] = True

# Handle user input
if prompt := st.chat_input():
    openai.api_key = openai_api_key
    st.session_state["messages"].append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613", messages=st.session_state["messages"])
    msg = response.choices[0].message
    st.session_state["messages"].append(msg)
    st.chat_message("assistant").write(msg["content"])

# Function to save JD to a Word file and upload to Google Cloud Storage
def save_jd_to_bucket(jd_text, bucket_name, job_role, designation, company_name):
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

# Revised function to extract job role, designation, and company name
def extract_details(messages):
    job_role = designation = company_name = "Unknown"
    prompts = {"What is the job title?": "job_role", 
               "What is the designation?": "designation", 
               "What is the company name?": "company_name"}
    
    for i, msg in enumerate(messages):
        if msg['role'] == 'assistant' and msg['content'] in prompts:
            # Assume that the user's next message contains the answer
            if i + 1 < len(messages) and messages[i + 1]['role'] == 'user':
                answer = messages[i + 1]['content']
                if prompts[msg['content']] == "job_role":
                    job_role = answer
                elif prompts[msg['content']] == "designation":
                    designation = answer
                elif prompts[msg['content']] == "company_name":
                    company_name = answer
    
    return job_role, designation, company_name

# Button to submit the job description
if st.button('Submit'):
    # Extract job role, designation, and company name from the session state messages
    job_role, designation, company_name = extract_details(st.session_state["messages"])
    
    jd_text = ''
    # Flag to determine when the job description starts
    jd_start_flag = False
    for msg in st.session_state["messages"]:
        if msg['role'] == 'assistant' and "Here is the updated job description:" in msg['content']:
            jd_start_flag = True  # Start capturing the job description from this point
        if jd_start_flag and msg['role'] == 'assistant':
            jd_text += msg['content'] + '\n'  # Add only assistant messages after job description start

    result = save_jd_to_bucket(jd_text, 'jd_storage_bucket', job_role, designation, company_name)
    st.success(result)
