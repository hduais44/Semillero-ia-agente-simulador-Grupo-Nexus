def test_cargar_conocimiento():
    from src.main import cargar_conocimiento
    data, ruta = cargar_conocimiento()
    assert isinstance(data, dict)
