from django.test import RequestFactory, SimpleTestCase, override_settings

from .services import VademecumService, normalize_medicamento, normalize_vademecum_response
from .views import buscar_vademecum, vademecum_page


class FakeClient:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        return {
            "medicamentos": [
                {
                    "nombreProducto": "AMPLIAR",
                    "nombreDroga": "atorvastatin",
                    "presentacion": "20 mg comp.x 30",
                    "regNo": "24818",
                }
            ],
            "pageInfo": {"numeroPagina": 1, "tieneMasResultados": True},
        }


class VademecumServiceTests(SimpleTestCase):
    def test_normalizes_common_list_response(self):
        self.assertEqual(normalize_vademecum_response({"items": [1, 2]}), [1, 2])

    @override_settings(
        QBI2_VADEMECUM_PATH="/apirecipe/GetMedicamento/{search}",
        QBI2_VADEMECUM_PAGE_PARAM="numeroPagina",
        QBI2_CLIENT_APP_ID="563",
        QBI2_CLIENT_APP_ID_PARAM="clienteAppId",
        QBI2_INCLUDE_CLIENT_APP_ID_IN_VADEMECUM=True,
    )
    def test_builds_provider_query(self):
        client = FakeClient()
        result = VademecumService(client=client).buscar("atorva", page=2)

        self.assertEqual(result["items"][0]["regNo"], "24818")
        self.assertEqual(result["page_info"], {"numeroPagina": 1, "tieneMasResultados": True})
        self.assertEqual(client.calls[0][0], "/apirecipe/GetMedicamento/atorva")
        self.assertEqual(client.calls[0][1]["numeroPagina"], 2)
        self.assertEqual(client.calls[0][1]["clienteAppId"], "563")

    def test_normalizes_medicamento_display(self):
        item = normalize_medicamento(
            {
                "nombreProducto": "AMPLIAR",
                "nombreDroga": "atorvastatin",
                "presentacion": "20 mg comp.x 30",
                "regNo": "24818",
            }
        )

        self.assertEqual(item["display"], "AMPLIAR - atorvastatin - 20 mg comp.x 30")
        self.assertEqual(item["regNo"], "24818")


class VademecumViewTests(SimpleTestCase):
    def test_requires_query(self):
        request = RequestFactory().get("/qbi2/api/vademecum/buscar/")
        response = buscar_vademecum(request)

        self.assertEqual(response.status_code, 400)

    def test_vademecum_page_renders_search_ui(self):
        request = RequestFactory().get("/vademecum/")
        response = vademecum_page(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"vademecum-input", response.content)
        self.assertIn(b"/qbi2/api/vademecum/buscar/", response.content)
