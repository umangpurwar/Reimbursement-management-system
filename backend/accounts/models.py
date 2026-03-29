from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):

    class Role(models.TextChoices):
        EMPLOYEE = "employee", _("Employee")
        MANAGER = "manager", _("Manager")
        ADMIN = "admin", _("Admin")

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
        verbose_name=_("Role"),
    )

    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
        verbose_name=_("Manager"),
        help_text=_("The user's direct manager. Null for top-level users."),
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["username"]

    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # Convenience helpers
    

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role == self.Role.MANAGER

    @property
    def is_employee(self) -> bool:
        return self.role == self.Role.EMPLOYEE

    def get_direct_reports(self):
        """Return all users that report directly to this user."""
        return self.direct_reports.all()
    