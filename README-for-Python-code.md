# HSA Exam Slot Checker

A Python tool to check and monitor available slots for HSA (Health Sciences Authority) exams.

## Features

- Check for available exam slots across multiple locations
- Monitor slots continuously with customizable intervals
- Email notifications when slots become available
- Sound alerts when slots are found
- Support for checking specific batches or all available batches
- Detailed logging and reporting

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - requests
  - boto3 (optional, for email notifications)

## Installation

1. Clone this repository or download the script
2. Install required dependencies:

```bash
pip install requests
pip install boto3  # Optional, for email notifications
```

## Usage

### Basic Usage

```bash
python hsa_checker.py -p PHONE_NUMBER -w PASSWORD
```

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `-b`, `--batch-code` | Check specific batch by code (e.g. 502, 503) |
| `-l`, `--location-id` | Only check a specific location ID |
| `-i`, `--interval` | Interval in seconds between checks when monitoring (default: 300) |
| `-d`, `--delay` | Delay in seconds between API calls (default: 2) |
| `-e`, `--email` | Email to send notifications to |
| `-n`, `--no-email` | No email notifications, just display results |
| `-v`, `--verbose` | Verbose output (show progress for each location) |
| `-m`, `--monitor` | Monitor mode - continuously check at specified intervals |
| `-p`, `--phone` | Phone number for authentication |
| `-w`, `--password` | Password for authentication |
| `-t`, `--token` | Custom authorization token |
| `-a`, `--show-batches` | Show all available batches and exit |
| `--all-batches` | Check all OPENING batches instead of just one |
| `--status` | Status of batches to check (default: OPENING) |

### Examples

Check all available OPENING batches:
```bash
python hsa_checker.py -p PHONE -w PASSWORD --all-batches
```

Monitor a specific batch code every 5 minutes:
```bash
python hsa_checker.py -p PHONE -w PASSWORD -b 502 -m -i 300
```

Show all available batches:
```bash
python hsa_checker.py -p PHONE -w PASSWORD -a
```

Check a specific location in a batch:
```bash
python hsa_checker.py -p PHONE -w PASSWORD -b 502 -l 1234
```

## Email Notifications

The script can send email notifications using Amazon SES. To use this feature:
1. Install boto3: `pip install boto3`
2. Configure AWS credentials with SES access
3. Update the `from_email` variable with a validated SES email address
4. Specify the recipient email with the `-e` flag

## Output

The script outputs detailed information to both the console and a timestamped results file. Each run generates a file named `results-YYYYMMDD-HHMMSS.tmp` with all checking results.

## Monitoring

Run the script with `-m` flag to enable continuous monitoring. The script will run checks at regular intervals (default: 300 seconds) until stopped with Ctrl+C.

```bash
python hsa_checker.py -p PHONE -w PASSWORD -m
```

## License

This project is open-source and available for personal use.
