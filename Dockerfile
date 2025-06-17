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
    poppler-utils \
    build-essential \
    wget \
    curl \
    gnupg \
    ca-certificates \
    unzip \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*


# Install Chromium and get its version
RUN apt-get update && apt-get install -y chromium

# Install matching ChromeDriver for Chromium
RUN CHROME_VERSION=$(chromium --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    echo "Detected Chromium version: $CHROME_VERSION" && \
    wget -q "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip" && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf chromedriver-linux64*


# Set Selenium to use Chromium + ChromeDriver
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH=$PATH:/usr/local/bin


# Copy requirement files
COPY requirements.txt .

COPY user_agents_list.txt ./user_agents_list.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps
RUN apt-get update && apt-get install -y chromium



# Copy app code
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
