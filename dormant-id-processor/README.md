# 🔍 Dormant-ID Processing System

A scalable, fault-tolerant data processing pipeline for processing 21M+ user IDs across multiple JSONL files.

## 🎯 Features

- ✅ Multi-file JSONL processing with streaming
- ✅ Batch processing (50-100 IDs per batch)
- ✅ Controlled concurrency (5-10 parallel API calls)
- ✅ Automatic token management and refresh
- ✅ Retry logic with exponential backoff
- ✅ Per-file checkpointing (resume capability)
- ✅ Real-time progress tracking
- ✅ Comprehensive error handling
- ✅ Modular API service architecture
- ✅ Production-grade logging

## 📁 Project Structure

```
dormant-id-processor/
├── main.py                 # Entry point
├── config.py              # Configuration
├── api_service.py         # All API interactions (ISOLATED)
├── file_processor.py      # File reading and processing
├── batch_processor.py     # Batching logic
├── checkpoint_manager.py  # Checkpointing system
├── output_writer.py       # Result writing
├── logger.py              # Logging setup
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── input/                # Input JSONL files
├── output/               # Processed results
├── checkpoints/          # Resume data
└── logs/                 # Application logs
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API credentials
```

### 3. Prepare Input Files

Place your `.jsonl` files in the `input/` directory:

```
input/
├── batch_1.jsonl
├── batch_2.jsonl
└── batch_3.jsonl
```

### 4. Run Processing

```bash
# Process all files in input directory
python main.py

# Process specific directory
python main.py --input-dir /path/to/files

# Custom batch size
python main.py --batch-size 100

# Custom concurrency
python main.py --concurrency 10

# Resume from checkpoint
python main.py --resume
```

## 📊 Output Format

Results are saved as JSONL files in `output/`:

```json
{"id": "123456789", "email": "user@example.com", "status": "ACTIVE"}
{"id": "987654321", "email": "inactive@example.com", "status": "DORMANT"}
```

## 🔧 Configuration

Edit `.env`:

```env
# API Endpoints
TOKEN_API_URL=https://api.example.com/token
EMAIL_API_URL=https://api.example.com/users
BLUEPAGES_API_URL=https://api.example.com/bluepages

# API Credentials
API_CLIENT_ID=your_client_id
API_CLIENT_SECRET=your_client_secret

# Processing Settings
BATCH_SIZE=50
CONCURRENCY=5
MAX_RETRIES=3
RETRY_DELAY=2
```

## 📈 Performance

- **Throughput**: ~1000-2000 IDs/minute (depends on API limits)
- **Memory**: < 200 MB (streaming processing)
- **Fault Tolerance**: Automatic retry + checkpointing
- **Scalability**: Handles 21M+ records efficiently

## 🛡️ Error Handling

- Automatic retry on failures (max 3 attempts)
- Failed IDs logged to `logs/failed_ids.log`
- Checkpoint saved every 1000 records
- Resume from last checkpoint on restart

## 📝 Logging

Logs are saved to `logs/`:

- `app.log` - General application logs
- `failed_ids.log` - Failed ID processing
- `api_errors.log` - API-specific errors

## 🔍 Monitoring

Real-time progress display:

```
Processing: batch_1.jsonl
Progress: 45,230 / 100,000 (45.23%)
Success: 44,890 | Failed: 340
Rate: 1,234 IDs/min
ETA: 45 minutes
```

## 🧪 Testing

```bash
# Run with sample data
python main.py --input-dir ./test_data --batch-size 10

# Dry run (no API calls)
python main.py --dry-run
```

## 📚 Architecture

### API Service Module (`api_service.py`)

All API interactions are isolated in this module:

- `get_token()` - Fetch and cache authentication token
- `get_emails(batch_ids)` - Retrieve emails for ID batch
- `get_user_status(email)` - Check ACTIVE/DORMANT status
- Automatic token refresh on expiry
- Built-in retry logic

### Processing Flow

```
Input Files → Stream Reader → Batch Creator → API Service → Output Writer
                                    ↓
                            Checkpoint Manager
```

## 🔐 Security

- API credentials stored in `.env` (not committed)
- Token cached in memory (not persisted)
- Secure HTTPS connections
- No sensitive data in logs

## 🤝 Contributing

This is a production-grade system. Follow these principles:

- Keep API logic in `api_service.py`
- Use async/await for I/O operations
- Add comprehensive error handling
- Update tests for new features
- Document all changes

## 📞 Support

For issues or questions, check:

1. Logs in `logs/` directory
2. Failed IDs in `logs/failed_ids.log`
3. Checkpoint status in `checkpoints/`

---

**Built for scale, designed for reliability.**