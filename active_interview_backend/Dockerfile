#Railway should be building using the last stage in the dockerfile
#As such production should get built and not ci

# Build stage
ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION} AS builder

# Combine venv creation and build dependencies
RUN python -m venv /opt/venv && \
    apt-get update && apt-get install -y \
    libpq-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    python3-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

ENV PATH=/opt/venv/bin:$PATH

# Install packages and cleanup in same layer
COPY requirements.txt /tmp/
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt gunicorn && \
    rm -rf /root/.cache/pip/* /tmp/requirements.txt

# Runtime base stage
FROM python:${PYTHON_VERSION} AS runtime

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Create runtime script
ARG PROJ_NAME="active_interview_project"
# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=${PROJ_NAME}.settings

WORKDIR /app
COPY . /app

RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-8080}\"\n\n" >> ./paracord_runner.sh && \
    printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
    printf "python manage.py collectstatic --no-input\n" >> ./paracord_runner.sh && \
    printf "python manage.py seed_bias_terms\n" >> ./paracord_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"[::]:\$RUN_PORT\" --workers 3\n" >> ./paracord_runner.sh && \
    chmod +x paracord_runner.sh

# CI stage (for testing)
FROM runtime AS ci

# Install Chrome, Chromedriver, and testing tools
ARG CHROME_VERSION=135.0.7049.52-1
ARG CHROMEDRIVER_VERSION=135.0.7049.52

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg \
    && wget -O google-chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb \
    && apt-get install -y ./google-chrome.deb \
    && rm google-chrome.deb \
    && wget -O chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip \
    && unzip chromedriver.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf chromedriver.zip chromedriver-linux64 \
    && rm -rf /var/lib/apt/lists/*

# Setup non-root user with proper permissions for testing
RUN groupadd -r paracord && useradd -r -g paracord paracord && \
    chown -R paracord:paracord /app && \
    chown -R paracord:paracord /opt/venv && \
    mkdir -p /home/paracord && chown -R paracord:paracord /home/paracord

# Create entrypoint wrapper that fixes permissions then drops to paracord user
RUN printf "#!/bin/bash\n" > ./docker-entrypoint.sh && \
    printf "set -e\n\n" >> ./docker-entrypoint.sh && \
    printf "# Fix permissions on volume mount points if running as root\n" >> ./docker-entrypoint.sh && \
    printf "if [ \"\$(id -u)\" = '0' ]; then\n" >> ./docker-entrypoint.sh && \
    printf "  echo 'Fixing permissions on volume mount points...'\n" >> ./docker-entrypoint.sh && \
    printf "  chown -R paracord:paracord /app/staticfiles /app/media /app/db 2>/dev/null || true\n" >> ./docker-entrypoint.sh && \
    printf "  chmod -R 755 /app/staticfiles /app/media /app/db 2>/dev/null || true\n" >> ./docker-entrypoint.sh && \
    printf "  echo 'Permissions fixed. Switching to paracord user...'\n" >> ./docker-entrypoint.sh && \
    printf "  exec gosu paracord \"\$@\"\n" >> ./docker-entrypoint.sh && \
    printf "else\n" >> ./docker-entrypoint.sh && \
    printf "  exec \"\$@\"\n" >> ./docker-entrypoint.sh && \
    printf "fi\n" >> ./docker-entrypoint.sh && \
    chmod +x docker-entrypoint.sh

# Install gosu for user switching
RUN apt-get update && \
    apt-get install -y gosu && \
    rm -rf /var/lib/apt/lists/*

# Create CI-specific default command that just keeps container running
RUN printf "#!/bin/bash\n" > ./ci_wait.sh && \
    printf "echo 'CI container ready. Waiting for commands...'\n" >> ./ci_wait.sh && \
    printf "tail -f /dev/null\n" >> ./ci_wait.sh && \
    chmod +x ci_wait.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["./ci_wait.sh"]

# Production stage (default - must be last for Railway)
FROM runtime AS production

# Setup non-root user
RUN groupadd -r paracord && useradd -r -g paracord paracord && \
    chown -R paracord:paracord /app && \
    chown -R paracord:paracord /opt/venv

USER paracord

CMD ./paracord_runner.sh