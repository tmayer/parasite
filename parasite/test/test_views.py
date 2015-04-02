import unittest

import parasite.views as views

class ViewTestsContainer(unittest.TestCase):
    def setUp(self):
        app = views.app
        app.config['TEXTFILES_FOLDER'] = app.config['BASE_PATH'] + '/static/testfiles/textfiles/'
        app.config['TEXTFILES_FOLDER_URL_PREFIX'] = '/static/testfiles/textfiles/'
        app.config['ZIPFILES_FOLDER']  = app.config['BASE_PATH'] + '/static/testfiles/zipfiles/'
        app.config['FILE_FOLDER']  = app.config['BASE_PATH'] + '/static/testfiles/'
        self.client = views.app.test_client()


def make_test_function(url, status_code):
    def test(self):
        result = self.client.get(url)
        self.assertEqual(result.status_code, status_code,
                         "Expected: % i; got: %i for %s" % (status_code, result.status_code, url))
    return test


expected = 200
urls = ['/',
        '/full/',
        '/all/',
        '/full/all/',
        '/search/',
        '/full/search/',
        '/search/aai-x-bible-arifa/aak-x-bible-ankav/Mose/',
        '/full/search/aai-x-bible-arifa/aak-x-bible-ankav/Mose/',
        '/search/aai-x-bible-arifa/Mose/',
        '/full/search/aai-x-bible-arifa/Mose/',
        '/aai-x-bible-arifa/',
        '/full/aai-x-bible-arifa/',
        '/aai-x-bible-arifa/41/',
        '/full/aai-x-bible-arifa/41/',
        '/aai-x-bible-arifa/41/001/',
        '/full/aai-x-bible-arifa/41/001/',
        '/aai-x-bible-arifa/41/001/001/',
        '/full/aai-x-bible-arifa/41/001/001/',
        '/aai-x-bible-arifa/41001001/',
        '/full/aai-x-bible-arifa/41001001/',
        '/compare/aai-x-bible-arifa/aak-x-bible-ankav/41001001/',
        '/full/compare/aai-x-bible-arifa/aak-x-bible-ankav/41001001/',
        ]
for i, url in enumerate(urls):
    test_func = make_test_function(url, expected)
    setattr(ViewTestsContainer, 'test_200_' + str(i), test_func)

    
expected = 302
urls = ['/full/aai-x-bible-arifa.txt',
        '/full/zipall/'
        ]
for i, url in enumerate(urls):
    test_func = make_test_function(url, expected)
    setattr(ViewTestsContainer, 'test_302_' + str(i), test_func)

    
expected = 404
urls = ['/search/aai-x-bible-arifa/aak-x-bible-ankav-vXX/Mose/',
        '/full/search/aai-x-bible-arifa-vXX/aak-x-bible-ankav/Mose/',
        '/full/search/aai-x-bible-arifa-vXX/Mose/',
        '/aai-x-bible-arifa-v11/',
        '/full/aai-x-bible-arifa-v11/',
        '/aai-x-bible-arifa/40/',
        '/full/aai-x-bible-arifa/99/',
        '/aai-x-bible-arifa/41/999/',
        '/full/aai-x-bible-arifa/41/999/',
        '/aai-x-bible-arifa/41/999/001/',
        '/full/aai-x-bible-arifa/41/999/001/',        
        '/aai-x-bible-arifa/41/001/999/',
        '/full/aai-x-bible-ariXX/41/001/001/',        
        '/aai-x-bible-ariXX/41/001/001/',
        '/full/aai-x-bible-arifa/41/001/999/',
        '/aai-x-bible-arifa/41999001/',
        '/aai-x-bible-arifa/40001001/',
        '/full/aai-x-bible-arifa/41999001/',        
        '/aai-x-bible-arifa/41001999/',
        '/full/aai-x-bible-arifa/41001999/',
        '/compare/aai-x-bible-ariXX/aak-x-bible-ankav/41001001/',
        '/full/compare/aai-x-bible-arifa/aak-x-bible-ankXX/41001001/',
        '/full/compare/aai-x-bible-arifa/aak-x-bible-ankav/41999001/',
        '/full/compare/aai-x-bible-arifa/aak-x-bible-ankav/41001999/',
        ]
for i, url in enumerate(urls):
    test_func = make_test_function(url, expected)
    setattr(ViewTestsContainer, 'test_404_' + str(i), test_func)
