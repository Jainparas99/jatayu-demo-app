from django.conf import settings
from django.core.files.storage import FileSystemStorage


class ExportStorage(FileSystemStorage):
    """Keep generated reports separate from normal uploaded documents."""

    def __init__(self, **kwargs):
        kwargs.setdefault("location", settings.EXPORT_ROOT)
        kwargs.setdefault("base_url", "/exports/")
        super().__init__(**kwargs)
