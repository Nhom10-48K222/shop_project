from django.contrib import admin
from .models import ShippingAddress

# Register your models here.

admin.site.register(ShippingAddress)
from django.contrib import admin
from .models import ContactMessage

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'sent_at')  # Các cột hiển thị
    search_fields = ('first_name', 'last_name', 'email')  # Cho phép tìm kiếm
    list_filter = ('sent_at',)  # Bộ lọc theo thời gian gửi

admin.site.register(ContactMessage, ContactMessageAdmin)