# Use an official Python runtime as the base image
FROM python:3.8

# Set the working directory in the container to /app
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 50001

# Run the application when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "50001"]
