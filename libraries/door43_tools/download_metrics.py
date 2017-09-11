from __future__ import print_function, unicode_literals
from libraries.app.app import App


class DownloadMetrics(object):
    ACCESS_FAILED_ERROR = 'could not access bucket for : '

    def check_download(self, commit_id):
        App.logger.debug("Start: check for download: " + commit_id)

        response = {  # default to error
            'ErrorMessage': DownloadMetrics.ACCESS_FAILED_ERROR + commit_id
        }

        if not commit_id:
            App.logger.warning("Invalid commit: " + commit_id)
            return response

        key = 'preconvert/{0}.zip'.format(commit_id)
        try:
            download_exists = App.pre_convert_s3_handler.key_exists(key)
        except Exception as e:
            App.logger.error("Access failure for '" + key + "': " + str(e))
            return response

        del response['ErrorMessage']
        App.logger.debug("Download exists for '" + key + "': " + str(download_exists))
        response['download_exists'] = download_exists
        return response
