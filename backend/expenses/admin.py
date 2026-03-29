from django.contrib import admin

from .models import ApprovalStep, Expense


class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 0
    readonly_fields = ("action_date",)
    fields = ("step_number", "approver", "status", "comment", "action_date")
    ordering = ("step_number",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "category", "date", "status", "current_step", "created_at")
    list_filter = ("status", "category")
    search_fields = ("user__username", "user__email", "description")
    readonly_fields = ("created_at",)
    inlines = [ApprovalStepInline]
    ordering = ("-created_at",)


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ("id", "expense", "approver", "step_number", "status", "action_date")
    list_filter = ("status",)
    search_fields = ("approver__username", "expense__id")
    readonly_fields = ("action_date",)
    ordering = ("expense", "step_number")