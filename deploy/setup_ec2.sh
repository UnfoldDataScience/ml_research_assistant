#!/bin/bash
# EC2 Setup Script for ML Research Assistant
# This script installs all dependencies and sets up the environment
# NOTE: Assumes project files are already copied to /home/ubuntu/ml-research-assistant via SCP

set -e  # Exit on any error

echo "========================================="
echo "ML Research Assistant - EC2 Setup"
echo "========================================="

# Verify we're in the correct directory
APP_DIR="/home/ubuntu/ml-research-assistant"
if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: Application directory not found: $APP_DIR"
    echo "Please copy project files to EC2 first using SCP (see DEPLOYMENT.md)"
    exit 1
fi

cd $APP_DIR
echo "Working directory: $(pwd)"

# Update system packages
echo "[1/6] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Python 3 and pip (works with 3.10, 3.11, 3.12)
echo "[2/6] Installing Python 3 and pip..."
sudo apt-get install -y python3 python3-venv python3-pip

# Create virtual environment
echo "[3/6] Creating Python virtual environment..."
# Use python3 (works with 3.10, 3.11, 3.12+)
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3 first."
    exit 1
fi

echo "Creating virtual environment with python3..."
python3 -m venv .venv

if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment creation failed!"
    echo "Please check Python installation and try manually:"
    echo "  python3 -m venv .venv"
    exit 1
fi

echo "Virtual environment created successfully."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "[4/6] Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file template (if it doesn't exist)
echo "[5/6] Setting up environment configuration..."
if [ ! -f ".env" ]; then
    echo "Creating .env file template..."
    cat > .env << 'EOF'
# Weaviate Cloud Configuration
WEAVIATE_URL=your-weaviate-url-here
WEAVIATE_API_KEY=your-weaviate-api-key-here

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Optional: OpenAI Base URL (for Azure/other providers)
# OPENAI_BASE_URL=https://api.openai.com/v1
EOF
    echo "✓ .env template created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your actual API keys:"
    echo "   nano $APP_DIR/.env"
    echo ""
    read -p "Press Enter after you've updated the .env file with your keys..."
else
    echo "✓ .env file already exists"
fi

# Create logs directory
mkdir -p logs

# Set permissions
chown -R ubuntu:ubuntu $APP_DIR

echo "[6/6] Setup complete!"
echo ""
echo "========================================="
echo "Next steps:"
echo "========================================="
echo "1. Make sure your .env file has correct API keys"
echo "2. Build the index (one-time):"
echo "   cd $APP_DIR"
echo "   source .venv/bin/activate"
echo "   python scripts/build_index.py"
echo "3. Test the app:"
echo "   streamlit run app/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"
echo "4. Set up auto-start (see DEPLOYMENT.md)"
echo "========================================="

