import asyncio, json
from pathlib import Path
import httpx
from app.core.config import settings

class ScopusError(RuntimeError): pass
class ScopusAuthError(ScopusError): pass
class ScopusEntitlementError(ScopusError): pass
class ScopusRateLimitError(ScopusError): pass

class ScopusClient:
    def __init__(self): self.quota={}; self.requests=0
    @property
    def headers(self):
        h={"X-ELS-APIKey":settings.elsevier_api_key,"Accept":"application/json"}
        if settings.elsevier_inst_token: h["X-ELS-Insttoken"]=settings.elsevier_inst_token
        return h
    async def _get(self,path:str,params:dict|None=None):
        if not settings.elsevier_api_key: raise ScopusAuthError("ELSEVIER_API_KEY is not configured")
        for attempt in range(settings.scopus_max_retries+1):
            try:
                async with httpx.AsyncClient(timeout=settings.scopus_request_timeout) as client:
                    response=await client.get(f"{settings.elsevier_base_url.rstrip('/')}/{path.lstrip('/')}",headers=self.headers,params=params)
                self.requests+=1
                self.quota={k:response.headers.get(k) for k in ("X-RateLimit-Limit","X-RateLimit-Remaining","X-RateLimit-Reset")}
                if response.status_code==401: raise ScopusAuthError("Elsevier rejected the API credentials")
                if response.status_code==403: raise ScopusEntitlementError("The API key lacks entitlement for this Scopus resource")
                if response.status_code==404: return None
                if response.status_code==429:
                    if attempt==settings.scopus_max_retries: raise ScopusRateLimitError("Scopus API rate limit reached")
                elif response.status_code<500:
                    response.raise_for_status(); return response.json()
                if attempt==settings.scopus_max_retries: response.raise_for_status()
            except (httpx.TimeoutException,httpx.NetworkError):
                if attempt==settings.scopus_max_retries: raise ScopusError("Scopus API is temporarily unavailable")
            await asyncio.sleep(min(2**attempt,8))
    async def search_authors(self,surname,given_name=None,institution=None,orcid=None):
        terms=[f"authlast({surname})"]
        if given_name: terms.append(f"authfirst({given_name})")
        if institution: terms.append(f"affil({institution})")
        if orcid: terms=[f"orcid({orcid})"]
        data=await self._get("search/author",{"query":" and ".join(terms),"count":25})
        return (data or {}).get("search-results",{}).get("entry",[])
    async def get_author_profile(self,author_id): return await self._get(f"author/author_id/{author_id}",{"view":"ENHANCED"})
    async def search_publications_by_author(self,author_id):
        start=0; result=[]
        while True:
            data=await self._get("search/scopus",{"query":f"AU-ID({author_id})","view":"COMPLETE","count":25,"start":start})
            page=(data or {}).get("search-results",{}); entries=page.get("entry",[]); result.extend(entries)
            start+=len(entries)
            if not entries or start>=int(page.get("opensearch:totalResults",len(result))): break
        return result
    async def get_abstract_details(self,eid): return await self._get(f"abstract/eid/{eid}",{"view":"FULL"})
    async def get_affiliation_details(self,affiliation_id): return await self._get(f"affiliation/affiliation_id/{affiliation_id}")
    async def get_api_status(self): return {"mode":"live","configured":bool(settings.elsevier_api_key),"quota":self.quota}

class MockScopusClient(ScopusClient):
    def __init__(self):
        super().__init__(); self.data=json.loads((Path(__file__).parents[3]/"mock_data"/"scopus.json").read_text(encoding="utf-8"))
    async def search_authors(self,surname,given_name=None,institution=None,orcid=None):
        q=f"{given_name or ''} {surname}".casefold(); return [x for x in self.data["authors"] if q.strip() in x["preferred-name"].casefold() or (orcid and x.get("orcid")==orcid)]
    async def get_author_profile(self,author_id): return next((x for x in self.data["authors"] if x["dc:identifier"].endswith(author_id)),None)
    async def search_publications_by_author(self,author_id): return [x for x in self.data["publications"] if author_id in x["author_ids"]]
    async def get_abstract_details(self,eid): return next((x for x in self.data["publications"] if x["eid"]==eid),None)
    async def get_api_status(self): return {"mode":"mock","configured":True,"quota":{}}

def get_scopus_client(): return MockScopusClient() if settings.scopus_mode=="mock" else ScopusClient()
