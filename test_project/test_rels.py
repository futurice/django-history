from test_project.tests import *

class HistoryTest(BaseSuite):
    def setUp(self):
        self.rf = RequestFactory()
        self.user_model = get_user_model()

    def test_changes(self):
        user = self.user_model.objects.create(username='BobbyTables')

        p0 = Publication.objects.create(title='Alice in Wonderland')
        self.assertTrue(History.objects.by_created('')[0].object_id, p0.pk)
        p = Publication.objects.create(title='Bobsled')
        self.assertTrue(History.objects.by_created('')[0].object_id, p.pk)
        p.title = 'Where is my title'
        p.save()
        a = Article.objects.create(headline='Once upon a time')
        a.publications.add(p)

        history = History.objects.by_instance(a).order_by('id')
        a_ct = ContentType.objects.get_for_model(a)
        self.assertTrue(history.count(), 2)
        self.assertEqual(history[0].action, ACTIONS.for_constant('save').value)
        self.assertEqual(history[0].model, a_ct.pk)
        self.assertEqual(history[1].action, ACTIONS.for_display('m2m.add').value)
        self.assertEqual(history[1].model, a_ct.pk)
        self.assertEqual(history[1].changes['fields']['publications']['changed'], [p.pk])

        history_count_before = history_count()
        num_history_entries = len([a, a.publications.all()])
        p.delete()
        self.assertEqual(history_count_before, history_count() - num_history_entries)

        self.assertEqual(
                History.objects.filter(user__isnull=True).count(),
                history_count())

        cnt = Counter()
        for k in History.objects.all().order_by('id'):
            self.assertTrue(ContentType.objects.get(pk=k.model))
            cnt[k.action] += 1
            for i,j in six.iteritems(k.changes['fields']):
                self.assertTrue(all(l in j for l in ['new', 'old'] if k.action in ['save']))
                self.assertTrue(all(l in j for l in ['changed'] if k.action in ['post_add', 'post_delete']))
                self.assertTrue((k.changes['fields']['id']['new'] is not None) if k.action in ['delete'] else True)
                self.assertTrue((k.changes['fields']['id']['old'] is not None) if k.action in ['delete'] else True)
        self.assertTrue(all(action_id(k) in cnt.keys() for k in ['save','delete','m2m.add']))

    def test_with_user(self):
        user = self.user_model.objects.create(username='BobbyTables')
        a = Article.objects.create(headline='Once upon a time')

        History.objects.add(
                action='save',
                changes={'headline': {'new': 'A Time', 'old': a.headline}},
                model=a,
                user=user,)

        self.assertEqual(History.objects.by_user(user).count(), 1)

    def test_view(self):
        a = Article.objects.create(headline='Once upon a time')
        view = LatestView.as_view()
        content = view(self.rf.get(reverse('history-latest'))).render()

    def test_diff(self):
        a = Article.objects.create(headline='Once upon a time')
        a.headline = 'Once upon a time there was'
        a.save()

        publisher = Publisher.objects.create(name="O'Really")
        p = Publication.objects.create(title='Ponytales')
        p.publisher = publisher
        p.save()

    def test_changes_tz_aware_datetime(self):
        publisher = Publisher.objects.create(name="O'Really")
        before = copy.deepcopy(publisher.created)
        publisher.created = now()
        publisher.save()
        self.assertNotEquals(before, publisher.created)

    def test_custom_user(self):
        user = self.user_model.objects.create(username='BobbyTables')
        user.first_name = 'Lakemoore'
        user.save()

    def test_changes_fk(self):
        publisher = Publisher.objects.create(name="O'Really")
        publisher2 = Publisher.objects.create(name="Alyson Books")
        p = Publication.objects.create(title='Ponytales')
        p.publisher = publisher
        p.save()
        p.publisher = publisher2
        p.save()

        a = Article.objects.create(headline='How Potatoes Are Made')
        a.publications.add(p)

        view = LatestView.as_view()
        content = view(self.rf.get(reverse('history-latest'))).render()

    def test_nested_settings(self):
        self.assertTrue(get_setting('EXCLUDE_CHANGES'))
        excludes = get_setting('EXCLUDE_CHANGES')
        self.assertTrue(excludes['test_project.user'])

        user = self.user_model.objects.create(username='Somebody')
        change_count = History.objects.all().count()
        user.last_login = now()
        user.save()

        self.assertEqual(History.objects.all().count(), change_count)


    def test_changes_have_changes(self):
        name = 'BobbyTables'
        user = self.user_model.objects.create(username=name)
        change_count = History.objects.all().count()
        user.first_name = 'Lakemoore'
        user.save()

        self.assertEqual(History.objects.all().count(), change_count+1)

        user, _ = self.user_model.objects.get_or_create(username=name)
        user.save()

        self.assertEqual(History.objects.all().count(), change_count+1)
