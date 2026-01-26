import re
from thefuzz import fuzz

def verify_citations(ai_response, source_documents):
    # Find [Doc Name, p. X]
    citation_pattern = r"\[(.*?),\s*p\.\s*(\d+)\]"
    matches = re.findall(citation_pattern, ai_response)
    
    results = []
    for doc_name, page_num in matches:
        page_idx = int(page_num) - 1
        
        # Check if the doc exists in your 50+ files
        if doc_name in source_documents and page_idx < len(source_documents[doc_name]):
            actual_text = source_documents[doc_name][page_idx].lower()
            
            # Grab the sentence the AI wrote before the citation
            parts = ai_response.split(f"[{doc_name}, p. {page_num}]")
            claim = parts[0].strip().split('.')[-1][-150:].lower()
            
            # Fuzzy match (Is the claim similar to the text on the page?)
            score = fuzz.token_set_ratio(claim, actual_text)
            
            results.append({
                "source": doc_name,
                "page": page_num,
                "score": score,
                "verified": score > 75 # 75% similarity = Pass
            })
    return results
