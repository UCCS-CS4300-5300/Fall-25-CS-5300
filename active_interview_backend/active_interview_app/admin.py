from django.contrib import admin
from .models import Chat, UploadedJobListing, UploadedResume, ExportableReport

# Register your models here.
admin.site.register(Chat)
admin.site.register(UploadedJobListing)
admin.site.register(UploadedResume)
admin.site.register(ExportableReport)
