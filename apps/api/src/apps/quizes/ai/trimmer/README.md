# Trimmer Module

The Trimmer module uses GPT-5-nano to analyze a table of contents (JSON format) and a user query to determine which page ranges should be included in the content.

## Structure

- `agent.py` - Defines the Pydantic AI agent using GPT-5-nano model
- `trim.py` - Main function to orchestrate the trimming process
- `prompts.py` - Placeholder for future prompt templates
- `__init__.py` - Exports the main `trim_content` function

## Usage

```python
from apps.quizes.ai.trimmer import trim_content

# Example table of contents (JSON string)
contents = '''
{
  "chapters": [
    {
      "title": "Introduction to Linear Algebra",
      "pages": "1-50"
    },
    {
      "title": "Vector Spaces",
      "pages": "51-100"
    },
    {
      "title": "Matrix Operations",
      "pages": "101-150"
    },
    {
      "title": "Eigenvalues and Eigenvectors",
      "pages": "151-200"
    }
  ]
}
'''

# User query
query = "I need information about matrix operations and eigenvalues"

# Get page ranges
page_ranges = await trim_content(
    contents=contents,
    query=query,
    user_id="user123",  # optional
    session_id="session456"  # optional
)

# Result example:
# [
#   {'start': 101, 'end': 150},  # Matrix Operations
#   {'start': 151, 'end': 200}   # Eigenvalues and Eigenvectors
# ]
```

## Output Format

The function returns a list of dictionaries with `start` and `end` keys representing page ranges:

```python
[
    {"start": 100, "end": 120},
    {"start": 140, "end": 170}
]
```

## Model

Uses `LLMS.GPT_5_NANO` (openai:gpt-5-nano) for efficient and cost-effective content trimming.

## Dependencies

The agent depends on:

- `TrimmerDeps` dataclass with `contents` and `query` fields
- `TrimmerOutput` model with `page_ranges` and `reasoning` fields
- Langfuse for observability and prompt management

## Langfuse Prompt

The agent expects a prompt template named `trimmer/base` in Langfuse. This prompt should instruct the model on how to analyze the table of contents and user query to determine relevant page ranges.
