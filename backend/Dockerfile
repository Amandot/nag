# Use a lightweight Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies for ML and Postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data (matching your local/Render setup)
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger_eng')"

# Copy the rest of the application
COPY . .

# Expose the HF default port
EXPOSE 7860

# Run with Gunicorn on port 7860
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]