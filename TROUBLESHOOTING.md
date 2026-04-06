# 🔧 Troubleshooting Guide

Common issues and solutions for the Cloudant Retrieval System.

## 📦 Installation Issues

### Dependency Conflicts

**Issue:** Version conflicts with existing packages (spyder, aiobotocore)

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
spyder 6.1.0 requires aiohttp>=3.11.2, but you have aiohttp 3.9.1 which is incompatible.
```

**Solution 1: Use a Virtual Environment (Recommended)**

```bash
# Create isolated environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Solution 2: Upgrade aiohttp**

```bash
# The system will work with newer aiohttp versions
pip install --upgrade aiohttp>=3.9.2
```

**Solution 3: Use Conda Environment**

```bash
# Create new conda environment
conda create -n cloudant-retrieval python=3.11
conda activate cloudant-retrieval

# Install dependencies
pip install -r requirements.txt
```

### Missing System Dependencies

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Ubuntu/Debian:**
```bash
# Install build essentials
sudo apt-get update
sudo apt-get install build-essential python3-dev
```

**Windows:**
```bash
# Install Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

## 🚀 Runtime Issues

### Backend Won't Start

**Issue:** Port 8000 already in use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use a different port
uvicorn backend.main:app --port 8001
```

**Issue:** Module not found errors

```bash
# Verify virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

**Issue:** Configuration validation error

```
ValueError: API_BASE_URL is required
```

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check .env content
cat .env

# Ensure all required variables are set
API_BASE_URL=https://...
API_KEY=...
API_PASSWORD=...
```

### Frontend Won't Start

**Issue:** Port 3000 already in use

```bash
# Kill process on port 3000
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Or change port in vite.config.js
server: {
  port: 3001,
  ...
}
```

**Issue:** Module not found

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**Issue:** SASS/SCSS errors

```bash
# Install sass if missing
npm install -D sass

# Or use CSS instead of SCSS
# Rename all .scss files to .css
```

## 🔌 Connection Issues

### Cannot Connect to Cloudant

**Issue:** Authentication failed

```bash
# Test credentials manually
curl -u "$API_KEY:$API_PASSWORD" "$API_BASE_URL?limit=1"
```

**Common causes:**
1. Wrong API key or password
2. Incorrect API_BASE_URL format
3. Network/firewall blocking connection
4. Cloudant service down

**Solution:**
```bash
# Verify URL format
# Correct: https://instance.cloudant.com/db/_design/design/_view/view
# Wrong: https://instance.cloudant.com/db (missing view path)

# Test with curl
curl -v -u "$API_KEY:$API_PASSWORD" "$API_BASE_URL?limit=1"

# Check for SSL issues
curl -k -u "$API_KEY:$API_PASSWORD" "$API_BASE_URL?limit=1"
```

### CORS Errors

**Issue:** Browser shows CORS policy errors

```
Access to XMLHttpRequest at 'http://localhost:8000/api/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution:**

Check [`backend/main.py`](backend/main.py:1) CORS configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## ⚡ Performance Issues

### Slow Retrieval Start

**Issue:** Takes 5-10 seconds to start

**Diagnosis:**
```python
# Check if using asyncio.create_task()
# In backend/retrieval_worker.py:
job.task = asyncio.create_task(self._run_retrieval(job))  # ✅ Correct
# NOT:
await self._run_retrieval(job)  # ❌ Wrong - blocks
```

**Solution:**

Verify [`backend/retrieval_worker.py`](backend/retrieval_worker.py:1) line ~95:

```python
async def start_job(self, job_id: str):
    job = self.jobs.get(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    
    # THIS MUST RETURN IMMEDIATELY
    job.task = asyncio.create_task(self._run_retrieval(job))
    job.status = "running"
    job.start_time = time.time()
```

### Low Throughput

**Issue:** Only getting 100-500 records/sec

**Solutions:**

1. **Increase batch size** in [`.env`](.env:1):
```env
BATCH_SIZE=10000  # Default is 5000
```

2. **Increase concurrent requests** in [`backend/config.py`](backend/config.py:1):
```python
MAX_CONCURRENT_REQUESTS = 5  # Default is 3
```

3. **Check network latency**:
```bash
# Test API response time
time curl -u "$API_KEY:$API_PASSWORD" "$API_BASE_URL?limit=5000"
```

### High Memory Usage

**Issue:** Memory grows continuously

**Diagnosis:**
```python
# Check for memory accumulation
# WRONG:
all_records = []
for batch in batches:
    all_records.extend(batch)  # ❌ Accumulates in memory

# CORRECT:
for batch in batches:
    await writer.write_batch(batch)  # ✅ Streaming
```

**Solution:**

Verify streaming writes in [`backend/file_writer.py`](backend/file_writer.py:1):

```python
async def write_batch(self, records: List[Dict]) -> int:
    # Append mode - no accumulation
    async with aiofiles.open(self.filepath, mode='a') as f:
        for record in records:
            await f.write(json.dumps(record) + '\n')
```

## 🎨 UI Issues

### Status Section Not Appearing

**Issue:** Status doesn't show after clicking Start

**Diagnosis:**

Check [`frontend/src/App.jsx`](frontend/src/App.jsx:1) line ~120:

```javascript
// Status should appear immediately
{(isRunning || jobStatus) && (
  <StatusSection
    status={jobStatus}
    isRunning={isRunning}
  />
)}
```

**Solution:**

Ensure `isRunning` is set to `true` immediately in `handleStart`:

```javascript
const handleStart = async (compress = false) => {
  const response = await startRetrieval(...);
  setCurrentJob(response.job);
  setJobStatus(response.job);
  setIsRunning(true);  // ✅ Set immediately
};
```

### Status Section Above Date Selection

**Issue:** Status appears in wrong position

**Solution:**

Check component order in [`frontend/src/App.jsx`](frontend/src/App.jsx:1):

```javascript
{/* CORRECT ORDER */}
<DateTimeSelector ... />
<ControlPanel ... />
{/* Status MUST be here - BELOW controls */}
{(isRunning || jobStatus) && <StatusSection ... />}
<HistorySection ... />
```

### Data Viewer Not Loading

**Issue:** Modal opens but shows loading forever

**Diagnosis:**
```bash
# Check backend endpoint
curl http://localhost:8000/api/retrieval/view/job_xxx?page=1&page_size=100
```

**Solution:**

1. Verify job is completed
2. Check file exists in `data/` directory
3. Check browser console for errors
4. Verify API endpoint in [`frontend/src/api/retrieval.js`](frontend/src/api/retrieval.js:1)

## 🔒 Security Issues

### .env File Exposed

**Issue:** .env file committed to git

**Solution:**
```bash
# Remove from git history
git rm --cached .env
git commit -m "Remove .env from tracking"

# Verify .gitignore includes .env
cat .gitignore | grep .env

# Rotate all credentials immediately
```

### SSL Certificate Errors

**Issue:** SSL verification failed

**Temporary solution (development only):**
```python
# In backend/cloudant_client.py
connector = aiohttp.TCPConnector(
    ssl=False  # ⚠️ Development only!
)
```

**Proper solution:**
```bash
# Update certificates
# macOS:
/Applications/Python\ 3.11/Install\ Certificates.command

# Ubuntu:
sudo apt-get install ca-certificates
sudo update-ca-certificates

# Windows:
# Download from: https://curl.se/docs/caextract.html
```

## 📊 Data Issues

### Incomplete Data

**Issue:** Retrieval stops before completion

**Diagnosis:**
```bash
# Check logs
tail -f backend.log

# Check checkpoint
cat checkpoints/job_xxx.checkpoint
```

**Solution:**

1. Check for API rate limits
2. Verify network stability
3. Check disk space
4. Review error logs

### Corrupted Files

**Issue:** Cannot read .jsonl file

**Diagnosis:**
```bash
# Check file integrity
head -n 10 data/job_xxx.jsonl
tail -n 10 data/job_xxx.jsonl

# Check for invalid JSON
python -c "
import json
with open('data/job_xxx.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except:
            print(f'Error on line {i}')
"
```

**Solution:**

1. Delete corrupted file
2. Restart retrieval
3. Check for disk errors

## 🧪 Testing Issues

### Cannot Run Tests

**Issue:** pytest not found

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v
```

## 🐳 Docker Issues

### Container Won't Start

**Issue:** Docker build fails

```bash
# Check Docker is running
docker ps

# Build with verbose output
docker build -t cloudant-retrieval . --progress=plain

# Check logs
docker logs <container-id>
```

## 📞 Getting More Help

If issues persist:

1. **Check logs:**
   ```bash
   # Backend logs
   tail -f backend.log
   
   # Frontend logs
   # Check browser console (F12)
   ```

2. **Enable debug mode:**
   ```python
   # In backend/main.py
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Create GitHub issue with:**
   - Operating system and version
   - Python version (`python --version`)
   - Node.js version (`node --version`)
   - Full error message
   - Steps to reproduce
   - Relevant log excerpts

4. **Check existing issues:**
   - Search GitHub issues
   - Review closed issues for solutions

---

**Most issues can be resolved by using a virtual environment and following the setup guide carefully.**