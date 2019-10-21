
from odoo.tests import HttpCase


class TestUi(HttpCase):

    def test_ui_web(self):
        """Test backend tests."""
        self.phantom_js(
            "/web/tests?module=web_responsive",
            "",
            login="admin",
        )
