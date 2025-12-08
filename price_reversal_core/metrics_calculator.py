import textstat
from typing import List, Dict
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def _download_nltk_data():
    """Downloads necessary NLTK data if not already present."""
    try:
        nltk.data.find('corpora/stopwords')
    except Exception: # Use generic Exception to avoid issues with specific NLTK DownloadError path
        nltk.download('stopwords')
    try:
        nltk.data.find('tokenizers/punkt')
    except Exception: # Use generic Exception to avoid issues with specific NLTK DownloadError path
        nltk.download('punkt')

# Call the function once when the module is loaded
_download_nltk_data()

stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def preprocess_text(text: str) -> str:
    """
    Cleans and preprocesses text for TF-IDF vectorization.
    """
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text) # Remove punctuation and numbers
    tokens = nltk.word_tokenize(text)
    tokens = [stemmer.stem(word) for word in tokens if word not in stop_words and len(word) > 1]
    return " ".join(tokens)

def calculate_text_metrics(summary_text: str, companies_data: List[Dict]) -> Dict:
    """
    Calculates reading level, word count, and a more sophisticated relevance score using cosine similarity.
    """
    metrics = {}

    # 1. Word Count
    words = summary_text.split()
    metrics['word_count'] = len(words)

    # 2. Reading Level (Flesch-Kincaid Grade Level)
    metrics['flesch_kincaid_grade'] = textstat.flesch_kincaid_grade(summary_text)

    # 3. Relevance Ranking (Cosine Similarity)
    # Generate query string from company data
    query_terms = []
    for company in companies_data:
        if 'SearchQuery' in company and company['SearchQuery']:
            query_terms.append(company['SearchQuery'])
        if 'Company Name' in company and company['Company Name']:
            query_terms.append(company['Company Name'])
        if 'Symbol' in company and company['Symbol']:
            query_terms.append(company['Symbol'])
    
    query_string = " ".join(query_terms)
    
    # Preprocess document and query
    processed_summary = preprocess_text(summary_text)
    processed_query = preprocess_text(query_string)

    if not processed_summary or not processed_query:
        metrics['cosine_relevance'] = 0.0
        metrics['relevance_keywords_found'] = 0 # No relevant keywords if text is empty
        return metrics

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer()
    # Fit and transform on both summary and query to ensure consistent vocabulary
    tfidf_matrix = vectorizer.fit_transform([processed_summary, processed_query])

    # Calculate cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    metrics['cosine_relevance'] = float(cosine_sim) # Convert to float for JSON serialization

    # Also keep the basic keyword matching for comparison/additional metric
    relevance_score = 0
    keywords = set()
    for company in companies_data:
        if 'SearchQuery' in company and company['SearchQuery']:
            keywords.add(company['SearchQuery'].lower())
        if 'Company Name' in company and company['Company Name']:
            keywords.add(company['Company Name'].lower())
        if 'Symbol' in company and company['Symbol']:
            keywords.add(company['Symbol'].lower())
            
    all_keywords = set()
    for kw in keywords:
        all_keywords.add(kw)
        for word in kw.split():
            all_keywords.add(word)

    summary_lower = summary_text.lower()
    for keyword in all_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', summary_lower):
            relevance_score += 1
            
    metrics['relevance_keywords_found'] = relevance_score
    metrics['relevant_keywords_list'] = list(all_keywords) # For debugging/inspection

    return metrics

