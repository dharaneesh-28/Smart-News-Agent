
import json
import boto3
import feedparser
import requests
from datetime import datetime, timedelta
import os

S3_BUCKET = os.environ.get('S3_BUCKET', 'ai-news-agent-dharaneesh')
SES_SENDER = os.environ.get('SES_SENDER', 'dharaneesh8526@gmail.com')
SES_RECIPIENT = os.environ.get('SES_RECIPIENT', 'dharaneesh8526@gmail.com')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'amazon.nova-lite-v1:0')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)
s3 = boto3.client('s3', region_name=AWS_REGION)
ses = boto3.client('ses', region_name=AWS_REGION)


def fetch_rss_feed(url, category, max_items=5):
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', ''),
                'summary': entry.get('summary', '')[:200],
                'category': category
            })
        return items
    except Exception as e:
        print(f"Error fetching {category}: {str(e)}")
        return []


def fetch_github_trending():
    try:
        url = "https://api.github.com/search/repositories"
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        params = {
            'q': f'created:>{yesterday}',
            'sort': 'stars',
            'order': 'desc',
            'per_page': 5
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            repos = response.json().get('items', [])
            items = []
            for repo in repos[:5]:
                items.append({
                    'title': f"{repo['full_name']} - {repo['stargazers_count']} stars",
                    'link': repo['html_url'],
                    'summary': repo.get('description', 'No description')[:200],
                    'category': 'GitHub Trending'
                })
            return items
        return []
    except Exception as e:
        print(f"Error fetching GitHub Trending: {str(e)}")
        return []


def collect_all_news():
    feeds = [
        ("https://blog.openai.com/rss/", "AI News"),
        ("https://news.google.com/rss/search?q=artificial+intelligence&hl=en", "AI News"),
        ("https://aws.amazon.com/blogs/aws/feed/", "AWS News"),
        ("https://aws.amazon.com/blogs/machine-learning/feed/", "AWS News"),
        ("https://feeds.feedburner.com/TheHackersNews", "Cyber Security"),
        ("https://www.schneier.com/feed/atom/", "Cyber Security"),
        ("https://hnrss.org/frontpage?count=5", "Tech/Hacker News"),
    ]
    all_news = []
    for url, category in feeds:
        items = fetch_rss_feed(url, category)
        all_news.extend(items)
        print(f"Fetched {len(items)} items from {category}")
    github_items = fetch_github_trending()
    all_news.extend(github_items)
    print(f"Fetched {len(github_items)} items from GitHub Trending")
    return all_news


def format_news_for_prompt(news_items):
    categorized = {}
    for item in news_items:
        cat = item['category']
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(item)
    formatted = ""
    for category, items in categorized.items():
        formatted += f"\n--- {category} ---\n"
        for item in items:
            formatted += f"- {item['title']}\n  {item['summary']}\n\n"
    return formatted


def summarize_with_bedrock(news_text):
    prompt = f"""You are an AI Research Digest Agent. Summarize today's collected news into a professional daily digest.

Here is today's raw news data:

{news_text}

Please create a structured summary with these sections:

1. AI News Highlights
2. AWS News and Updates
3. Cyber Security Alerts
4. GitHub Trending Projects
5. Key Takeaways

Rules:
- Keep the entire summary under 500 words
- Use bullet points for clarity
- Highlight actionable insights
- Use only plain ASCII characters, no emojis or special symbols
- End with Top 3 Things to Watch Today"""

    try:
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 1500,
                "temperature": 0.3,
                "topP": 0.9
            }
        })
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=body,
            contentType='application/json',
            accept='application/json'
        )
        response_body = json.loads(response['body'].read())
        if 'output' in response_body:
            summary = response_body['output']['message']['content'][0]['text']
        elif 'content' in response_body:
            summary = response_body['content'][0]['text']
        else:
            summary = str(response_body)
        print("Bedrock summarization complete")
        return summary
    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        return f"Auto-Summary unavailable. Raw digest:\n\n{news_text[:2000]}"


def upload_to_s3(summary_text):
    today = datetime.now().strftime('%Y-%m-%d')
    file_key = f"reports/ResearchDigest_{today}.txt"
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=file_key, Body=summary_text.encode('utf-8'), ContentType='text/plain')
        presigned_url = s3.generate_presigned_url('get_object', Params={'Bucket': S3_BUCKET, 'Key': file_key}, ExpiresIn=604800)
        print(f"Report uploaded to s3://{S3_BUCKET}/{file_key}")
        return presigned_url
    except Exception as e:
        print(f"S3 upload error: {str(e)}")
        return None


def send_email(presigned_url, summary_text):
    today = datetime.now().strftime('%B %d, %Y')
    clean_summary = summary_text[:1500].encode('ascii', 'ignore').decode('ascii')
    html_body = f"""<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
<div style="background:linear-gradient(135deg,#1a237e,#283593);padding:25px;border-radius:10px 10px 0 0;">
<h1 style="color:white;margin:0;font-size:22px;">Morning AI Research Digest</h1>
<p style="color:#bbdefb;margin:5px 0 0 0;font-size:14px;">{today}</p></div>
<div style="padding:25px;background:#fafafa;border-radius:0 0 10px 10px;">
<p style="font-size:15px;">Good Morning! Your daily AI Research Digest is ready.</p>
<div style="background:white;padding:20px;border-radius:8px;border-left:4px solid #1a237e;margin:15px 0;">
<pre style="white-space:pre-wrap;font-size:12px;font-family:Consolas,monospace;line-height:1.6;color:#333;">{clean_summary}</pre></div>
<div style="text-align:center;margin:25px 0;">
<a href="{presigned_url}" style="background:#1a237e;color:white;padding:14px 35px;text-decoration:none;border-radius:6px;font-weight:bold;font-size:14px;">Download Full Report</a></div>
<hr style="border:1px solid #e0e0e0;margin:20px 0;">
<p style="color:#999;font-size:11px;text-align:center;">AI News Research Digest Agent | Amazon Bedrock | AWS Lambda | EventBridge | S3 | SES</p>
</div></body></html>"""
    try:
        response = ses.send_email(
            Source=SES_SENDER,
            Destination={'ToAddresses': [SES_RECIPIENT]},
            Message={
                'Subject': {'Data': f'Morning AI Research Digest - {today}', 'Charset': 'UTF-8'},
                'Body': {'Html': {'Data': html_body, 'Charset': 'UTF-8'}}
            }
        )
        print(f"Email sent! MessageId: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"SES error: {str(e)}")
        return False


def lambda_handler(event, context):
    print("AI News Research Digest Agent - Starting...")
    print(f"Execution time: {datetime.now().isoformat()}")
    try:
        print("Step 1: Collecting news from RSS feeds and GitHub...")
        news_items = collect_all_news()
        print(f"Total items collected: {len(news_items)}")
        if not news_items:
            return {'statusCode': 200, 'body': json.dumps('No news items found today.')}

        print("Step 2: Summarizing with Amazon Bedrock AI...")
        news_text = format_news_for_prompt(news_items)
        summary = summarize_with_bedrock(news_text)

        print("Step 3: Uploading report to S3...")
        presigned_url = upload_to_s3(summary)

        print("Step 4: Sending email via SES...")
        email_sent = False
        if presigned_url:
            email_sent = send_email(presigned_url, summary)

        print("COMPLETE!")
        print(f"News: {len(news_items)} | Report: Uploaded | Email: {'Sent' if email_sent else 'Failed'}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'AI Research Digest generated successfully!',
                'news_count': len(news_items),
                'email_sent': email_sent,
                'services_used': ['Bedrock', 'S3', 'SES', 'Lambda', 'EventBridge']
            })
        }
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps(f'Error: {str(e)}')}

