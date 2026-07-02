import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mindriver.delivery_evidence import ArtifactEvidence, write_evidence_ledger

def test_evidence_ledger_hashes_file(tmp_path):
    f=tmp_path/'out.txt'; f.write_text('done')
    data=write_evidence_ledger(tmp_path/'ledger.json',[ArtifactEvidence(str(f),'report','worker','qa')])
    assert data['ok'], data
    assert len(data['artifacts'][0]['sha256']) == 64

def test_evidence_ledger_rejects_missing_file(tmp_path):
    data=write_evidence_ledger(tmp_path/'ledger.json',[ArtifactEvidence(str(tmp_path/'missing.txt'),'report','worker','qa')])
    assert not data['ok']
