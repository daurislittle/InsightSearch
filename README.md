# InsightSearch

A lightweight serverless semantic search API built with AWS Lambda,
DynamoDB, and OpenAI embeddings. Send a text query, get back ranked,
semantically relevant results — even when exact words do not match.

---

## How It Works

```
1. You send a POST request:  { "query": "how do I reset my password?" }
2. Lambda converts your query into an embedding via OpenAI
3. Lambda fetches all stored document embeddings from DynamoDB
4. Lambda scores each document using cosine similarity
5. Lambda returns the top ranked matches as JSON
```

---

## Project Structure

```
InsightSearch/
│
├── backend/
│   ├── lambda_function.py     ← Lambda entry point
│   ├── requirements.txt       ← Python dependencies
│   └── utils/
│       ├── __init__.py
│       ├── embeddings.py      ← OpenAI embedding calls
│       ├── ranking.py         ← Cosine similarity + ranking
│       └── dynamo.py          ← DynamoDB read/write helpers
│
├── data/
│   ├── docs_example.json      ← Sample documents dataset
│   └── embed_indexer.py       ← One-time script to embed and upload docs
│
├── infra/
│   └── setup_notes.md         ← Manual AWS setup notes
│
├── template.yaml              ← AWS SAM infrastructure definition
└── README.md
```

---

## Prerequisites

Before you start make sure you have the following:

- **AWS SAM CLI** installed and configured
- **Python 3.12**
- **An OpenAI API key**
- **AWS credentials** configured locally

```bash
# Verify your tools
sam --version
aws --version
python3 --version
```

---

## Step 1 — Store Your OpenAI API Key

Store your OpenAI API key in AWS Secrets Manager. This keeps it
encrypted and out of your source code.

```bash
aws secretsmanager create-secret \
  --name "insight-search/openai-key" \
  --secret-string '{"OPENAI_API_KEY":"sk-your-key-here"}' \
  --region us-east-1
```

> You only need to run this once. If the secret already exists use
> `update-secret` instead of `create-secret`.

```bash
# If you need to update an existing secret
aws secretsmanager update-secret \
  --secret-id "insight-search/openai-key" \
  --secret-string '{"OPENAI_API_KEY":"sk-your-new-key-here"}' \
  --region us-east-1
```

---

## Step 2 — Create the SAM Template

Create a `template.yaml` file in the root of the project with the
following contents:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: InsightSearch — Serverless semantic search API

Globals:
  Function:
    Runtime: python3.12
    CodeUri: backend/
    Handler: lambda_function.lambda_handler
    MemorySize: 256
    Timeout: 30
    Environment:
      Variables:
        DYNAMODB_TABLE_NAME: searchable-documents
        SECRET_NAME: semantic-search/openai-key
        REGION: us-east-1

Resources:

  InsightSearchFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: insight-search-handler
      Description: Semantic search using OpenAI embeddings and DynamoDB
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref InsightSearchTable
        - AWSSecretsManagerGetSecretValuePolicy:
            SecretArn: !Sub >
              arn:aws:secretsmanager:us-east-1:${AWS::AccountId}:secret:insight-search/openai-key-*
      Events:
        SearchEndpoint:
          Type: Api
          Properties:
            RestApiId: !Ref InsightSearchApi
            Path: /search
            Method: POST
        HealthCheck:
          Type: Api
          Properties:
            RestApiId: !Ref InsightSearchApi
            Path: /health
            Method: GET

  InsightSearchApi:
    Type: AWS::Serverless::Api
    Properties:
      Name: insight-search-api
      StageName: prod
      Cors:
        AllowMethods: "'POST, GET, OPTIONS'"
        AllowHeaders: "'Content-Type'"
        AllowOrigin: "'*'"

  InsightSearchTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: searchable-documents
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST

Outputs:
  SearchApiUrl:
    Description: "POST your queries to this endpoint"
    Value: !Sub >
      https://${InsightSearchApi}.execute-api.us-east-1.amazonaws.com/prod/search

  HealthCheckUrl:
    Description: "GET this URL to verify the API is live"
    Value: !Sub >
      https://${InsightSearchApi}.execute-api.us-east-1.amazonaws.com/prod/health

  DynamoDBTableName:
    Description: "DynamoDB table name — needed for embed_indexer.py"
    Value: !Ref InsightSearchTable
```

---

## Step 3 — Build and Deploy

```bash
# Build the project
# SAM installs dependencies and packages your Lambda code
sam build
```

```bash
# Deploy for the first time
# The --guided flag walks you through setup and saves your answers
sam deploy --guided
```

When prompted answer as follows:

```
Stack Name:         insight-search
AWS Region:         us-east-1
Confirm changes:    y
Allow SAM to create IAM roles: y
Disable rollback:   n
Save to samconfig.toml: y
```

After deployment completes SAM prints your live endpoint:

```
Outputs
───────────────────────────────────────────────────────
Key    SearchApiUrl
Value  https://abc123.execute-api.us-east-1.amazonaws.com/prod/search

Key    HealthCheckUrl
Value  https://abc123.execute-api.us-east-1.amazonaws.com/prod/health
───────────────────────────────────────────────────────
```

Copy the `SearchApiUrl` — you will need it in the steps below.

> For all subsequent deploys after the first you can simply run:
> ```bash
> sam build && sam deploy
> ```

---

## Step 4 — Index Your Documents

Before searching you need to embed your documents and store them
in DynamoDB. Run this once locally.

```bash
# Set your OpenAI key as a local environment variable
export OPENAI_API_KEY="sk-your-key-here"

# Run the indexer from the project root
python data/embed_indexer.py
```

Expected output:

```
[INFO] Loaded 10 documents from data/docs_example.json

[1/10] Processing: 'How to reset your password...'
  ✓ Stored document '1'

[2/10] Processing: 'Troubleshooting login issues...'
  ✓ Stored document '2'

...

==================================================
Indexing complete!
  ✓ Success: 10 documents
  ✗ Failed:  0 documents
==================================================
```

> Only run this script once unless you change your dataset.
> Re-running it overwrites existing documents with the same id.

---

## Step 5 — Test the API

### Health Check

```bash
curl https://YOUR_API_URL/prod/health
```

Expected response:

```json
{ "message": "OK" }
```

### Search Request

```bash
curl -X POST https://YOUR_API_URL/prod/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how do I reset my password?"}'
```

Expected response:

```json
{
  "query": "how do I reset my password?",
  "total_docs_searched": 10,
  "results_returned": 3,
  "results": [
    {
      "id": "1",
      "text": "How to reset your password using the account settings page"
    },
    {
      "id": "6",
      "text": "Setting up two-factor authentication for better security"
    },
    {
      "id": "2",
      "text": "Troubleshooting login issues and authentication errors"
    }
  ]
}
```

### Controlling Result Count

```bash
# Return only the top 3 results
curl -X POST "https://YOUR_API_URL/prod/search?top_k=3" \
  -H "Content-Type: application/json" \
  -d '{"query": "billing and invoices"}'
```

---

## Useful SAM Commands

```bash
# Build the project after any code change
sam build

# Deploy after build
sam deploy

# Test your Lambda locally without deploying
# Requires Docker to be running
sam local invoke InsightSearchFunction \
  --event events/search_event.json

# Start a local API Gateway for browser/Postman testing
sam local start-api

# Tail live Lambda logs in your terminal
sam logs -n insight-search-handler --tail

# Delete all AWS resources created by this stack
sam delete
```

---

## Viewing Logs

All Lambda output is automatically sent to CloudWatch Logs.

```bash
# Stream logs live in your terminal
sam logs -n insight-search-handler --tail
```

Or in the AWS Console:

```
CloudWatch → Log Groups → /aws/lambda/insight-search-handler
```

Look for these prefixes to filter logs quickly:

```
[INFO]  — normal operation
[WARN]  — something unexpected but non-fatal
[ERROR] — something failed
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| Empty results array | `min_score` too high | Lower threshold in `ranking.py` |
| All scores near 0.0 | Wrong embedding model | Check model name in `embeddings.py` |
| 500 Internal Server Error | Missing IAM permissions | Check Lambda execution role in console |
| 403 Forbidden | API not deployed | Run `sam deploy` again |
| `No documents found` | Indexer not run | Run `embed_indexer.py` |
| `KeyError: embedding` | Malformed DynamoDB item | Re-run `embed_indexer.py` |
| Slow first request | Lambda cold start | Expected — takes ~2s on first call |

---

## Teardown

To delete all AWS resources created by this project:

```bash
sam delete
```

You will be prompted to confirm. This removes the Lambda, API
Gateway, DynamoDB table, and IAM roles. It does not delete the
Secrets Manager secret — remove that separately if needed:

```bash
aws secretsmanager delete-secret \
  --secret-id "insight-search/openai-key" \
  --force-delete-without-recovery
```

## Adding Your Own Documents

To replace the sample dataset with your own documents edit
`data/docs_example.json` following this format:

```json
[
  { "id": "1", "text": "Your first document text goes here" },
  { "id": "2", "text": "Your second document text goes here" },
  { "id": "3", "text": "Your third document text goes here" }
]
```

Rules to follow:

```
- id must be a unique string for each document
- text should be a single coherent piece of content
- Keep each document under 8000 characters
- There is no minimum or maximum number of documents
```

After editing the file re-run the indexer:

```bash
export OPENAI_API_KEY="sk-your-key-here"
python data/embed_indexer.py
```

---

## Environment Variables Reference

These are set automatically by `template.yaml` and passed to
Lambda at runtime. You do not need to set these manually.

| Variable | Value | Description |
|---|---|---|
| `DYNAMODB_TABLE_NAME` | `searchable-documents` | DynamoDB table to read from |
| `SECRET_NAME` | `semantic-search/openai-key` | Secrets Manager secret path |
| `REGION` | `us-east-1` | AWS region for all clients |

> If you need to change any of these values update `template.yaml`
> and run `sam build && sam deploy`.

## How Semantic Search Differs From Keyword Search

| | Keyword Search | Semantic Search |
|---|---|---|
| Query: "I can't log in" | Finds: nothing | Finds: "Troubleshooting login issues" |
| Query: "charge on my bill" | Finds: nothing | Finds: "Understanding your monthly billing" |
| Query: "MFA setup" | Finds: nothing | Finds: "Setting up two-factor authentication" |
| Matches on | Exact words | Meaning and context |
| Handles typos | No | Partially |
| Understands synonyms | No | Yes |


## Quick Reference

```bash
# First time setup
aws secretsmanager create-secret \
  --name "insight-search/openai-key" \
  --secret-string '{"OPENAI_API_KEY":"sk-your-key-here"}' \
  --region us-east-1

sam build
sam deploy --guided
python data/embed_indexer.py

# Every deploy after that
sam build && sam deploy

# Test
curl -X POST https://YOUR_URL/prod/search \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query here"}'

# Watch logs live
sam logs -n insight-search-handler --tail

# Tear down everything
sam delete
```