from test_project.tests import *

class HistoryCountTest(BaseSuite):
    def test_delete_no_rels(self):
        a = Article.objects.create(headline='Once upon a time')
        a.delete()
        self.assertEqual(history_count(),
                len(['a.create', 'a.delete']))

    def test_delete_rels(self):
        a = Article.objects.create(headline='Once upon a time')
        p = Publication.objects.create(title='Bobsled')
        a.publications.add(p)
        a.delete()
        self.assertEqual(history_count(),
                len(['a.create',
                    'p.create',
                    '.add(p) for a',
                    '.add(p) for p',
                    'a.delete',
                    'a.delete for p',]))

    def test_delete_rels_many(self):
        a = Article.objects.create(headline='Once upon a time')
        p = Publication.objects.create(title='Bobsled')
        p2 = Publication.objects.create(title='Nature')
        a.publications.add(p)
        a.publications.add(p2)
        a.delete()
        self.assertEqual(history_count(),
                len(['a.create',
                    'p.create',
                    'p2.create',
                    '.add(p) for a',
                    '.add(p) for p',
                    '.add(p2) for a',
                    '.add(p2) for p2',
                    'a.delete',
                    'a.delete for p',
                    'a.delete for p2',]))

    def test_delete_m2m(self):
        p = Publication.objects.create(title='Bobsled')
        p.delete()
        self.assertEqual(history_count(),
                len(['p.create','p.delete',]))

    def test_delete_m2m_rels(self):
        a = Article.objects.create(headline='Once upon a time')
        p = Publication.objects.create(title='Bobsled')
        a.publications.add(p)
        p.delete()
        self.assertEqual(history_count(),
                len(['a.create',
                    'p.create',
                    'a.add(p) for a',
                    'a.add(p) for p',
                    'p.delete',
                    'p.delete for a',]))

    def test_delete_m2m_rels_many(self):
        a = Article.objects.create(headline='Once upon a time')
        a2 = Article.objects.create(headline='Once upon a time 2.0')
        p = Publication.objects.create(title='Bobsled')
        a.publications.add(p)
        a2.publications.add(p)
        p.delete()
        self.assertEqual(history_count(),
                len(['a.create',
                    'a2.create',
                    'p.create',
                    'a.add(p) for a',
                    'a.add(p) for p',
                    'a2.add(p) for a2',
                    'a2.add(p) for p',
                    'p.delete',
                    'p.delete for a',
                    'p.delete for a2',
                    ]))
