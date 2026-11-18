from django.contrib import admin

from .models import AceptacionLegal, Usuario


@admin.register(Usuario)
class AdministracionUsuario(admin.ModelAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "telefono",
        "correo_verificado",
        "is_staff",
        "is_active",
    )
    list_filter = ("correo_verificado", "is_staff", "is_active", "is_superuser")
    search_fields = ("email", "first_name", "last_name", "telefono")
    fieldsets = (
        (None, {"fields": ("email",)}),
        ("Datos personales", {"fields": ("first_name", "last_name", "telefono")}),
        ("Verificación", {"fields": ("correo_verificado",)}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Seguridad", {"fields": ("password",)}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = ("password", "last_login", "date_joined")

    def has_add_permission(self, request):
        return False


@admin.register(AceptacionLegal)
class AdministracionAceptacionLegal(admin.ModelAdmin):
    list_display = ("usuario", "documento", "version", "aceptado_en")
    list_filter = ("documento", "version")
    search_fields = ("usuario__email", "usuario__first_name", "usuario__last_name")
    readonly_fields = ("usuario", "documento", "version", "aceptado_en")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("cuentas.view_aceptacionlegal")

    def has_change_permission(self, request, obj=None):
        return False
