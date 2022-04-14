from django.contrib import admin

from keja_user.models import Contact, KejaUser

admin.site.register(KejaUser)
admin.site.register(Contact)
