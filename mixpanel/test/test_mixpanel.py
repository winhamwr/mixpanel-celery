import unittest
import mixpanel


class TestInitFile(unittest.TestCase):

    def test_version(self):
        self.assertTrue(mixpanel.VERSION)
        self.assertEquals(len(mixpanel.VERSION), 4)

    def test_meta(self):
        for m in ("__author__", "__contact__", "__homepage__",
                "__docformat__", "__version__", "__release__", "__doc__"):
            self.assertTrue(getattr(mixpanel, m, None))