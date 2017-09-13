from __future__ import unicode_literals, print_function
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler


class DashboardHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        max_failures = int(self.retrieve(self.data, 'failures', 'Payload', required=False,
                                         default=TxManager.MAX_FAILURES))

        # Execute
        return TxManager().generate_dashboard(max_failures)
