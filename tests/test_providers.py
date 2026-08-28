from civicos.core.providers import provider_for, composition_status

def test_existing_projects_cover_core_capabilities():
    required = ["entity_resolution","legal_retrieval","document_extraction","budget_lookup","change_monitoring","evaluation","human_approval"]
    status = composition_status(required)
    assert status["coverage"] == 1.0
    assert not status["missing"]

def test_gitlaw_owns_legal_retrieval():
    assert any(p["provider_id"] == "gitlaw" for p in provider_for("legal_retrieval"))
