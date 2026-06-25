from api.artifact_binding_api import router


def test_specific_route_precedes_generic_route() -> None:
    paths = [route.path for route in router.routes]
    assert paths.index("/artifact-bindings/by-model/{model_key:path}") < paths.index("/artifact-bindings/{binding_id}")
