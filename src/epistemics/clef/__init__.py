"""Clef pilot (docs/clef-pilot-design.md): the disposition cases put to Cloudflare's decision models.

Clef and Clef-flash take a state and typed questions and return a probability for every allowed
answer. The pilot sends them the rendered cases the agent configurations answered (evident,
hinted and description cases), as single questions and as joint calls that ask a case's base rate,
structure probe and forecast together.

  requests  deterministic request bodies and the frozen plan
  client    Workers AI REST client (credentials from the environment only)
  answers   parsing of noul and choice answers
  pilot     plan, run (resumable, append-only records) and the smoke test
"""
