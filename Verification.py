import re
from thefuzz import fuzz

def verify_citations(ai_response, source_documents):
    citation_pattern = r"\[(.*?),\s*p\.\s*(\d+)\]"
    matches = re.findall(citation_pattern, ai_response)
    
    results = []
    for doc_name, page_num in matches:
        page_idx = int(page_num) - 1
        if doc_name in source_documents and page_idx < len(source_documents[doc_name]):
            actual_text = source_documents[doc_name][page_idx].lower()
            
            # Logic: If text is marked [UNCLEAR], lower the score
            if "[unclear]" in actual_text.lower():
                score = 30 # Forced low score for handwriting warning
            else:
                parts = ai_response.split(f"[{doc_name}, p. {page_num}]")
                claim = parts[0].strip().split('.')[-1][-150:].lower()
                score = fuzz.token_set_ratio(claim, actual_text)
            
            results.append({
                "source": doc_name, "page": page_num, 
                "score": score, "verified": score > 75
            })
    return results
