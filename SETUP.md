# 🛠️ Detailed Setup Guide

This guide provides step-by-step instructions for setting up the Cloudant Retrieval System.

## 📋 System Requirements

### Required Software
- **Python**: 3.9 or higher
- **Node.js**: 18.0 or higher
- **npm**: 9.0 or higher (comes with Node.js)
- **Git**: Latest version

### Operating Systems
- macOS 10.15+
- Ubuntu 20.04+
- Windows 10/11 with WSL2 (recommended) or native

## 🔧 Installation Steps

### Step 1: Install Python

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Verify installation
python3 --version
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Verify installation
python3 --version
```

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer (check "Add Python to PATH")
3. Verify in Command Prompt:
```cmd
python --version
```

### Step 2: Install Node.js

**macOS:**
```bash
# Using Homebrew
brew install node@18

# Verify installation
node --version
npm --version
```

**Ubuntu/Debian:**
```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

**Windows:**
1. Download from [nodejs.org](https://nodejs.org/)
2. Run installer
3. Verify in Command Prompt:
```cmd
node --version
npm --version
```

### Step 3: Clone Repository

```bash
# Clone the repository
git clone <your-repository-url>
cd cloudant-retrieval-system

# Verify you're in the correct directory
ls -la
```

### Step 4: Backend Setup

```bash
# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 5: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Verify installation
npm list --depth=0

# Return to project root
cd ..
```

### Step 6: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
# macOS/Linux:
nano .env

# Windows:
notepad .env
```

**Required Configuration:**

```env
# IBM Cloudant API Configuration
API_BASE_URL=https://your-cloudant-instance.cloudant.com/your-database/_design/your-design/_view/your-view
API_KEY=your-api-key-here
API_PASSWORD=your-api-password-here

# Application Settings
DATA_DIR=./data
CHECKPOINT_DIR=./checkpoints
BATCH_SIZE=5000
```

### Step 7: Create Required Directories

```bash
# Create data and checkpoint directories
mkdir -p data checkpoints

# Verify creation
ls -la
```

## 🚀 Running the Application

### Option 1: Using Two Terminals (Recommended)

**Terminal 1 - Backend:**
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Run backend server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
# Navigate to frontend
cd frontend

# Run development server
npm run dev
```

### Option 2: Using Screen/Tmux (Linux/macOS)

```bash
# Start backend in background
screen -dmS backend bash -c 'source venv/bin/activate && python -m uvicorn backend.main:app --reload'

# Start frontend in background
screen -dmS frontend bash -c 'cd frontend && npm run dev'

# View running sessions
screen -ls

# Attach to a session
screen -r backend  # or frontend
```

### Option 3: Using PM2 (Production)

```bash
# Install PM2 globally
npm install -g pm2

# Start backend
pm2 start "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000" --name cloudant-backend

# Start frontend
pm2 start "npm run dev" --name cloudant-frontend --cwd ./frontend

# View status
pm2 status

# View logs
pm2 logs
```

## ✅ Verification

### 1. Check Backend

```bash
# Test health endpoint
curl http://localhost:8000/

# Expected response:
# {"status":"healthy","service":"Cloudant Retrieval System","version":"2.0.0"}
```

### 2. Check Frontend

Open browser and navigate to:
```
http://localhost:3000
```

You should see the IBM Carbon-styled interface.

### 3. Test Cloudant Connection

```bash
# Test Cloudant API directly
curl -u "$API_KEY:$API_PASSWORD" "$API_BASE_URL?limit=1"
```

## 🐛 Common Issues

### Issue: Port Already in Use

**Backend (Port 8000):**
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

**Frontend (Port 3000):**
```bash
# Find and kill process
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows
```

### Issue: Module Not Found

```bash
# Reinstall Python dependencies
pip install --force-reinstall -r requirements.txt

# Reinstall Node dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Permission Denied

**macOS/Linux:**
```bash
# Fix directory permissions
chmod -R 755 data checkpoints

# Fix virtual environment
chmod -R 755 venv
```

**Windows:**
Run Command Prompt or PowerShell as Administrator.

### Issue: SSL Certificate Errors

```bash
# Update certificates (macOS)
/Applications/Python\ 3.11/Install\ Certificates.command

# Update certificates (Ubuntu)
sudo apt-get install ca-certificates
sudo update-ca-certificates
```

### Issue: Python Virtual Environment Not Activating

**Windows PowerShell:**
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
venv\Scripts\Activate.ps1
```

## 🔒 Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] API credentials are not hardcoded
- [ ] Virtual environment is activated
- [ ] Dependencies are up to date
- [ ] Firewall allows ports 8000 and 3000 (if needed)

## 📊 Performance Tuning

### Backend Optimization

Edit [`backend/config.py`](backend/config.py:1):

```python
# For faster retrieval (more memory)
BATCH_SIZE = 10000
MAX_CONCURRENT_REQUESTS = 5

# For slower but safer retrieval
BATCH_SIZE = 2000
MAX_CONCURRENT_REQUESTS = 1
```

### Frontend Optimization

Edit [`frontend/src/App.jsx`](frontend/src/App.jsx:1):

```javascript
// Change polling interval (line ~35)
const pollInterval = setInterval(async () => {
  // ...
}, 500);  // Poll every 500ms instead of 1000ms
```

## 🔄 Updating the Application

```bash
# Pull latest changes
git pull origin main

# Update Python dependencies
pip install --upgrade -r requirements.txt

# Update Node dependencies
cd frontend
npm update
cd ..
```

## 🧪 Testing

### Backend Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when available)
pytest tests/
```

### Frontend Tests

```bash
cd frontend

# Run tests (when available)
npm test
```

## 📦 Building for Production

### Backend

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend

```bash
cd frontend

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🌐 Deployment

### Using Docker (Recommended)

Create `Dockerfile`:

```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./checkpoints:/app/checkpoints
  
  frontend:
    image: node:18
    working_dir: /app
    command: npm run dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
```

Run:
```bash
docker-compose up -d
```

## 📞 Getting Help

If you encounter issues:

1. Check this guide thoroughly
2. Review the main [README.md](README.md:1)
3. Check existing GitHub issues
4. Create a new issue with:
   - Operating system
   - Python version
   - Node.js version
   - Error messages
   - Steps to reproduce

---

**Setup complete! 🎉 You're ready to start retrieving data.**