from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accounts.models import User

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import ApprovalStep, Expense


UserModel = get_user_model()

# User


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Lightweight read-only snapshot.
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserModel  
        fields = ["id", "username", "full_name", "email", "role"]
        read_only_fields = fields

    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username


class UserSerializer(serializers.ModelSerializer):
    """
    Full serializer for create / update flows.
    """

    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserModel 
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "manager",
            "is_active",
            "date_joined",
            "password",
        ]
        read_only_fields = ["id", "date_joined", "full_name"]
        extra_kwargs = {
            "manager": {"required": False, "allow_null": True},
        }

    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username

    def create(self, validated_data: dict) -> "User":
        password = validated_data.pop("password")
        user = UserModel(**validated_data) 
        user.set_password(password)
        user.save()
        return user

    def update(self, instance: "User", validated_data: dict) -> "User":
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

# Expense

class ExpenseSerializer(serializers.ModelSerializer):
    """
    Full Expense serializer.
    """

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_detail = UserMinimalSerializer(source="user", read_only=True)

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    approval_steps = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "user",
            "user_detail",
            "amount",
            "category",
            "category_display",
            "description",
            "date",
            "status",
            "status_display",
            "current_step",
            "approval_steps",
            "created_at",
        ]
        read_only_fields = ["id", "status", "current_step", "created_at"]

    def get_approval_steps(self, obj) -> list[dict]:
        steps = obj.approval_steps.select_related("approver").order_by("step_number")
        return [
            {
                "step_number": s.step_number,
                "approver_id": s.approver_id,
                "approver_username": s.approver.username,
                "status": s.status,
                "action_date": s.action_date,
            }
            for s in steps
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Expense date cannot be in the future.")
        return value


class ExpenseListSerializer(serializers.ModelSerializer):
    """
    Slim serializer for list views.
    """

    user_detail = UserMinimalSerializer(source="user", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "user_detail",
            "amount",
            "category_display",
            "date",
            "status",
            "status_display",
            "current_step",
            "created_at",
        ]
        read_only_fields = fields

# ApprovalStep

class ApprovalStepSerializer(serializers.ModelSerializer):
    """
    Manager-facing serializer.
    """

    approver_detail = UserMinimalSerializer(source="approver", read_only=True)
    expense_detail = serializers.SerializerMethodField(read_only=True)

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ApprovalStep
        fields = [
            "id",
            "expense",
            "expense_detail",
            "approver",
            "approver_detail",
            "step_number",
            "status",
            "status_display",
            "comment",
            "action_date",
        ]
        read_only_fields = [
            "id",
            "expense",
            "expense_detail",
            "approver",
            "approver_detail",
            "step_number",
            "status_display",
            "action_date",
        ]
        extra_kwargs = {
            "expense": {"read_only": True},
            "approver": {"read_only": True},
            "comment": {"required": False, "allow_blank": True},
        }

    def get_expense_detail(self, obj) -> dict:
        e = obj.expense
        return {
            "id": e.id,
            "amount": str(e.amount),
            "category": e.get_category_display(),
            "description": e.description,
            "date": e.date,
            "submitted_by": e.user.get_full_name() or e.user.username,
            "total_steps": e.approval_steps.count(),
        }

    def validate_status(self, value: str) -> str:
        allowed = {ApprovalStep.Status.APPROVED, ApprovalStep.Status.REJECTED}
        if value not in allowed:
            raise serializers.ValidationError(
                "Only 'approved' or 'rejected' are valid actions."
            )

        instance = self.instance
        if instance and instance.status != ApprovalStep.Status.PENDING:
            raise serializers.ValidationError(
                "This step has already been actioned."
            )

        return value

    def update(self, instance: ApprovalStep, validated_data: dict) -> ApprovalStep:
        new_status = validated_data.get("status")
        comment = validated_data.get("comment", "")

        if new_status == ApprovalStep.Status.APPROVED:
            instance.approve(comment=comment)
        elif new_status == ApprovalStep.Status.REJECTED:
            instance.reject(comment=comment)

        return instance