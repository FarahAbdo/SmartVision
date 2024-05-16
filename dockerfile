FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of your app's code
COPY . /app
WORKDIR /app

# Run the Streamlit app
CMD ["streamlit", "run", "app.py"]
