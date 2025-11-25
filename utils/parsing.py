import tldextract

def extract_base_domain(url, include_subdomain=True):
    extracted = tldextract.extract(url)
    if include_subdomain:
        base_domain_parts = [
            part
            for part in [extracted.subdomain, extracted.domain, extracted.suffix]
            if part and part != "www"
        ]
    else:
        base_domain_parts = [
            part
            for part in [extracted.domain, extracted.suffix]
            if part and part != "www"
        ]
    base_domain = ".".join(base_domain_parts)
    return base_domain