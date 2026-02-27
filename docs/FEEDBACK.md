# Feedback System Guide

## What It Does

Zenus occasionally asks for your feedback after executing commands:

```
✓ Plan executed successfully

Was this helpful? (y/n/skip):
```

This helps improve Zenus over time by learning what works and what doesn't.

## Frequency

**Default:** 10% of commands (not annoying!)

- Won't ask about the same command twice in a session
- Won't ask if you've already given feedback for that command
- Random sampling to avoid being intrusive

## How to Disable

If you don't want feedback prompts at all:

### Option 1: Environment Variable (Permanent)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export ZENUS_FEEDBACK_PROMPTS=off
```

Then reload:
```bash
source ~/.bashrc
```

### Option 2: One-Time Disable

```bash
ZENUS_FEEDBACK_PROMPTS=off zenus "your command"
```

### Option 3: Session-Only Disable

```bash
export ZENUS_FEEDBACK_PROMPTS=off
zenus
# Feedback disabled for this terminal session
```

## Valid Disable Values

Any of these will disable feedback:
- `false`
- `0`
- `no`
- `off`

## Why Give Feedback?

Your feedback helps:
- **Identify problem tools** - Which tools fail most often?
- **Improve prompts** - What commands are misunderstood?
- **Train better models** - Export data for fine-tuning
- **Prioritize improvements** - What to fix first?

## Privacy

All feedback is:
- **Stored locally** (`~/.zenus/feedback.jsonl`)
- **Never sent anywhere** automatically
- **Privacy-filtered** when exported (removes passwords, emails, tokens)
- **Your data** - delete the file anytime

## Feedback Data

View your feedback:
```bash
cat ~/.zenus/feedback.jsonl | jq
```

Delete all feedback:
```bash
rm ~/.zenus/feedback.jsonl
```

## Frequency Customization

To change feedback frequency (for developers):

Edit in code or create custom FeedbackCollector:
```python
from zenus_core.feedback import FeedbackCollector

# 50% of commands
collector = FeedbackCollector(prompt_frequency=0.5)

# 1% of commands (very rare)
collector = FeedbackCollector(prompt_frequency=0.01)

# Never (same as disabling)
collector = FeedbackCollector(enable_prompts=False)
```

---

**Default is 10% - a good balance between learning and not being annoying!**
