import re
from thefuzz import fuzz

def verify_citations(ai_response, source_documents):
    # البحث عن الاستشهادات مثل [اسم الملف, p. رقم الصفحة]
    citation_pattern = r"\[(.*?),\s*p\.\s*(\d+)\]"
    matches = re.findall(citation_pattern, ai_response)
    
    results = []
    for doc_name, page_num in matches:
        page_idx = int(page_num) - 1
        
        if doc_name in source_documents and page_idx < len(source_documents[doc_name]):
            actual_text = source_documents[doc_name][page_idx].lower()
            
            # استخراج الادعاء قبل الاستشهاد مباشرة
            parts = ai_response.split(f"[{doc_name}, p. {page_num}]")
            claim = parts[0].strip().split('.')[-1][-150:].lower()
            
            # مطابقة ذكية (تدعم العربي والإنجليزي)
            score = fuzz.token_set_ratio(claim, actual_text)
            
            results.append({
                "source": doc_name,
                "page": page_num,
                "score": score,
                "verified": score > 70 # درجة مطابقة 70% تعتبر ناجحة
            })
    return results
