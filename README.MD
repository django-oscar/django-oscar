# AI PR Review Bot – POC

This repository demonstrates an **AI-powered Pull Request review bot** using [pr-agent](https://github.com/qodo-ai/pr-agent).  
When a pull request is opened or updated, the bot automatically reviews the changes and posts comments using an AI model.

## 📌 Overview

- **Trigger:** Every time a PR is opened, synchronized, or reopened.
- **Technology:**
  - GitHub Actions (CI/CD)
  - [pr-agent](https://github.com/qodo-ai/pr-agent) for AI-based PR review
  - OpenAI for LLM processing
- **Goal:** Automate code review to save developer time and maintain quality.

---

## 🚀 Setup Steps

# Features
- Automatic PR reviews on every pull request
- Self-hosted or GitHub-hosted runners supported
- Minimal setup required
- Uses your OpenAI API key 

### 1. Clone the repo
```bash
git clone https://github.com/django-oscar/django-oscar
```

### 2. Create our branch 
```bash
git checkout -b abhay_task
```
### 3. Copy pr-agent folder
## Clone pr-agent and copy the pr-agent directory into your repo root:
```bash
git clone https://github.com/qodo-ai/pr-agent.git
cp -r pr-agent /path/to/your/repo/
```

### 4. Add GitHub Actions Workflow
## Create .github/workflows/ai-pr-review.yml
```bash
name: AI PR Review AI PR Review bot_abh
 
on:
 
  pull_request:
 
    types: [opened, synchronize, reopened]
 
jobs:
 
  review:
 
    runs-on: ubuntu-latest 
 
    steps:
 
      - name: Checkout PR branch
 
        uses: actions/checkout@v4
        with:
          submodules: true
 
      - name: Install PR Bot
 
        working-directory: ./pr-agent
 
        shell: bash
 
        run: |
 
          pip install -e .
 
      - name: Run PR Review
 
        env:
 
          GITHUB__USER_TOKEN: ${{ secrets.AI_PR_REVIEW_BOT }}
 
          OPENAI__KEY: ${{ secrets.OPENAI_API_KEY }}
 
        working-directory: ./pr-agent
 
        shell: bash
 
        run: |
 
          python -c "from pr_agent.cli import run_command; run_command('${{ github.event.pull_request.html_url }}', 'review')"
``` 