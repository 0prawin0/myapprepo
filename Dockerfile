FROM python:3.8

# Define a build argument for the OpenAI API key
ARG OPENAI_API_KEY

# Set the OpenAI API key as an environment variable in the container
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
