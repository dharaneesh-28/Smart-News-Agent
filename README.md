## What It Does

This agent runs completely on its own. No buttons, no clicks. Every morning:

1. **Collects** 35+ articles from 7 RSS feeds + GitHub Trending
2. **Summarizes** using Amazon Bedrock (Nova Lite) AI model
3. **Stores** the report in Amazon S3
4. **Emails** a professional digest via Amazon SES

## Architecture
EventBridge (6 AM Daily Cron Trigger) | v AWS Lambda (Python 3.12 - Agent Orchestrator) | ├── RSS Feeds (7 sources) + GitHub API ──> Collect 35+ Articles | v Amazon Bedrock (Nova Lite Model) ──> AI Summarization | v Amazon S3 ──> Store Report (.txt) | v Amazon SES ──> Send Professional Email Digest


## AWS Services Used (6 Services)

| Service | Purpose |
|---------|---------|
| **AWS Lambda** | Serverless compute - executes agent code (Python 3.12, 512MB, 120s timeout) |
| **Amazon Bedrock (Nova Lite)** | AI/ML - intelligent news summarization |
| **Amazon S3** | Storage - stores generated reports |
| **Amazon SES** | Email - delivers daily HTML digest |
| **Amazon EventBridge** | Scheduler - cron trigger at 6 AM IST daily |
| **AWS IAM** | Security - manages roles and permissions |

## News Sources

| Source | Category |
|--------|----------|
| OpenAI Blog | AI News |
| Google AI News | AI News |
| AWS Official Blog | AWS News |
| AWS Machine Learning Blog | AWS News |
| The Hacker News | Cybersecurity |
| Schneier on Security | Cybersecurity |
| Hacker News | Tech |
| GitHub Trending | Open Source |

## How It Works

1. **Amazon EventBridge** fires a cron trigger at 6:00 AM IST daily (`cron(30 0 * * ? *)`)
2. **AWS Lambda** function starts execution
3. Lambda fetches news from **7 RSS feeds** using `feedparser`
4. **GitHub API** provides trending repositories
5. All 35+ articles are formatted and sent to **Amazon Bedrock**
6. Bedrock's **Nova Lite** model generates a structured AI summary with:
   - AI News Highlights
   - AWS News and Updates
   - Cyber Security Alerts
   - GitHub Trending Projects
   - Key Takeaways
   - Top 3 Things to Watch Today
7. Summary is uploaded to **Amazon S3** as a report
8. **Amazon SES** sends a professional HTML email with the full summary + download link

## Key Features

- Fully automated - zero manual intervention required
- 35+ articles collected per execution from diverse sources
- AI-powered summarization (not just aggregation)
- Professional HTML email with S3 download link
- Serverless architecture (pay only when running)
- Event-driven design
- Runs within AWS Free Tier

## Tech Stack

- **Runtime:** Python 3.12
- **Libraries:** feedparser, requests, boto3
- **AI Model:** Amazon Nova Lite (via Amazon Bedrock)
- **Infrastructure:** 100% Serverless (Lambda + EventBridge)
- **Storage:** Amazon S3
- **Notification:** Amazon SES

## Deployment

```bash
# Install dependencies
pip install feedparser requests fpdf2 -t package/

# Remove unnecessary packages (Lambda has boto3 built-in)
rm -rf package/boto3 package/botocore package/PIL

# Package deployment
cd package && zip -r ../deployment.zip . && cd ..
zip deployment.zip lambda_function.py

# Upload to S3 and update Lambda
aws s3 cp deployment.zip s3://ai-news-agent-dharaneesh/deployment.zip
aws lambda update-function-code --function-name NewsDigestAgent --s3-bucket ai-news-agent-dharaneesh --s3-key deployment.zip
Cost
Table



Service


Cost


Lambda	~120 seconds/execution - Free Tier eligible
Bedrock	Minimal per-invocation
S3	Negligible storage
SES	Free within sandbox
EventBridge	Free for scheduled rules
View more
Total estimated cost: < $1/month (mostly Free Tier)

Sample Email Output
The agent delivers a professional HTML email every morning with:

AI News Highlights
AWS News and Updates
Cyber Security Alerts
GitHub Trending Projects
Key Takeaways
Top 3 Things to Watch Today
Download link for full report stored in S3
Project Structure
Smart-News-Agent/
├── lambda_function.py      # Main agent code
├── requirements.txt        # Python dependencies
└── README.md              # This file
Author
Dharaneesh - Built for AWS Weekend Agent Challenge 2026

License
MIT
