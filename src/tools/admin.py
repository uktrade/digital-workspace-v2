from core.admin import admin_site
from tools.models import IrapToolData, IrapToolDataImport, Tool


# Really crude admin, to be used for development

admin_site.register(IrapToolData)
admin_site.register(IrapToolDataImport)
admin_site.register(Tool)
