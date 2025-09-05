# Amazon Comprehend Demo
Simple application to showcase comprehend.

## Specificiation
- UI: Clean and simple desktop app
- Purpose: Take in a block of text.  Send to Amazon Comprehend.  Display curated results to user in human-readable format.
- Language: Python FastAPI
- Technical details:
  - Comprehend Features: Sentiment, Entity Recognition, Key Phrases, Syntax, Language Detection, PII Detection, Categories, Targeted Sentiment
  - Use AWS_PROFILE for sdk access to aws resources (no other IAM roles needed)
  - 2000 character max input
  - no copy/export needed
  - no accessibility or mobile considerations
  - no batch support needed
  - no need to mask/redact PII
  - local deployment only
  - no audit logging needed
  - this is for demo purposes, keep it very simple
  - no tests needed
  - keep logging minimal
  - no content filtering needed

## Agent Steps
1. Create simple and clean user interface
2. Create back-end to call Amazon Comprehend.