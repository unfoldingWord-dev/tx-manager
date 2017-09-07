from __future__ import print_function, unicode_literals
import logging
from libraries.aws_tools.s3_handler import S3Handler


class DownloadMetrics(object):
    ACCESS_FAILED_ERROR = 'could not access bucket for : '

    def __init__(self, pre_convert_bucket=None):
        """
        :param string pre_convert_bucket:
        """
        self.logger = logging.getLogger('tx-manager')
        self.logger.addHandler(logging.NullHandler())
        self.pre_convert_bucket = pre_convert_bucket
        self.preconvert_handler = None

    def check_download(self, commit_id):
        self.logger.debug("Start: check for download: " + commit_id)

        response = {  # default to error
            'ErrorMessage': DownloadMetrics.ACCESS_FAILED_ERROR + commit_id
        }

        if not commit_id:
            self.logger.warning("Invalid commit: " + commit_id)
            return response

        if not self.preconvert_handler:
            self.preconvert_handler = S3Handler(self.pre_convert_bucket)

        key = 'preconvert/{0}.zip'.format(commit_id)
        download_exists = False
        try:
            download_exists = self.preconvert_handler.key_exists(key)
        except Exception as e:
            self.logger.error("Access failure for '" + key + "': " + str(e))
            return response

        del response['ErrorMessage']
        self.logger.debug("Download exists for '" + key + "': " + str(download_exists))
        response['download_exists'] = download_exists
        return response
