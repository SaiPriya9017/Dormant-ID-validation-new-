# Dormant ID Processor - Usage Guide

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to project directory
cd dormant-id-processor

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your IBM credentials
nano .env
```

Required configuration:
```env
TOKEN_URL=https://login.ibm.com/v1.0/endpoint/default/token
USERS_API_URL=https://login.ibm.com/v2.0/Users
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
```

### 3. Prepare Input Files

Place your JSONL files in the `input/` directory. Each line should contain:

```json
{"user_id": "username@ibm.com"}
```

Example:
```bash
# Create sample file
cat > input/users_batch1.jsonl << EOF
{"user_id": "user1@ibm.com"}
{"user_id": "user2@ibm.com"}
{"user_id": "user3@ibm.com"}
EOF
```

### 4. Run Processing

```bash
# Basic usage (default settings)
python main.py

# Custom settings
python main.py --batch-size 100 --concurrency 10

# Start fresh (ignore checkpoints)
python main.py --no-resume

# Clear all checkpoints
python main.py --clear-checkpoints
```

---

## 📋 Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input-dir` | `./input` | Directory containing input JSONL files |
| `--batch-size` | `50` | Number of IDs to process per batch |
| `--concurrency` | `5` | Number of concurrent API calls |
| `--no-resume` | `False` | Start from beginning (ignore checkpoints) |
| `--clear-checkpoints` | `False` | Clear all checkpoints before starting |

---

## 📊 Output Format

Results are written to `output/` directory as JSONL files:

```json
{
  "user_id": "user1@ibm.com",
  "email": "user1@ibm.com",
  "status": "ACTIVE"
}
```

Possible status values:
- `"ACTIVE"` - User is active
- `"DORMANT"` - User is dormant/inactive
- `null` - User not found or error occurred

---

## 🔄 Resume Capability

The system automatically saves checkpoints every batch. If processing is interrupted:

```bash
# Simply run again - it will resume from last checkpoint
python main.py
```

To start fresh:
```bash
python main.py --no-resume
```

---

## 📈 Performance Tuning

### For Large Datasets (21M+ records)

```bash
# Increase batch size and concurrency
python main.py --batch-size 100 --concurrency 10
```

### For Rate-Limited APIs

```bash
# Reduce concurrency to avoid rate limits
python main.py --batch-size 50 --concurrency 3
```

### Memory Optimization

The system uses streaming processing - memory usage stays constant regardless of file size (typically < 200 MB).

---

## 🔍 Monitoring Progress

### Real-Time Progress

The CLI shows:
- Current file being processed
- Progress bar with ETA
- Records processed per second
- Live statistics

### Log Files

Check `logs/` directory for detailed logs:
```bash
# View latest log
tail -f logs/dormant-id-processor_*.log
```

### Checkpoints

Check processing status:
```bash
# List all checkpoints
ls -lh checkpoints/
```

---

## 🛠️ Troubleshooting

### Authentication Errors

```
Error: Missing required configuration: CLIENT_ID
```

**Solution**: Ensure `.env` file has all required credentials.

### API Rate Limiting

```
Error: 429 Too Many Requests
```

**Solution**: Reduce `--concurrency` value:
```bash
python main.py --concurrency 3
```

### Token Expiration

The system automatically refreshes tokens. If you see repeated 401 errors:

**Solution**: Verify your `CLIENT_ID` and `CLIENT_SECRET` are correct.

### Out of Memory

```
MemoryError: Unable to allocate array
```

**Solution**: This shouldn't happen with streaming processing. If it does:
1. Check if other processes are consuming memory
2. Reduce `--batch-size` to 25

### File Not Found

```
Error: No JSONL files found in ./input
```

**Solution**: Ensure input files:
1. Are in the `input/` directory
2. Have `.jsonl` extension
3. Contain valid JSON (one object per line)

---

## 📁 Directory Structure

```
dormant-id-processor/
├── input/              # Place input JSONL files here
├── output/             # Results written here
├── checkpoints/        # Resume checkpoints stored here
├── logs/               # Log files
├── .env                # Your configuration (create from .env.example)
├── main.py             # Main entry point
└── *.py                # Other modules
```

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use environment-specific credentials** - Different for dev/prod
3. **Rotate credentials regularly** - Update CLIENT_SECRET periodically
4. **Restrict file permissions**:
   ```bash
   chmod 600 .env
   ```

---

## 📊 Example Workflow

### Processing 21M Records

```bash
# 1. Prepare input files (split into manageable chunks if needed)
ls -lh input/
# users_batch1.jsonl (5M records)
# users_batch2.jsonl (5M records)
# users_batch3.jsonl (5M records)
# users_batch4.jsonl (6M records)

# 2. Start processing with optimal settings
python main.py --batch-size 100 --concurrency 10

# 3. Monitor progress
# - Watch console output
# - Check logs: tail -f logs/dormant-id-processor_*.log

# 4. If interrupted, simply restart
python main.py

# 5. Results available in output/
ls -lh output/
# users_batch1_results_20260403_120000.jsonl
# users_batch2_results_20260403_130000.jsonl
# ...
```

---

## 🎯 Performance Expectations

| Dataset Size | Batch Size | Concurrency | Estimated Time |
|--------------|------------|-------------|----------------|
| 100K records | 50 | 5 | ~30 minutes |
| 1M records | 100 | 10 | ~3 hours |
| 10M records | 100 | 10 | ~30 hours |
| 21M records | 100 | 10 | ~60 hours |

*Times vary based on API response times and network conditions*

---

## 💡 Tips

1. **Test with small files first** - Use `sample_users.jsonl` to verify setup
2. **Monitor API quotas** - Check your IBM API usage limits
3. **Use screen/tmux for long runs** - Prevents interruption if SSH disconnects
4. **Backup checkpoints** - Copy `checkpoints/` directory periodically
5. **Validate output** - Spot-check results before processing entire dataset

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs in `logs/` directory
2. Review this guide's troubleshooting section
3. Verify `.env` configuration
4. Test with sample data first
5. Check IBM API status/documentation

---

## 📝 Notes

- The system processes files sequentially (one at a time)
- Within each file, batches are processed with controlled concurrency
- Checkpoints are per-file, allowing independent resume
- Output files are timestamped to prevent overwrites
- All API interactions are in `api_service.py` for easy maintenance