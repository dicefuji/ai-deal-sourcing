import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import anthropic
import os
import json
from tabulate import tabulate
import logging
import re
import textwrap
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def wrap_text(text, width=20):
    return "\n".join(textwrap.wrap(text, width=width))

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta

def search_arxiv(query, max_results=10, start_days=1, end_days=3):
    base_url = 'http://export.arxiv.org/api/query?'
    
    # Calculate the date range
    now = datetime.now()
    end_date = now - timedelta(days=start_days)
    start_date = now - timedelta(days=end_days)
    
    # Adjust dates to skip weekends
    while end_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        end_date -= timedelta(days=1)
    while start_date.weekday() >= 5:
        start_date -= timedelta(days=1)
    
    # Format dates for the query
    date_query = f'submittedDate:[{start_date.strftime("%Y%m%d")}000000 TO {end_date.strftime("%Y%m%d")}235959]'
    
    # Construct the full query
    search_query = f'search_query=all:{query}+AND+{date_query}&sortBy=submittedDate&sortOrder=descending&start=0&max_results={max_results}'
    
    response = requests.get(base_url + search_query)
    root = ET.fromstring(response.content)
    
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text
        link = entry.find('{http://www.w3.org/2005/Atom}id').text
        authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')]
        papers.append({'title': title, 'abstract': abstract, 'link': link, 'authors': authors})
    
    return papers



def analyze_with_claude(paper, client):
    prompt = f"""
Analyze the following AI research paper from arXiv for venture capitalists seeking investment opportunities. Provide your analysis in simple Japanese explaining technical language, strictly adhering to this structure:

1. 要約 (150字以内):
[論文の主要な洞察を強調した概要を記入]

2. 詳細分析 (150字以内):
[最も洞察に富む発見についてのコメントを記入]

3. 評価:
評価は1-49の段階で、つけてください

大規模採用の可能性の基準:
0-10点: 研究段階のアイデアで、実用化までに10年以上かかる可能性が高い。11-20点: 限定的な用途で採用される可能性があるが、広範な採用には課題が多い、実用化までに5年以上かかる可能性が高い。21-30点: 特定の業界や分野で広く採用される可能性が高く、3年以内に実用化の見込みがある。31-44点: 特定の業界や分野で広く採用される可能性が高く、1年以内に実用化の見込みがある。45-49点: ChatGPTのように、発表後すぐに世界中で広く採用され、1日で1億人規模のユーザーを獲得する可能性がある革新的な技術。

技術的進歩の基準:
0-10点: 既存技術の改良や最適化をしていない。11-20点: 既存技術の小規模な改良や最適化。21-30点: 既存のアプローチに対するな改善、または新しいアイデアの提案。31-44点: 既存の課題に対する画期的な解決策、または新しい研究分野を開拓する可能性がある。45-49点: GPT-5レベルの革新的な技術進歩。AIの能力を劇的に向上させ、新たなパラダイムシフトを引き起こす可能性がある。

- 大規模採用の可能性: [1-49の数字] 
理由: [150字以内で説明]
- 技術的進歩: [1-49の数字]
理由: [150字以内で説明]

4. 潜在的な産業と用途:
- 産業1: [産業名]
用途と理由: [50字以内で説明]
- 産業2: [産業名]
用途と理由: [50字以内で説明]
- 産業3: [産業名]
用途と理由: [50字以内で説明]

5. 産業の歴史と将来:
- 産業1: [産業名]
[150字以内で初期の歴史、進化、この研究成果の位置づけを説明]
- 産業2: [産業名]
[150字以内で初期の歴史、進化、この研究成果の位置づけを説明]
- 産業3: [産業名]
[150字以内で初期の歴史、進化、この研究成果の位置づけを説明]

6. 著者：{', '.join(paper['authors'])}

各セクションの文字制限を厳守し、指定された構造に従って回答してください。

論文:
タイトル: {paper['title']}
要約: {paper['abstract']}
著者: {', '.join(paper['authors'])}
    """

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text if isinstance(response.content, list) else response.content
        
        logger.info(f"Raw response for paper '{paper['title']}':\n{content[:500]}...")  # Log first 500 characters
        
        # Extract structured data using regex
        structured_data = {}
        sections = ['要約', '詳細分析', '評価', '潜在的な産業と用途', '産業の歴史と将来', 'arXiv論文リンク']
        for i, section in enumerate(sections):
            pattern = f"{i+1}\. {section}(.*?)(?={i+2}\. |$)"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                structured_data[section] = match.group(1).strip()
        
        # Extract scores
        adoption_score = re.search(r'大規模採用の可能性:\s*(\d+)', structured_data.get('評価', ''))
        tech_score = re.search(r'技術的進歩:\s*(\d+)', structured_data.get('評価', ''))
        
        if adoption_score and tech_score:
            adoption_score = int(adoption_score.group(1))
            tech_score = int(tech_score.group(1))
            impact_score = (adoption_score + tech_score) / 2
        else:
            logger.error(f"Could not extract scores for paper '{paper['title']}'")
            return None
        
        return {
            'analysis': content,
            'structured_data': structured_data,
            'impact_score': impact_score
        }
    except Exception as e:
        logger.error(f"Error analyzing paper '{paper['title']}': {str(e)}")
        return None

def select_most_impactful_paper(analyzed_papers):
    return max(analyzed_papers, key=lambda x: x['impact_score'])

def extract_score_and_reason(text, category):
    pattern = rf'{category}:\s*(\d+).*?理由:\s*(.+?)(?=(?:大規模採用の可能性|技術的進歩):|$)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1), match.group(2).strip()
    return "N/A", "Reason not found"

def main():
    """Main entry point for the script."""
    # Use environment variable for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("Please set the ANTHROPIC_API_KEY environment variable")

    client = anthropic.Anthropic(api_key=api_key)

    # ArXiv query parameters - can be customized
    arxiv_query = "Consumer AI"
    papers = search_arxiv(arxiv_query, max_results=5, start_days=1, end_days=100) 

    analyzed_papers = []
    for paper in papers:
        analysis = analyze_with_claude(paper, client)
        if analysis:
            analyzed_papers.append({**paper, **analysis})
        else:
            logger.error(f"Failed to analyze paper: {paper['title']}")

    if analyzed_papers:
        most_impactful_paper = select_most_impactful_paper(analyzed_papers)

        print("\nMost Impactful Paper:")
        print(f"Title: {most_impactful_paper['title']}")
        print(f"Impact Score: {most_impactful_paper['impact_score']:.2f}")
        print("\nAnalysis:")
        for key, value in most_impactful_paper['structured_data'].items():
            print(f"\n{key}:")
            print(value)
        print(f"\narXiv Link: {most_impactful_paper['link']}")
        print(f"\nAuthors: {', '.join(most_impactful_paper['authors'])}")

        # Add table summary
        print("\nSummary of All Papers:")
        table_data = []
        for paper in analyzed_papers:
            impact_score = paper['impact_score']
            evaluation = paper['structured_data'].get('評価', '')
            
            adoption_score, adoption_reason = extract_score_and_reason(evaluation, '大規模採用の可能性')
            tech_score, tech_reason = extract_score_and_reason(evaluation, '技術的進歩')
            
            if adoption_score == "N/A" or tech_score == "N/A":
                logger.warning(f"Could not extract all scores for paper: {paper['title']}")
                logger.debug(f"Evaluation text: {evaluation}")

            is_most_impactful = "✓" if paper == most_impactful_paper else ""
            
            table_data.append([
                is_most_impactful,
                wrap_text(paper['title'], width=30),
                f"Score: {adoption_score}\n{wrap_text('Reason: ' + adoption_reason, width=30)}",
                f"Score: {tech_score}\n{wrap_text('Reason: ' + tech_reason, width=30)}"
            ])
        
        headers = ["T", "Title", "Adoption Score & Reason", "Tech Score & Reason"]
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
    else:
        print("No papers were successfully analyzed.")

if __name__ == "__main__":
    main()
    
    