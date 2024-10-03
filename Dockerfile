FROM python:3.12

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y curl build-essential \
    && curl -sL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install npm separately to avoid conflicts
RUN npm install -g npm@latest

# Copy the requirements file and install Python dependencies
COPY ./requirements.txt /requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /requirements.txt

# Create Django user and setup permissions
RUN groupadd -r django && useradd -r -g django django
COPY . /app
RUN chown -R django /app

# Set the working directory
WORKDIR /app

# Install the application
RUN make install

# Switch to the Django user
USER django

# Build the sandbox environment
RUN make build_sandbox

# Copy necessary files
RUN cp --remove-destination /app/src/oscar/static/oscar/img/image_not_found.jpg /app/sandbox/public/media/

# Set working directory to sandbox and run the server with uWSGI
WORKDIR /app/sandbox/
CMD ["uwsgi", "--ini", "uwsgi.ini"]
