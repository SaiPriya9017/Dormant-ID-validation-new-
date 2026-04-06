# 🚀 Cloudant Retrieval System v2.0

A high-performance data retrieval system for IBM Cloudant with enterprise-grade UI built using IBM Carbon Design System.

## ✨ Features

- ⚡ **Instant Start** - Retrieval begins immediately (< 1 second)
- 🧠 **Memory Efficient** - Streaming architecture, no buffering
- 📊 **Real-time Progress** - Live status updates via SSE
- 🎨 **Enterprise UI** - IBM Carbon Design System
- 💾 **Smart Checkpointing** - Resume capability for interrupted jobs
- 📦 **Compression Support** - Optional gzip compression
- 🔍 **Data Viewer** - Paginated in-browser data viewing
- 📥 **Easy Downloads** - Direct file downloads

## 🏗️ Architecture

### Backend (FastAPI + Async)
- **Bookmark-based pagination** (no skip-based queries)
- **Async streaming** with `aiohttp`
- **Background workers** using `asyncio.create_task()`
- **Streaming file writes** (append-only, no memory accumulation)
- **Automatic checkpointing** every 10 batches

### Frontend (React + Carbon)
- **IBM Carbon Design System** components
- **Real-time status updates** (1-second polling)
- **Instant UI feedback** (status appears immediately)
- **Paginated data viewer** (100/500/1000 rows per page)
- **Download management** with compression support

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- IBM Cloudant account with API credentials

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd cloudant-retrieval-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your Cloudant credentials
nano .env  # or use your preferred editor
```

**Required Configuration:**

```env
# IBM Cloudant API Configuration
API_BASE_URL=https://your-instance.cloudant.com/your-db/_design/your-design/_view/your-view
API_KEY=your-api-key-here
API_PASSWORD=your-api-password-here

# Application Settings (optional)
DATA_DIR=./data
CHECKPOINT_DIR=./checkpoints
BATCH_SIZE=5000
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
# From project root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
# From project root
cd frontend
npm run dev
```

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

## 📖 Usage Guide

### Starting a Retrieval

1. **Select Date Range**
   - Choose start and end dates using the date picker
   - Optionally set specific times (defaults to 00:00:00 and 23:59:59)

2. **Start Retrieval**
   - Click "Start Retrieval" for uncompressed output
   - Click "Start with Compression" for gzip-compressed output
   - Status section appears **instantly** (before any data is fetched)

3. **Monitor Progress**
   - Real-time updates every second
   - View records fetched, records/sec, progress %, and estimated time
   - Progress bar shows visual completion status

4. **Stop if Needed**
   - Click "Stop Retrieval" to gracefully halt the process
   - Checkpoint is saved automatically
   - Can resume later (feature in development)

### Viewing History

- All retrieval jobs appear in the History section
- Each row shows:
  - Job ID
  - Date range
  - Status (Running/Completed/Failed/Stopped)
  - Records fetched

### Viewing Data

1. Click the **View** icon (👁️) for any completed job
2. Modal opens with paginated data table
3. Use pagination controls to navigate:
   - 100, 500, or 1000 rows per page
   - Previous/Next page buttons

### Downloading Data

1. Click the **Download** icon (⬇️) for any completed job
2. File downloads automatically:
   - `.jsonl` for uncompressed
   - `.jsonl.gz` for compressed

## 🔧 Configuration

### Backend Settings

Edit [`backend/config.py`](backend/config.py:1) to customize:

```python
BATCH_SIZE = 5000  # Records per API request
MAX_CONCURRENT_REQUESTS = 3  # Parallel request limit
REQUEST_TIMEOUT = 30  # Seconds
```

### Frontend Settings

Edit [`frontend/vite.config.js`](frontend/vite.config.js:1) for proxy settings:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## 📁 Project Structure

```
cloudant-retrieval-system/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── cloudant_client.py   # Cloudant API client
│   ├── file_writer.py       # Streaming file writer
│   └── retrieval_worker.py  # Background worker
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── api/            # API client
│   │   ├── App.jsx         # Main application
│   │   └── main.jsx        # Entry point
│   ├── package.json
│   └── vite.config.js
├── .env.example            # Environment template
├── .gitignore
├── requirements.txt        # Python dependencies
└── README.md
```

## ⚡ Performance Optimizations

### Backend
- ✅ Bookmark-based pagination (no skip queries)
- ✅ Reusable `aiohttp.ClientSession`
- ✅ Streaming writes (no memory accumulation)
- ✅ Background task execution (`asyncio.create_task()`)
- ✅ Checkpoint every 10 batches (not every record)

### Frontend
- ✅ Instant UI updates (status appears before data fetch)
- ✅ Efficient polling (1-second intervals)
- ✅ Lazy data loading (paginated viewer)
- ✅ Optimized re-renders (React best practices)

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Verify Python dependencies
pip list | grep fastapi
```

### Frontend won't start
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Slow retrieval start
- Verify you're using `asyncio.create_task()` in [`backend/retrieval_worker.py`](backend/retrieval_worker.py:1)
- Check that API endpoint returns immediately
- Ensure background worker is not blocking

### Connection errors
- Verify `.env` credentials are correct
- Test Cloudant API manually:
  ```bash
  curl -u "$API_KEY:$API_PASSWORD" "$API_BASE_URL?limit=1"
  ```

## 🔒 Security Notes

- Never commit `.env` file to version control
- Use environment variables for all credentials
- Rotate API keys regularly
- Consider using IAM authentication for production

## 📊 API Endpoints

### Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/retrieval/start` | POST | Start new retrieval job |
| `/api/retrieval/status/{job_id}` | GET | Get job status |
| `/api/retrieval/stop/{job_id}` | POST | Stop running job |
| `/api/retrieval/stream/{job_id}` | GET | SSE status stream |
| `/api/retrieval/history` | GET | List all jobs |
| `/api/retrieval/download/{job_id}` | GET | Download data file |
| `/api/retrieval/view/{job_id}` | GET | View paginated data |

## 🎯 Performance Benchmarks

Expected performance on standard hardware:

- **Start Time**: < 1 second
- **Throughput**: 5,000-10,000 records/sec
- **Memory Usage**: < 100 MB (streaming)
- **20M Records**: ~30-60 minutes

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- IBM Carbon Design System
- FastAPI framework
- React community

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check existing documentation
- Review troubleshooting section

---

**Built with ❤️ using IBM Carbon Design System**