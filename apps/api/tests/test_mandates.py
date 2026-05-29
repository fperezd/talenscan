def test_mandate_crud_flow(client) -> None:
    create_payload = {
        "client_name": "Cliente Demo",
        "search_title": "Gerencia Comercial",
        "target_role": "Gerente Comercial",
        "industry": "Servicios",
        "country": "Chile",
        "city": "Santiago",
        "work_mode": "Hibrido",
        "seniority_level": "Senior",
        "reports_to": "CEO",
        "business_context": "Crecimiento regional",
        "role_objective": "Escalar ventas enterprise",
        "key_challenges": "Estructurar equipo",
        "main_responsibilities": ["Liderar equipo", "Definir estrategia"],
        "expected_results": ["+20% ventas"],
        "must_have_requirements": ["10 anos experiencia"],
        "nice_to_have_requirements": ["MBA"],
        "target_companies": ["Empresa A"],
        "target_industries": ["Tecnologia"],
        "equivalent_roles": ["Head of Sales"],
        "compensation_context": "Mercado competitivo",
        "urgency": "Alta",
        "comments": "Prioridad Q2",
        "status": "Activo",
    }

    create_response = client.post("/api/mandatos", json=create_payload)
    assert create_response.status_code == 201
    created = create_response.json()
    mandate_id = created["id"]
    assert created["client_name"] == "Cliente Demo"

    list_response = client.get("/api/mandatos")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/mandatos/{mandate_id}")
    assert get_response.status_code == 200
    assert get_response.json()["search_title"] == "Gerencia Comercial"

    update_response = client.put(
        f"/api/mandatos/{mandate_id}",
        json={"status": "Con shortlist", "comments": "Actualizado"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "Con shortlist"

    delete_response = client.delete(f"/api/mandatos/{mandate_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/mandatos/{mandate_id}")
    assert missing_response.status_code == 404
