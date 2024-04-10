import openai
import streamlit as st

openai_api_key = "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"

st.title("🧑‍💻 Job Genius JD Creator")
st.write("""
My name is Sridhr, the JD Creator🤖. 
Let me help you create the best job description in the world.
Please, don't ask me stupid questions❓
""")

# Initialize the session state keys
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "The following is a conversation with an AI assistant helping to create a job description. The assistant collects the following data one by one by interacting with the user by asking questions to create the best job description: job_title, key_skills, soft_skills, location, desired_experience, preferred_experience, about_the_team."}
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

# Example of checking and accessing a specific key in the session state
if 'job_title' in st.session_state:
    job_title = st.session_state['job_title']
else:
    job_title = 'Default Job Title'

# You can use job_title in your app as needed
