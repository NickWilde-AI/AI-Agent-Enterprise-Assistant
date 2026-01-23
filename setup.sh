#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Project Setup...${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${GREEN}✅ Virtual environment already exists.${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}📥 Installing dependencies from requirements.txt...${NC}"
    pip install -r requirements.txt
    # Also ensure streamlit is installed (it might be in requirements, but just in case)
    pip install streamlit
else
    echo "Warning: requirements.txt not found!"
fi

# Create .env from template if strictly necessary, but for now just warn
if [ ! -f ".env" ]; then
    echo -e "\n⚠️  ${BLUE}Note: .env file not found.${NC}"
    echo "Please create a .env file with your OPENAI_API_KEY."
    echo "Example content:"
    echo "OPENAI_API_KEY=sk-..."
    echo "OPENAI_BASE_URL=https://api.deepseek.com/v1"
    echo "OPENAI_MODEL=deepseek-chat"
    echo "OPENAI_EMBED_MODEL=local:BAAI/bge-small-zh-v1.5"
fi

echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo -e "To start the application, run:"
echo -e "${BLUE}source venv/bin/activate${NC}"
echo -e "${BLUE}streamlit run src/app/streamlit_app.py${NC}"
