# Use the Python 3.11.5 image
FROM python:3.11.5-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory into the container
COPY . /app

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port 9600
EXPOSE 9600

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9600"]