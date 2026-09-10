import base64
from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from lms_modules.tutor.github_fetch import fetch_github_file


def response(data, status=200):
    return Mock(status_code=status, content=b'{}', json=lambda: data)


class GithubFolderTests(SimpleTestCase):
    @patch('lms_modules.tutor.github_fetch.requests.get')
    def test_folder_reads_text_without_following_download_urls(self, get):
        get.side_effect = [response([{'type':'file', 'path':'assignments/chapter03/a.py', 'download_url':'https://untrusted.example/a.py'}, {'type':'file','path':'assignments/chapter03/picture.png'}]), response({'type':'file','encoding':'base64','content':base64.b64encode(b'print(42)').decode()})]
        text = fetch_github_file('https://github.com/owner/repo/tree/main/assignments/chapter03')
        self.assertIn('print(42)', text)
        self.assertIn('a.py', text)
        self.assertEqual(get.call_count, 2)
        for call in get.call_args_list:
            self.assertTrue(call.args[0].startswith('https://api.github.com/repos/owner/repo/contents/'))
            self.assertFalse(call.kwargs['allow_redirects'])

    @patch('lms_modules.tutor.github_fetch.requests.get')
    def test_missing_folder_does_not_fabricate_content(self, get):
        get.return_value = response({}, 404)
        self.assertIsNone(fetch_github_file('https://github.com/owner/repo/tree/main/missing'))

    @patch('lms_modules.tutor.github_fetch.requests.get')
    def test_external_host_is_rejected(self, get):
        self.assertIsNone(fetch_github_file('https://example.com/owner/repo/tree/main/a'))
        get.assert_not_called()
