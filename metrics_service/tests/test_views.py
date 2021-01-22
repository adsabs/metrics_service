from flask_testing import TestCase
from metrics_service import app
import unittest
import mock

class TestViews(TestCase):
    '''Test some basic properties of views'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app()
        return app_

    def test_MetricsView(self):
        from metrics_service.views import Metrics

        self.assertEqual(Metrics.__class__.__name__, 'MethodViewType')
        self.assertEqual(list(Metrics.methods), ['POST'])
        self.assertEqual(Metrics.endpoint, 'metrics')
        self.assertTrue(hasattr(Metrics ,'scopes'))
        self.assertTrue(hasattr(Metrics ,'rate_limit'))

    @mock.patch('metrics_service.views.generate_metrics', return_value='foo')
    def test_PubMetricsView(self, mock_generate_metrics):
        from metrics_service.views import PubMetrics

        self.assertEqual(PubMetrics.__class__.__name__, 'MethodViewType')
        self.assertEqual(list(PubMetrics.methods), ['GET'])
        self.assertEqual(PubMetrics.endpoint, 'pubmetrics')
        self.assertTrue(hasattr(PubMetrics ,'scopes'))
        self.assertTrue(hasattr(PubMetrics ,'rate_limit'))

        res = PubMetrics().get('bibcode')
        self.assertEqual(res, 'foo')

    def test_DetailMetricsView(self):
        from metrics_service.views import DetailMetrics

        self.assertEqual(DetailMetrics.__class__.__name__, 'MethodViewType')
        self.assertEqual(list(DetailMetrics.methods), ['POST'])
        self.assertEqual(DetailMetrics.endpoint, 'detailmetrics')
        self.assertTrue(hasattr(DetailMetrics ,'scopes'))
        self.assertTrue(hasattr(DetailMetrics ,'rate_limit'))

class TestLocalApp(TestCase):
    '''Test some basic properties of views'''

    def create_app(self):
        '''Create the wsgi application'''
        app_ = app.create_app(**{"FOO":"BAR"})
        return app_

    def test_MetricsView(self):
        from metrics_service.views import Metrics
        self.assertEqual(self.app.config['FOO'], 'BAR')

