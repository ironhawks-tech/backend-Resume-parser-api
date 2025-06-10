FROM python:3.11-slim

WORKDIR /app

# Install OS-level dependencies (for PDFs etc. and Chromium dependencies)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    build-essential \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    libdrm2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps
RUN apt-get update && apt-get install -y chromium



# Copy app code
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
