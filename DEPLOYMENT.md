# AWS EC2 Deployment Guide - Windows

Complete step-by-step guide to deploy the ML Research Assistant RAG application on AWS EC2 from Windows.

## Prerequisites

- AWS Account
- Windows machine with PowerShell or Git Bash
- Your Weaviate Cloud URL and API key
- Your OpenAI API key
- SCP client (comes with Git Bash or use PowerShell)

## Step 1: Launch EC2 Instance

### 1.1 Log into AWS Console

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **EC2** service

### 1.2 Launch Instance

1. Click **"Launch Instance"**
2. Configure the instance:

   **Name**: `ml-research-assistant` (or any name you prefer)

   **AMI (Amazon Machine Image)**:
   - Select **Ubuntu Server 22.04 LTS** (free tier eligible)
   - Architecture: 64-bit (x86)

   **Instance Type**:
   - For testing: `t2.micro` (free tier, but may be slow)
   - For production: `t3.medium` or `t3.large` (recommended)
   - Minimum: 2 vCPU, 4 GB RAM
   
   **Note**: Ubuntu 22.04 comes with Python 3.10+ by default, which works fine!

   **Key Pair**:
   - Create a new key pair or select existing one
   - **Important**: Download the `.pem` file and save it securely (e.g., `C:\Users\YourName\Downloads\`)
   - You'll need this to SSH into the instance

   **Network Settings**:
   - Click **"Edit"**
   - **Security Group**: Create new security group
   - **Allow SSH traffic from**: Your IP (or `0.0.0.0/0` for any IP - less secure)
   - Click **"Add security group rule"**:
     - **Type**: Custom TCP
     - **Port**: 8501
     - **Source**: `0.0.0.0/0` (or your IP for better security)
     - **Description**: Streamlit App

   **Configure Storage**:
   - **Size**: 20 GB (minimum, 30 GB recommended)
   - **Volume Type**: gp3 (default)

3. Click **"Launch Instance"**

### 1.3 Allocate Elastic IP (Optional but Recommended)

1. In EC2 console, go to **"Elastic IPs"** (left sidebar)
2. Click **"Allocate Elastic IP address"**
3. Click **"Allocate"**
4. Select the Elastic IP, click **"Actions"** → **"Associate Elastic IP address"**
5. Select your instance and click **"Associate"**

**Note**: Elastic IP gives you a static IP address that won't change when you restart the instance.

## Step 2: Connect to EC2 Instance

### 2.1 Get Instance Details

1. In EC2 console, go to **"Instances"**
2. Find your instance and note the **Public IPv4 address** (or Elastic IP if you created one)

### 2.2 SSH into Instance (Windows)

**Important**: Make sure you've downloaded the `.pem` key file from AWS when you created the key pair!

1. **Locate your key file**. It should be in your Downloads folder (e.g., `C:\Users\YourName\Downloads\your-key-name.pem`)

2. **Open PowerShell or Git Bash** on Windows

3. **Navigate to the folder containing your key file**:
   ```powershell
   cd C:\Users\YourName\Downloads
   # Replace YourName with your Windows username
   ```

4. **Set key file permissions (first time only)**:
   
   **Method 1: Using GUI (Easiest - Recommended)**:
   1. Right-click on your `.pem` file (e.g., `ml-research-assistant.pem`)
   2. Select **"Properties"**
   3. Go to the **"Security"** tab
   4. Click **"Advanced"**
   5. Uncheck **"Include inheritable permissions from this object's parent"**
   6. When prompted, choose **"Remove all inherited permissions"** or **"Convert inherited permissions into explicit permissions"**
   7. Click **"OK"** to save
   8. Make sure your user account has **"Read"** permission (it should by default)

5. **SSH into instance**:
   ```bash
   ssh -i your-key-name.pem ubuntu@<YOUR-INSTANCE-IP>
   ```
   
   **Or use full path if you're not in the same directory**:
   ```bash
   ssh -i "C:\Users\YourName\Downloads\your-key-name.pem" ubuntu@<YOUR-INSTANCE-IP>
   ```

   Replace:
   - `your-key-name.pem` with your actual key file name (e.g., `ml-research-assistant-key.pem`)
   - `<YOUR-INSTANCE-IP>` with your instance's public IP address (e.g., `98.80.120.233`)

**Troubleshooting SSH Issues**:

- **"Identity file not accessible: No such file or directory"**: 
  - Make sure you're in the correct directory where the `.pem` file is located
  - Or use the full path to the file: `ssh -i "C:\full\path\to\your-key.pem" ubuntu@<IP>`
  - Check that the file name is correct (including the `.pem` extension)

- **"Permission denied (publickey)"**:
  - Verify you're using the correct key file that matches the key pair selected when launching the instance
  - Make sure the key file permissions are set correctly (use GUI method above)
  - Verify you're connecting as `ubuntu` user (for Ubuntu AMI)

- **"Connection timeout"**:
  - Check that your security group allows SSH (port 22) from your IP
  - Verify the instance is running in AWS console
  - Check the instance's public IP address is correct

## Step 3: Set Up the Application

### 3.1 Upload Project Files Using SCP

**⚠️ IMPORTANT: Exclude large directories to speed up transfer!**

SCP will copy everything including `.venv/`, `__pycache__/`, and other large files if not excluded, which can take 30+ minutes. We'll exclude these to only copy source code.

**Option A: Using PowerShell Script (Recommended - Easy)**

1. **Open PowerShell** in your project directory on Windows

2. **Run the SCP script**:
   ```powershell
   .\deploy\copy_to_ec2.ps1 -KeyPath "C:\Users\YourName\Downloads\your-key-name.pem" -InstanceIP "YOUR-INSTANCE-IP"
   ```

   Replace:
   - `YourName` with your Windows username
   - `your-key-name.pem` with your actual key file name
   - `YOUR-INSTANCE-IP` with your EC2 instance IP address

   The script will:
   - Exclude large directories (`.venv`, `__pycache__`, `hf_cache`, `.git`, etc.)
   - Copy only source code files
   - Transfer to EC2 using SCP
   - **Note**: `.env` file is NOT copied (it's in `.gitignore` for security). The setup script will create a template for you to edit.

**Option B: Manual SCP Command**

1. **Open PowerShell or Git Bash** in your project directory on Windows

2. **Copy files excluding large directories** (SCP will create the directory automatically):
   ```powershell
   # From your project root directory on Windows
   scp -i "C:\Users\YourName\Downloads\your-key-name.pem" -r `
     --exclude='.venv' `
     --exclude='__pycache__' `
     --exclude='hf_cache' `
     --exclude='.git' `
     --exclude='*.pyc' `
     --exclude='.streamlit' `
     --exclude='logs' `
     --exclude='*.log' `
     . ubuntu@<YOUR-INSTANCE-IP>:/home/ubuntu/ml-research-assistant/
   ```

   **Note**: If `--exclude` doesn't work in your SCP version, you can manually copy specific directories:
   ```powershell
   # Copy only necessary files and folders
   scp -i "C:\Users\YourName\Downloads\your-key-name.pem" -r `
     app `
     scripts `
     deploy `
     requirements.txt `
     ubuntu@<YOUR-INSTANCE-IP>:/home/ubuntu/ml-research-assistant/
   ```
   
   **Note**: `.env` file is NOT copied (it's in `.gitignore` for security). The setup script will create a template that you'll edit manually.

4. **Verify files were copied** (SSH into EC2):
   ```bash
   ssh -i your-key-name.pem ubuntu@<YOUR-INSTANCE-IP>
   cd /home/ubuntu/ml-research-assistant
   ls -la
   # Should show: app/, scripts/, deploy/, requirements.txt, etc.
   ```

### 3.2 Run Setup Script

```bash
# Make sure you're in the project directory
cd /home/ubuntu/ml-research-assistant

# Make setup script executable
chmod +x deploy/setup_ec2.sh

# Run setup script
./deploy/setup_ec2.sh
```

The setup script will:
- Update system packages
- Install Python 3 and pip (works with 3.10, 3.11, 3.12+)
- Create virtual environment (`.venv` folder)
- Install Python packages from `requirements.txt`
- Create `.env` file template (if it doesn't exist) - you'll edit this with your API keys
- Create logs directory

**Note**: The script assumes project files are already copied to `/home/ubuntu/ml-research-assistant` via SCP. It does NOT create the directory or install git. The `.env` file is created as a template that you'll edit manually.

**Troubleshooting: If the setup script didn't create `.venv`:**

1. **Check if Python 3 is installed**:
   ```bash
   python3 --version
   # Should show Python 3.10, 3.11, or 3.12
   ```

2. **Create venv manually**:
   ```bash
   # Make sure you're in the project directory
   cd /home/ubuntu/ml-research-assistant
   
   # Create virtual environment
   python3 -m venv .venv
   
   # Verify it was created
   ls -la .venv
   
   # Activate it
   source .venv/bin/activate
   
   # Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **If you see errors, check**:
   - Python version: `python3 --version` (should be 3.10+)
   - Permissions: `ls -la` (should show you own the directory)
   - Disk space: `df -h` (should have free space)

### 3.3 Configure Environment Variables

The setup script created a `.env` template file. Now you need to edit it with your actual API keys:

```bash
# Edit .env file
nano .env
```

Replace the placeholder values with your actual API keys:

```env
# Weaviate Cloud Configuration
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your-actual-weaviate-api-key

# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

**Important Notes**:
- Make sure `WEAVIATE_URL` starts with `https://` (not just the domain)
- Make sure `WEAVIATE_API_KEY` uses underscores, not spaces
- No quotes needed around values
- No spaces around the `=` sign

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

## Step 4: Build the Index (One-Time Setup)

This step populates your Weaviate database with research papers. It only needs to be run once.

**Important**: This project uses **OpenAI embeddings** (not HuggingFace models), so there are no large model downloads. The build process is fast!

```bash
# Make sure you're in the project root directory
cd /home/ubuntu/ml-research-assistant

# Activate virtual environment
source .venv/bin/activate

# Build the index (this takes 5-15 minutes depending on number of papers)
python3 scripts/build_index.py
```

**What happens**:
- Loads papers from Hugging Face (streaming, no full download)
- Chunks them using semantic chunking
- Generates embeddings using OpenAI API (no model downloads!)
- Uploads to Weaviate

**Expected output**:
```
Collection PaperChunk already exists.
Loading dataset scientific_papers/arxiv...
Streaming first 5 papers (no full download needed)
Loaded 5 papers.
Using chunking strategy: semantic
Processing papers 1 to 5...
Generated 120 chunks (total so far: 120)
Total chunks generated: 120
Using OpenAI embeddings (text-embedding-3-small)...
Indexing 120 chunks in batches of 32...
100%|████████████| 4/4 [00:06<00:00, 1.56s/it]
Indexing complete.
Done.
```

**Troubleshooting**:

- **"ModuleNotFoundError: No module named 'app'"**:
  - The script automatically adds the project root to Python path
  - Make sure you're in the project root: `cd /home/ubuntu/ml-research-assistant`
  - Make sure virtual environment is activated: `source .venv/bin/activate`

- **"WEAVIATE_URL: NOT SET" or "API Key: NOT SET"**:
  - Check your `.env` file: `cat .env`
  - Make sure there are no spaces in variable names (use `WEAVIATE_API_KEY`, not `WEAVIATE API KEY`)
  - Make sure `WEAVIATE_URL` starts with `https://`
  - Make sure `.env` file is in the project root directory

- **OpenAI API errors**:
  - Verify your `OPENAI_API_KEY` is correct in `.env`
  - Check you have API credits available

## Step 5: Test the Application

### 5.1 Start Streamlit Manually

```bash
# Make sure you're in the project directory
cd /home/ubuntu/ml-research-assistant

# Activate virtual environment
source .venv/bin/activate

# Start Streamlit
streamlit run app/ui/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

The app should start and you'll see output like:
```
You can now view your Streamlit app in your browser.
Network URL: http://0.0.0.0:8501
```

**Note**: Keep this terminal window open while using the app. If you close SSH, the app will stop.

### 5.2 Access the Application

1. Open your web browser on Windows
2. Go to: `http://<YOUR-INSTANCE-IP>:8501`
3. You should see the ML Research Assistant interface!

**Note**: If you can't access it, check:
- Security group allows port 8501 from your IP
- Firewall on EC2 (Ubuntu firewall should be fine by default)

### 5.3 Stop the App

Press `Ctrl+C` in the terminal to stop the app

## Step 6: Performance Optimization

This project has been optimized for fast performance:

- **OpenAI Embeddings**: No model downloads needed (uses API)
- **Reranking Disabled by Default**: Faster responses (can be enabled in UI)
- **Evaluation Disabled by Default**: Faster responses (can be enabled in UI)



## Troubleshooting

### App Not Accessible

1. **Check Security Group**: Ensure port 8501 is open in AWS console
2. **Check if app is running**: Look at your SSH terminal
3. **Check Firewall**: 
   ```bash
   sudo ufw status
   # If firewall is active, allow port 8501:
   sudo ufw allow 8501/tcp
   ```

### App Crashes on Startup

1. **Check .env file**: 
   ```bash
   cat .env
   # Make sure all API keys are correct
   ```

2. **Check Python environment**: 
   ```bash
   source .venv/bin/activate
   python3 --version  # Should be 3.10+
   ```

3. **Check dependencies**:
   ```bash
   pip list
   # Should show all packages from requirements.txt
   ```

4. **Check for import errors**:
   ```bash
   python3 -c "from app.config import config; print('OK')"
   ```

### ModuleNotFoundError in Streamlit

If you see `ModuleNotFoundError: No module named 'app'`:
- The `streamlit_app.py` file has been updated to automatically add the project root to Python path
- Make sure you've copied all files from the `app/` directory to EC2
- Make sure you're running from the project root directory: `cd /home/ubuntu/ml-research-assistant`

### Slow Performance

- **First query**: May be slow (loading models), subsequent queries should be faster
- **With reranking enabled**: First use downloads model (~100MB), subsequent uses are faster
- **Instance too small**: Consider upgrading to `t3.medium` or `t3.large`

### Out of Memory

- Upgrade to larger instance type (t3.large or t3.xlarge)
- Reduce `max_papers` in `app/config.py` (default is 5)

## Cost Optimization

1. **Stop Instance When Not in Use**:
   - In EC2 console, select instance → Actions → Instance State → Stop
   - Start when needed: Actions → Instance State → Start

2. **Monitor Costs**:
   - Set up billing alerts in AWS Billing & Cost Management

3. **OpenAI API Costs**:
   - Embeddings: ~$0.02 per 1M tokens (very cheap)
   - For 5 papers (~120 chunks), cost is negligible (< $0.01)

## Security Best Practices

1. **Restrict Security Group**: Only allow port 8501 from your IP, not `0.0.0.0/0`
2. **Rotate API Keys**: Regularly update your API keys
3. **Keep System Updated**: 
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

## Summary of Changes Made

This deployment uses several optimizations:

1. **OpenAI Embeddings**: No HuggingFace model downloads (fast, uses API)
2. **Streaming Dataset Loading**: No full dataset download
3. **Lazy Reranker Loading**: Model only loads when reranking is enabled
4. **Performance Optimizations**: Reranking and evaluation disabled by default
5. **Fixed Import Paths**: Streamlit app automatically finds modules

## Next Steps

- Test the application with various queries
- Enable reranking/evaluation in UI if needed
- Monitor costs and performance
- Consider setting up auto-start (systemd) if needed for production

---

**Congratulations!** Your ML Research Assistant is now deployed on AWS EC2! 

For questions or issues, check the logs or review this guide.
