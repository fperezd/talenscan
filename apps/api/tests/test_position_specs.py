def _create_mandate(client) -> int:
    payload = {
        "client_name": "Cliente PR3",
        "search_title": "Busqueda lider comercial",
        "target_role": "Gerente Comercial",
        "industry": "Tecnologia",
        "must_have_requirements": ["Liderazgo comercial", "Gestion de pipeline"],
        "nice_to_have_requirements": ["MBA"],
        "main_responsibilities": ["Dirigir estrategia de ventas", "Liderar equipo regional"],
        "expected_results": ["Aumentar ingresos en 20%"],
        "target_industries": ["Tecnologia", "SaaS"],
        "target_companies": ["Empresa A", "Empresa B"],
        "equivalent_roles": ["Head of Sales"],
        "status": "Activo",
    }
    response = client.post("/api/mandatos", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


def test_position_spec_generation_and_update(client) -> None:
    mandate_id = _create_mandate(client)

    generated = client.post(f"/api/mandatos/{mandate_id}/generar-perfil-objetivo")
    assert generated.status_code == 201
    generated_body = generated.json()
    assert generated_body["search_mandate_id"] == mandate_id
    assert generated_body["must_have_requirements"]

    listed = client.get(f"/api/mandatos/{mandate_id}/perfiles-objetivo")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    position_spec_id = generated_body["id"]
    updated = client.put(
        f"/api/perfiles-objetivo/{position_spec_id}",
        json={"market_mapping_hypothesis": "Ajuste de mercado actualizado"},
    )
    assert updated.status_code == 200
    assert updated.json()["market_mapping_hypothesis"] == "Ajuste de mercado actualizado"
