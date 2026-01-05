# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Create directories for file handling
# These directories will be used for storing uploads, reports, and completed files.
RUN mkdir -p /app/files/uploads/completed /app/files/reports

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the cache, which reduces the image size.
# -r requirements.txt: Specifies the file to install from.
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

# Copy the rest of the application's source code from the host to the container's working directory
COPY . .

# Command to run the application
# This will be the default command executed when the container starts.
CMD ["python", "runner.py"]
