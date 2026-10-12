"""The pictures in this identity's docs match its spec (tools/gen_diagrams.py).

Agent pictures come from identity/routes.json and the agents' edge tables;
playbook pictures from the playbook data; where this repo has end-to-end
playbook tests, docs/PLAY-BY-PLAY.md shows real runs. A change that is not
regenerated fails here. Regenerate with: python tools/gen_diagrams.py
"""
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import gen_diagrams  # noqa: E402


def test_diagrams_are_current():
    files = gen_diagrams.build()
    stale = [os.path.relpath(p, ROOT) for p, body in files.items()
             if not os.path.exists(p) or open(p).read() != body]
    assert stale == [], f"run python tools/gen_diagrams.py: {stale}"


def test_every_agent_and_playbook_folder_has_a_picture():
    files = gen_diagrams.build()
    folders = glob.glob(os.path.join(ROOT, "[0-1][0-9]-*")) + \
        [d for d in glob.glob(os.path.join(ROOT, "playbooks", "P*")) if os.path.isdir(d)]
    assert folders
    for d in folders:
        body = files[os.path.join(d, "README.md")]
        assert "```mermaid" in body, d


def test_every_edge_has_words():
    gen_diagrams.build()
    assert gen_diagrams.FALLBACKS == set(), sorted(gen_diagrams.FALLBACKS)
