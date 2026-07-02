from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, json, time
@dataclass
class ArtifactEvidence:
    path:str; kind:str; producer:str; verifier:str; sha256:str=''
    def materialize(self)->'ArtifactEvidence':
        p=Path(self.path)
        if p.exists() and p.is_file(): self.sha256=hashlib.sha256(p.read_bytes()).hexdigest()
        return self
def write_evidence_ledger(path:str|Path, artifacts:list[ArtifactEvidence])->dict:
    rows=[asdict(a.materialize()) for a in artifacts]; errors=[]
    for r in rows:
        if not r['sha256']: errors.append(f"missing artifact or checksum: {r['path']}")
        if not r['producer'] or not r['verifier']: errors.append(f"producer/verifier required: {r['path']}")
    data={'created_at':time.time(),'ok':not errors,'errors':errors,'artifacts':rows}
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data
