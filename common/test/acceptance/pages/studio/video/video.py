import requests
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.javascript import wait_for_js, js_defined

SELECTORS = {
    'video_init': '.is-initialized',
    'video_xmodule': '.xmodule_VideoModule',
    'video_spinner': '.video-wrapper .spinner',
    'video_controls': 'section.video-controls',
    'handout_download': '.video-handout.video-download-button a',
    'handout_download_editor': '.wrapper-comp-setting.file-uploader .download-action',
}


@js_defined('window.Video', 'window.RequireJS.require', 'window.jQuery', 'window.XModule', 'window.XBlock',
            'window.MathJax.isReady')
class VidoComponentPage(PageObject):
    """
    CMS Video Component Page
    """

    url = None

    @wait_for_js
    def is_browser_on_page(self):
        return self.q(css='div{0}'.format(SELECTORS['video_xmodule'])).present

    def _wait_for(self, check_func, desc, result=False, timeout=200):
        """
        Calls the method provided as an argument until the Promise satisfied or BrokenPromise

        Arguments:
            check_func (callable): Promise function to be fulfilled.
            desc (str): Description of the Promise, used in log messages.
            result (bool): Indicates whether we need result from Promise or not
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out.

        """
        if result:
            return Promise(check_func, desc, timeout=timeout).fulfill()
        else:
            return EmptyPromise(check_func, desc, timeout=timeout).fulfill()

    def wait_for_video_component_render(self):
        """
        Wait until video component rendered completely
        """
        self._wait_for(lambda: self.q(css=SELECTORS['video_init']).present, 'Video Player Initialized')
        self._wait_for(lambda: not self.q(css=SELECTORS['video_spinner']).visible, 'Video Buffering Completed')
        self._wait_for(lambda: self.q(css=SELECTORS['video_controls']).visible, 'Video Player Controls are Visible')

    def _get_handout(self, url):
        """
        Download handout at `url`
        """
        kwargs = dict()

        session_id = [{i['name']: i['value']} for i in self.browser.get_cookies() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)
        return response.status_code < 400, response.headers, response.content

    def download_handout(self, mime_type, is_editor=False):
        """
        Download handout with mime type specified by `mime_type`

        Arguments:
            mime_type (str): mime type of handout file

        Returns:
            tuple: Handout download result.

        """
        selector = SELECTORS['handout_download_editor'] if is_editor else SELECTORS['handout_download']

        handout_url = self.q(css=selector).attrs('href')[0]
        result, headers, content = self._get_handout(handout_url)

        return result, headers['content-type'] == mime_type

    def is_download_handout_button_visible(self):
        """
        Check if handout download button is visible
        """
        return self.q(css=SELECTORS['handout_download']).visible
