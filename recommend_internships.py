"""Recommend internships from a transformed internships JSON file.

This module provides generate_recommendations(internships, user_skills, top_k)
and a small CLI to produce `recommendations.json` from an `outputmech.json` file.
"""

from typing import List, Dict, Optional
import json
import argparse
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from job_search import fetch_jobs


def fetch_and_recommend_jobs(title: str, skills: List[str], degree: Optional[str] = None, location: str = "India", user_skills: Optional[List[str]] = None, top_k: int = 20, model_name: str = 'all-MiniLM-L6-v2') -> pd.DataFrame:
    """
    Fetch job listings and generate recommendations in one step.
    
    Args:
        title: Job title to search for
        skills: List of skills to include in search
        degree: Optional degree to include in search
        location: Location to search in
        user_skills: User's skills for recommendation matching
        top_k: Number of top recommendations to return
        model_name: Sentence transformer model name
        
    Returns:
        pandas DataFrame of ranked recommendations
    """
    # Fetch jobs directly using the new function
    internships = fetch_jobs(title, skills, degree, location)
    
    # Generate recommendations from the fetched jobs
    return generate_recommendations(internships, user_skills, top_k, model_name)


def generate_recommendations(internships: List[Dict], user_skills: Optional[List[str]] = None, top_k: int = 20, model_name: str = 'all-MiniLM-L6-v2') -> pd.DataFrame:
    """Generate recommendations and write `recommendations.json`.

    Returns a pandas DataFrame of ranked recommendations.
    """
    if user_skills is None:
        user_skills = ["CAD", "SolidWorks", "3D Printing", "FEA", "Problem Solving"]

    # Load embedding model
    model = SentenceTransformer(model_name)

    # Build embeddings for internships
    keys = []
    embeds = []
    metas = []
    for intern in internships:
        desc = intern.get('description', '') or ''
        emb = model.encode([desc])[0]
        title = intern.get('job_title', '')
        company = intern.get('company', '')
        location = intern.get('location', '')
        keys.append(f"{title}||{company}||{location}")
        embeds.append(emb)
        metas.append({'title': title, 'company': company, 'location': location, 'description': desc})

    # User embedding
    user_text = ' '.join(user_skills)
    user_emb = model.encode([user_text])[0]

    # Compute similarities
    results = []
    for meta, emb in zip(metas, embeds):
        sim = float(cosine_similarity([user_emb], [emb])[0][0])
        results.append({'job_title': meta['title'], 'company': meta['company'], 'location': meta['location'], 'similarity': sim, 'description': meta['description']})

    # Rank
    results = sorted(results, key=lambda r: r['similarity'], reverse=True)

    # Build DataFrame
    df = pd.DataFrame(results)
    df = df.rename(columns={'job_title': 'Job Title', 'company': 'Company', 'location': 'Location', 'similarity': 'Similarity Score'})

    # Write top_k to recommendations.json
    out_records = df.head(top_k).to_dict(orient='records')
    with open('recommendations.json', 'w', encoding='utf-8') as f:
        json.dump({'recommendations': out_records, 'total_found': len(df)}, f, indent=2, ensure_ascii=False)

    return df


def main():
    parser = argparse.ArgumentParser(description='Generate internship recommendations from transformed internships JSON')
    parser.add_argument('--input', '-i', default='outputmech.json', help='Input transformed internships JSON file')
    parser.add_argument('--skills', '-s', help='Comma-separated list of user skills')
    parser.add_argument('--top', '-k', type=int, default=20, help='Number of top recommendations to write')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    internships = data.get('internships', [])
    user_skills = args.skills.split(',') if args.skills else None

    df = generate_recommendations(internships, user_skills=user_skills, top_k=args.top)
    print('\nTop Internship Recommendations:\n')
    print(df.head(args.top))


if __name__ == '__main__':
    main()