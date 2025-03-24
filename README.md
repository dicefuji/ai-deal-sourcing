# AI Deal Sourcing

This project uses arXiv and Claude AI to automatically identify and analyze high-impact AI research papers for venture capital investment opportunities.

## Features

- Searches arXiv for recent AI research papers
- Uses Claude AI to analyze papers in Japanese for:
  - Summary and detailed analysis
  - Adoption potential score (1-49)
  - Technical advancement score (1-49)
  - Potential industries and use cases
  - Historical context for each industry
- Ranks papers by impact score (average of adoption and technical scores)
- Generates a formatted summary table of all analyzed papers

## Requirements

- Python 3.8+
- Anthropic API key

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ai-deal-sourcing.git
cd ai-deal-sourcing
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Usage

Run the script with:
```bash
python src/ai-deal-sourcing.py
```

You can modify the following parameters in the script:
- `arxiv_query`: The search term for arXiv (default: "Consumer AI")
- `max_results`: Number of papers to analyze (default: 5)
- `start_days`/`end_days`: Date range for the search

## Output

The script outputs:
1. Detailed analysis of the most impactful paper
2. A summary table of all analyzed papers with their scores

## Customization

You can modify the Claude prompt in the `analyze_with_claude` function to change:
- The language of analysis
- The criteria for scoring
- The specific information extracted from papers

## License

[MIT License](LICENSE) 