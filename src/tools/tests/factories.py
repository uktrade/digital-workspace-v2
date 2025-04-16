from tools.models import Tool
from working_at_dit.tests.factories import PageWithTopicsFactory


class ToolFactory(PageWithTopicsFactory):
    class Meta:
        model = Tool
