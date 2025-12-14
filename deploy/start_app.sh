#!/bin/bash
# Start Script for ML Research Assistant Streamlit App
# This script starts the Streamlit application

set -e  # Exit on any error

APP_DIR="/home/ubuntu/ml-research-assistant"
cd $APP_DIR

# Activate virtual environment
source .venv/bin/activate

# Start Streamlit app
# --server.port 8501: Use port 8501
# --server.address 0.0.0.0: Listen on all interfaces (accessible from outside)
# --server.headless true: Run in headless mode (no browser)
# --server.enableCORS false: Disable CORS (not needed for single app)
# --server.enableXsrfProtection false: Disable XSRF protection for simplicity
streamlit run app/ui/streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --logger.level error

