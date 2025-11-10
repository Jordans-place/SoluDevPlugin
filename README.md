# SoluDev Plugin - Anecdotes Integration

A Python plugin that automatically collects user and role data from SoluDev and pushes it as evidence to the Anecdotes platform. Designed for weekly scheduled execution with robust error handling, retry mechanisms, and backup recovery.

## Overview

This plugin serves as a bridge between **SoluDev** (NewSolutions' R&D collaboration tool) and **Anecdotes** (compliance and evidence management platform). It automates the collection and synchronization of:

1. **User Data**: List of users and their assigned roles
2. **Role Data**: List of roles and their associated permissions

The plugin is designed to run on a weekly schedule, ensuring compliance data is always up-to-date in the Anecdotes platform.

### Key Capabilities

- Automated data collection from SoluDev API
- Automatic evidence upload to Anecdotes platform
- Backup and recovery mechanism for failed uploads
- Comprehensive logging for monitoring and debugging
- JWT token management with automatic refresh
- Connection pooling for optimal performance
- Retry logic

## Features

### Core Functionality

- **Dual API Integration**: Seamlessly connects to both SoluDev and Anecdotes APIs
- **Pagination Support**: Handles large datasets with automatic pagination
- **Atomic Operations**: Ensures data consistency with backup mechanism
- **Resilient Design**: Automatic retry on failures with configurable delays

### Reliability Features

- **Backup System**: Saves data locally before upload; retries on failure
- **Token Management**: Automatic JWT token refresh on expiration or 401 errors
- **Error Recovery**: Graceful handling of network issues, API errors, and timeouts
- **Connection Pooling**: Optimized HTTP connection management

### Observability

- **Component-Based Logging**: Separate log files for each component
- **Structured Logging**: Metadata-rich logs for easy debugging
- **Error Tracking**: Detailed error messages with context

## Architecture

### System Flow

```
┌─────────────┐
│   SoluDev   │
│     API     │
└──────┬──────┘
       │
       │ 1. Authenticate & Fetch
       │    - Users (paginated)
       │    - Roles
       ▼
┌─────────────────┐
│  SoluDevPlugin  │
│                 │
│  ┌───────────┐  │
│  │  Backup   │  │
│  │  Storage  │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  Process  │  │
│  │  & Upload │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │
         │ 2. Authenticate & Upload
         │    - Create Evidence Collections
         │    - Attach JSON Files
         ▼
┌─────────────┐
│  Anecdotes  │
│  Platform   │
└─────────────┘
```

### Component Architecture

```
src/
├── auth/              # Anecdotes authentication
│   └── anecdotes_auth.py
├── clients/           # External API clients
│   └── soludev_client.py
├── common/            # Shared utilities
│   ├── config.py      # Configuration management
│   ├── exceptions.py   # Custom exceptions
│   ├── logger.py       # Logging infrastructure
│   ├── models.py       # Data models (Pydantic)
│   └── utils.py       # Utility functions
├── storage/           # Local storage
│   └── local_backup.py
├── uploaders/         # Upload handlers
│   └── anecdotes_uploader.py
└── main.py            # Entry point
```

## Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Linux, macOS, or Windows
- **Network**: Access to SoluDev API and Anecdotes platform

### API Access

- **SoluDev API**: Valid username and API key
- **Anecdotes API**: Valid API key for authentication

### Python Dependencies

All dependencies are listed in `requirements.txt`:
- `dynaconf` - Configuration management
- `pydantic` - Data validation
- `python-dotenv` - Environment variable management
- `requests` - HTTP client
- `urllib3` - HTTP connection pooling and retries

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd SoluDevPlugin
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
# SoluDev API Credentials
SOLUDEV_USERNAME=your_soludev_username
SOLUDEV_API_KEY=your_soludev_api_key
SOLUDEV_BASE_URL=http://your-soludev-server:8080

# Anecdotes API Credentials
ANECDOTES_API_KEY=your_anecdotes_api_key
```

## Configuration

### Configuration File (`config.json`)

#### Service Configuration

```json
{
  "SERVICE": {
    "OUT_DIR_PATH": "./out",                    // Output directory for files
    "BACKUP_FILE_NAME": "backup.json",          // Backup file name
    "USERS_FILE_NAME": "users.json",            // Users data file
    "ROLES_FILE_NAME": "roles.json",            // Roles data file
    "EVIDENCE_IDS_FILE_NAME": "evidence_ids.json", // Evidence ID cache
    "EVIDENCE_NAME_PREFIX": "SoluDev",          // Evidence name prefix
    "RETRY_DELAY_SECONDS": 60,                  // Retry delay on failure
    "JWT_EXPIRY_BUFFER_SECONDS": 3300          // JWT expiry buffer (55 min)
  }
}
```

#### HTTP Configuration

```json
{
  "HTTP": {
    "TIMEOUT_SECONDS": 30,                         // Request timeout
    "ANECDOTES_AUTH_EXCHANGE_URL": "...",          // Anecdotes auth endpoint
    "ANECDOTES_UPLOADER_BASE_URL": "...",          // Anecdotes upload endpoint
    "MIN_POOL_CONNECTIONS": 10,                    // Min connection pool size
    "MAX_POOL_CONNECTIONS": 20                     // Max connection pool size
  }
}
```

#### Logging Configuration

```json
{
  "LOGGING": {
    "MAIN_COMPONENT_NAME": "MAIN",
    "SOLUDEV_CLIENT_NAME": "SOLUDEV_CLIENT",
    "ANECDOTES_UPLOADER_NAME": "ANECDOTES_UPLOADER",
    "AUTH_COMPONENT_NAME": "ANECDOTES_AUTH",
    "BACKUP_COMPONENT_NAME": "LOCAL_BACKUP",
    "COMPONENT_TO_LOG_FILE": {
      "MAIN": "logs/main.log",
      "SOLUDEV_CLIENT": "logs/soludev_client.log",
      "ANECDOTES_UPLOADER": "logs/anecdotes_uploader.log",
      "ANECDOTES_AUTH": "logs/anecdotes_auth.log",
      "LOCAL_BACKUP": "logs/local_backup.log"
    }
  }
}
```

## Usage

### Manual Execution

Run the plugin directly:

```bash
python -m src.main
```

Or:

```bash
python src/main.py
```

## Project Structure

```
SoluDevPlugin/
├── config.json                 # Application configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .env                        # Environment variables (create this)
├── .gitignore                  # Git ignore rules
│
└── src/
    ├── main.py                 # Application entry point
    │
    ├── auth/                   # Authentication modules
    │   └── anecdotes_auth.py  # Anecdotes JWT authentication
    │
    ├── clients/                # External API clients
    │   └── soludev_client.py  # SoluDev API client
    │
    ├── common/                 # Shared utilities
    │   ├── config.py          # Configuration loader
    │   ├── exceptions.py      # Custom exceptions
    │   ├── logger.py          # Logging infrastructure
    │   ├── models.py          # Data models (User, Role)
    │   └── utils.py           # Utility functions
    │
    ├── storage/                # Local storage
    │   └── local_backup.py    # Backup management
    │
    ├── uploaders/              # Upload handlers
    │   └── anecdotes_uploader.py # Anecdotes upload handler
    │
    ├── logs/                   # Log files (auto-generated)
    │   ├── main.log
    │   ├── soludev_client.log
    │   ├── anecdotes_uploader.log
    │   ├── anecdotes_auth.log
    │   └── local_backup.log
    │
    └── out/                    # Output files (auto-generated)
        ├── users.json
        ├── roles.json
        ├── backup.json
        └── evidence_ids.json
```

## API Integration Details

### SoluDev API Integration

#### Authentication

The plugin authenticates with SoluDev using username and API key:

```http
POST /login
Content-Type: application/json

{
  "username": "your_username",
  "api_key": "your_api_key"
}

Response:
{
  "token": "bearer_token_here"
}
```

#### Endpoints Used

- **GET `/users`**: Retrieves paginated list of users
  - Query Parameters: `page` (integer)
  - Response: `{ "users": [...], "pagination": { "has_next": boolean } }`

- **GET `/roles`**: Retrieves list of roles
  - Response: `{ "roles": [...] }`

### Anecdotes API Integration

#### Authentication

The plugin exchanges API key for JWT token:

```http
GET /identity/v1/apikey/exchange
Headers:
  x-anecdotes-api-key: your_api_key

Response: "jwt_token_string"
```

#### Endpoints Used

- **POST `/evidence/v1/evidence/create`**: Creates evidence collection
  - Form Data:
    - `service_id`: "SoluDev"
    - `evidence_name`: Evidence name
    - `evidence_help`: Description
    - `empty_state`: Empty state message
    - `is_uar`: "false"
    - `is_sot`: "false"
  - Response: `{ "evidence_id": "uuid" }`

- **POST `/evidence/v1/evidence/{evidence_id}/attach`**: Attaches file to evidence
  - Form Data:
    - `evidence_file`: JSON file
  - Response: 201 Created

## Error Handling & Recovery

### Retry Mechanisms

1. **HTTP Retry**: Built into `requests.Session` via `urllib3.Retry`
   - Retries on: 429, 500, 502, 503, 504
   - Max retries: 5
   - Exponential backoff: 0.5s 

2. **Application-Level Retry**: Main loop retries on any exception
   - Retry delay: 60 seconds (configurable)
   - Continues until success

3. **Authentication Retry**: Automatic token refresh on 401 errors
   - Detects `AnecdotesAuthenticationError`
   - Refreshes JWT token
   - Retries upload immediately

### Backup & Recovery

1. **Backup Creation**: Data is saved to `backup.json` before upload
2. **Recovery**: On restart, plugin checks for backup and retries upload
3. **Cleanup**: Backup is deleted only after successful upload

### Error Types Handled

- **Network Errors**: Connection timeouts, DNS failures
- **HTTP Errors**: 4xx, 5xx status codes
- **Authentication Errors**: Token expiration, invalid credentials
- **Data Errors**: Invalid JSON, missing fields
- **File System Errors**: Permission issues, disk full

## Logging

### Log Structure

Each component has its own log file with structured format:

```
YYYY-MM-DD HH:MM:SS - COMPONENT_NAME - logger - LEVEL - Message | Metadata: {...}
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages (e.g., token refresh)
- **ERROR**: Error messages with context

### Log Files

- `logs/main.log` - Main application flow
- `logs/soludev_client.log` - SoluDev API interactions
- `logs/anecdotes_uploader.log` - Anecdotes upload operations
- `logs/anecdotes_auth.log` - Authentication operations
- `logs/local_backup.log` - Backup operations


## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptom**: `ValueError: ANECDOTES API key is empty`

**Solution**:
- Verify `.env` file exists and contains `ANECDOTES_API_KEY`
- Check for typos in variable name
- Ensure no extra spaces or quotes
- Check the `API KEY` Expiration date 

#### 2. Connection Timeouts

**Symptom**: `requests.exceptions.Timeout`

**Solution**:
- Check network connectivity to SoluDev/Anecdotes
- Increase `TIMEOUT_SECONDS` in `config.json` if needed

#### 3. Invalid JSON Response

**Symptom**: `json.JSONDecodeError` in logs

**Solution**:
- Check API endpoint URLs in `config.json`
- Verify API versions haven't changed
- Check SoluDev/Anecdotes API status

#### 4. Permission Errors

**Symptom**: `IOError` or `PermissionError` when writing files

**Solution**:
- Check write permissions for `out/` and `logs/` directories
- Verify disk space availability
- Run with appropriate user permissions

#### 5. Backup Not Clearing

**Symptom**: `backup.json` persists after successful run

**Solution**:
- Check logs for upload errors
- Verify Anecdotes API is accessible
- Manually delete `backup.json` if upload succeeded but cleanup failed


## Development

### Adding New Features

1. **New API Endpoint**: Add method to appropriate client class
2. **New Data Model**: Add Pydantic model to `common/models.py`
3. **New Configuration**: Add to `config.json` and access via `config` object

### Code Style

- Follow PEP 8 guidelines
- Use descriptive variable names
- Add type hints to all functions
- Document complex logic with comments

## Contributing

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-new-feature`)
3. Commit your changes (`git commit -m 'Add new feature requirements'`)
4. Push to the branch (`git push origin feature/your-new-feature`)
5. Open a Pull Request


**Last Updated**: November 2025
