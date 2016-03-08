from test_project.tests import *

class HistoryViewTest(BaseSuite):
    def setUp(self):
        self.client = Client()

    def test_view_latest(self):
        p = self.client.get(reverse("history-latest"))
        self.assertEquals(p.status_code, 200)

    def test_view_ct(self):
        ct_id = ContentType.objects.all()[0].pk
        p = self.client.get(reverse("history-by-ct", kwargs=dict(ct_id=ct_id)))
        self.assertEquals(p.status_code, 200)
