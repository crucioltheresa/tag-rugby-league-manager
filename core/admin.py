from django.contrib import admin
from .models import InterestRegistration, EmailWhitelist


@admin.register(InterestRegistration)
class InterestRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "team_name",
        "is_mixed",
        "estimated_players",
        "played_before",
        "status",
        "submitted_at",
    )
    list_filter = ("status", "is_mixed", "played_before")
    search_fields = ("first_name", "last_name", "email", "team_name")
    readonly_fields = ("submitted_at",)
    ordering = ("-submitted_at",)
    actions = ["approve_registrations", "reject_registrations"]

    fieldsets = (
        ("Contact", {
            "fields": ("first_name", "last_name", "email", "phone_number"),
        }),
        ("Team", {
            "fields": ("team_name", "is_mixed", "estimated_players", "female_players", "male_players"),
        }),
        ("Other", {
            "fields": ("played_before", "message"),
        }),
        ("Status", {
            "fields": ("status", "submitted_at"),
        }),
    )

    @admin.display(description="Name")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def save_model(self, request, obj, form, change):
        previous_status = InterestRegistration.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        super().save_model(request, obj, form, change)
        if obj.status == "approved" and previous_status != "approved":
            EmailWhitelist.objects.get_or_create(
                email=obj.email,
                defaults={"source": "admin", "interest_registration": obj},
            )

    @admin.action(description="Approve selected registrations")
    def approve_registrations(self, request, queryset):
        approved = 0
        for reg in queryset.exclude(status="approved"):
            reg.status = "approved"
            reg.save()
            EmailWhitelist.objects.get_or_create(
                email=reg.email,
                defaults={"source": "admin", "interest_registration": reg},
            )
            approved += 1
        self.message_user(request, f"{approved} registration(s) approved and added to the whitelist.")

    @admin.action(description="Reject selected registrations")
    def reject_registrations(self, request, queryset):
        updated = queryset.exclude(status="rejected").update(status="rejected")
        self.message_user(request, f"{updated} registration(s) rejected.")


@admin.register(EmailWhitelist)
class EmailWhitelistAdmin(admin.ModelAdmin):
    list_display = ("email", "source", "used", "created_at")
    list_filter = ("source", "used")
    search_fields = ("email",)
    readonly_fields = ("created_at",)
