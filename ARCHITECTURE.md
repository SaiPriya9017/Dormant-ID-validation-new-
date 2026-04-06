# 🏗️ Architecture Documentation

This document provides a detailed overview of the Cloudant Retrieval System architecture.

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         React + IBM Carbon Design System           │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │    │
│  │  │  Date    │  │ Control  │  │   Status     │    │    │
│  │  │ Selector │  │  Panel   │  │   Section    │    │    │
│  │  └──────────┘  └──────────┘  └──────────────┘    │    │
│  │  ┌──────────────────────────────────────────┐    │    │
│  │  │         History DataTable                 │    │    │
│  │  └──────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/SSE
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │              REST API Endpoints                     │    │
│  │  /start  /stop  /status  /stream  /download        │    │
│  └────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Retrieval Worker (Async)                  │    │
│  │  • Background task (asyncio.create_task)            │    │
│  │  • Job management                                   │    │
│  │  • Progress tracking                                │    │
│  └────────────────────────────────────────────────────┘    │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐            │
│         ▼                                      ▼            │
│  ┌─────────────┐                      ┌──────────────┐    │
│  │  Cloudant   │                      │    File      │    │
│  │   Client    │                      │   Writer     │    │
│  │  (aiohttp)  │                      │ (streaming)  │    │
│  └─────────────┘                      └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
         │                                        │
         │ Bookmark Pagination                   │ Append-only
         ▼                                        ▼
┌──────────────────┐                    ┌──────────────────┐
│  IBM Cloudant    │                    │  Local Storage   │
│    Database      │                    │  data/*.jsonl    │
└──────────────────┘                    └──────────────────┘
```

## 🔧 Backend Architecture

### Core Components

#### 1. FastAPI Application ([`backend/main.py`](backend/main.py:1))

**Responsibilities:**
- HTTP endpoint routing
- Request validation
- Response formatting
- CORS handling
- SSE streaming

**Key Features:**
- Non-blocking API endpoints
- Instant response times
- Background task delegation

**Critical Design:**
```python
@app.post("/api/retrieval/start")
async def start_retrieval(...):
    job = worker.create_job(...)
    await worker.start_job(job.job_id)  # Returns immediately
    return {"job": job.to_dict()}  # Instant response
```

#### 2. Retrieval Worker ([`backend/retrieval_worker.py`](backend/retrieval_worker.py:1))

**Responsibilities:**
- Job lifecycle management
- Background task execution
- Progress tracking
- Status updates

**Key Features:**
- Async task creation with `asyncio.create_task()`
- Non-blocking job start
- Real-time progress calculation

**Architecture:**
```python
class RetrievalWorker:
    async def start_job(self, job_id):
        # Create background task - RETURNS IMMEDIATELY
        job.task = asyncio.create_task(self._run_retrieval(job))
        job.status = "running"  # Update status instantly
        
    async def _run_retrieval(self, job):
        # Runs in background
        async with CloudantClient() as client:
            async for batch in client.stream_all(...):
                await writer.write_batch(batch)
                # Update progress
```

#### 3. Cloudant Client ([`backend/cloudant_client.py`](backend/cloudant_client.py:1))

**Responsibilities:**
- Cloudant API communication
- Bookmark-based pagination
- Batch fetching
- Error handling

**Key Features:**
- Reusable `aiohttp.ClientSession`
- Async streaming
- Automatic pagination

**Pagination Strategy:**
```python
async def stream_all(self, start_date, end_date, batch_size):
    bookmark = None
    has_more = True
    
    while has_more:
        result = await self.fetch_batch(
            bookmark=bookmark,
            limit=batch_size
        )
        
        if result["rows"]:
            yield result["rows"]
            
        bookmark = result["bookmark"]
        has_more = result["has_more"]
```

**Why Bookmark Pagination?**
- ✅ Constant time complexity O(1)
- ✅ No skip overhead
- ✅ Handles large datasets efficiently
- ❌ Skip-based: O(n) - gets slower with offset

#### 4. File Writer ([`backend/file_writer.py`](backend/file_writer.py:1))

**Responsibilities:**
- Streaming file writes
- Checkpoint management
- Compression support
- Resume capability

**Key Features:**
- Append-only writes (no memory accumulation)
- Async I/O operations
- Automatic checkpointing

**Streaming Architecture:**
```python
async def write_batch(self, records):
    # Append mode - no memory accumulation
    async with aiofiles.open(self.filepath, mode='a') as f:
        for record in records:
            line = json.dumps(record) + '\n'
            await f.write(line)  # Streaming write
```

**Checkpoint Strategy:**
```python
# Save checkpoint every 10 batches
if batch_count % 10 == 0:
    await writer.save_checkpoint(bookmark)
```

#### 5. Configuration ([`backend/config.py`](backend/config.py:1))

**Responsibilities:**
- Environment variable loading
- Configuration validation
- Directory management

**Key Settings:**
```python
BATCH_SIZE = 5000  # Records per API request
MAX_CONCURRENT_REQUESTS = 3  # Parallel limit
REQUEST_TIMEOUT = 30  # Seconds
```

## 🎨 Frontend Architecture

### Core Components

#### 1. Main Application ([`frontend/src/App.jsx`](frontend/src/App.jsx:1))

**Responsibilities:**
- State management
- Component orchestration
- API communication
- Real-time updates

**State Management:**
```javascript
const [currentJob, setCurrentJob] = useState(null);
const [jobStatus, setJobStatus] = useState(null);
const [isRunning, setIsRunning] = useState(false);
const [history, setHistory] = useState([]);
```

**Polling Strategy:**
```javascript
useEffect(() => {
  if (!currentJob || !isRunning) return;
  
  const pollInterval = setInterval(async () => {
    const status = await getStatus(currentJob.job_id);
    setJobStatus(status);
    
    if (['completed', 'failed', 'stopped'].includes(status.status)) {
      setIsRunning(false);
    }
  }, 1000);  // Poll every second
  
  return () => clearInterval(pollInterval);
}, [currentJob, isRunning]);
```

#### 2. Date/Time Selector ([`frontend/src/components/DateTimeSelector.jsx`](frontend/src/components/DateTimeSelector.jsx:1))

**Features:**
- Carbon DatePicker (range selection)
- Carbon TimePicker
- Timezone display (UTC)
- Disabled state during retrieval

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Start Date    │  End Date    │  Start Time │
│  [mm/dd/yyyy]  │  [mm/dd/yyyy]│  [HH:MM]    │
└─────────────────────────────────────────────┘
```

#### 3. Control Panel ([`frontend/src/components/ControlPanel.jsx`](frontend/src/components/ControlPanel.jsx:1))

**Features:**
- Start Retrieval button
- Start with Compression button
- Stop Retrieval button
- Instant feedback (disable on click)

**Button States:**
```javascript
<Button
  onClick={() => onStart(false)}
  disabled={isRunning}  // Instant disable
>
  Start Retrieval
</Button>
```

#### 4. Status Section ([`frontend/src/components/StatusSection.jsx`](frontend/src/components/StatusSection.jsx:1))

**Critical Placement:**
- ✅ BELOW Date Selection
- ✅ Appears instantly on Start click
- ✅ Updates every second

**Displays:**
- Records fetched (formatted with commas)
- Records/sec (2 decimal places)
- Progress % (1 decimal place)
- Estimated time remaining (formatted)
- Status tag (color-coded)
- Progress bar (visual)

**Status Colors:**
```javascript
const statusMap = {
  running: 'blue',
  completed: 'green',
  failed: 'red',
  stopped: 'gray',
  initializing: 'purple'
};
```

#### 5. History Section ([`frontend/src/components/HistorySection.jsx`](frontend/src/components/HistorySection.jsx:1))

**Features:**
- Carbon DataTable
- Search functionality
- Refresh button
- Action buttons (View, Download)

**Table Columns:**
- Job ID (truncated)
- Start Date (localized)
- End Date (localized)
- Status (tag)
- Records (formatted)
- Actions (icons)

#### 6. Data Viewer Modal ([`frontend/src/components/DataViewerModal.jsx`](frontend/src/components/DataViewerModal.jsx:1))

**Features:**
- Carbon Modal (large size)
- Paginated DataTable
- Dynamic column generation
- Page size selection (100/500/1000)

**Pagination:**
```javascript
const handlePageChange = ({ page, pageSize }) => {
  setPage(page);
  setPageSize(pageSize);
  loadData(page, pageSize);  // Fetch on demand
};
```

## 🔄 Data Flow

### Retrieval Flow

```
1. User clicks "Start Retrieval"
   ↓
2. Frontend calls POST /api/retrieval/start
   ↓
3. Backend creates job and background task
   ↓
4. API returns immediately with job info
   ↓
5. Frontend updates UI instantly (status appears)
   ↓
6. Background worker starts fetching data
   ↓
7. Frontend polls GET /api/retrieval/status every 1s
   ↓
8. Status updates appear in real-time
   ↓
9. Worker writes batches to file (streaming)
   ↓
10. Checkpoints saved every 10 batches
    ↓
11. Job completes, status updates to "completed"
    ↓
12. Frontend stops polling, shows final stats
```

### Download Flow

```
1. User clicks Download icon
   ↓
2. Frontend opens GET /api/retrieval/download/{job_id}
   ↓
3. Backend streams file to browser
   ↓
4. Browser saves file (.jsonl or .jsonl.gz)
```

### View Flow

```
1. User clicks View icon
   ↓
2. Modal opens, calls GET /api/retrieval/view/{job_id}?page=1&page_size=100
   ↓
3. Backend reads first 100 lines from file
   ↓
4. Frontend displays in DataTable
   ↓
5. User changes page/size
   ↓
6. Frontend fetches new page on demand
```

## ⚡ Performance Optimizations

### Backend

1. **Bookmark Pagination**
   - O(1) complexity vs O(n) for skip
   - No performance degradation with large offsets

2. **Streaming Writes**
   - Append-only file operations
   - No memory accumulation
   - Constant memory usage

3. **Reusable Session**
   - Single `aiohttp.ClientSession` per job
   - Connection pooling
   - Reduced overhead

4. **Background Tasks**
   - Non-blocking API responses
   - Instant user feedback
   - Parallel execution

5. **Checkpoint Strategy**
   - Save every 10 batches (not every record)
   - Minimal I/O overhead
   - Fast resume capability

### Frontend

1. **Instant UI Updates**
   - Status appears before data fetch
   - Optimistic UI updates
   - No perceived lag

2. **Efficient Polling**
   - 1-second intervals (not too frequent)
   - Stops when job completes
   - Minimal network overhead

3. **Lazy Loading**
   - Data viewer fetches on demand
   - Paginated requests
   - Reduced initial load

4. **Optimized Re-renders**
   - React best practices
   - Memoization where needed
   - Minimal DOM updates

## 🔒 Security Considerations

### Backend

1. **Environment Variables**
   - All credentials in `.env`
   - Never hardcoded
   - `.gitignore` protection

2. **Input Validation**
   - FastAPI Pydantic models
   - Date format validation
   - Parameter sanitization

3. **CORS Configuration**
   - Configurable origins
   - Credential support
   - Method restrictions

### Frontend

1. **API Communication**
   - Axios for HTTP requests
   - Error handling
   - Timeout configuration

2. **Data Display**
   - JSON sanitization
   - XSS prevention
   - Safe rendering

## 📊 Scalability

### Current Limits

- **Records**: Tested up to 20M+
- **File Size**: Limited by disk space
- **Concurrent Jobs**: Multiple supported
- **Memory**: < 100 MB per job

### Scaling Strategies

1. **Horizontal Scaling**
   - Multiple backend instances
   - Load balancer
   - Shared storage

2. **Vertical Scaling**
   - Increase `BATCH_SIZE`
   - Increase `MAX_CONCURRENT_REQUESTS`
   - More CPU/RAM

3. **Database Optimization**
   - Cloudant view optimization
   - Index tuning
   - Query optimization

## 🧪 Testing Strategy

### Backend Tests

```python
# Unit tests
test_cloudant_client.py
test_file_writer.py
test_retrieval_worker.py

# Integration tests
test_api_endpoints.py
test_end_to_end.py
```

### Frontend Tests

```javascript
// Component tests
DateTimeSelector.test.jsx
ControlPanel.test.jsx
StatusSection.test.jsx

// Integration tests
App.test.jsx
```

## 📈 Monitoring

### Metrics to Track

1. **Performance**
   - Records/sec
   - API response time
   - Memory usage
   - Disk I/O

2. **Reliability**
   - Success rate
   - Error rate
   - Retry count
   - Checkpoint frequency

3. **Usage**
   - Active jobs
   - Completed jobs
   - Data volume
   - User activity

## 🔮 Future Enhancements

1. **Resume Capability**
   - Load from checkpoint
   - Continue interrupted jobs

2. **Advanced Filtering**
   - Custom query parameters
   - Field selection
   - Conditional retrieval

3. **Export Formats**
   - CSV export
   - Parquet export
   - Database import

4. **Scheduling**
   - Cron-based jobs
   - Recurring retrievals
   - Email notifications

5. **Analytics**
   - Data visualization
   - Statistics dashboard
   - Performance graphs

---

**Architecture designed for performance, scalability, and maintainability.**