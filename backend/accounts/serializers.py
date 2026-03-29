from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accounts.models import User

from django.contrib.auth import get_user_model
from rest_framework import serializers


UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length=8)
    manager_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserModel  
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "manager",
            "manager_detail",
            "is_active",
            "date_joined",
            "password",
        ]
        read_only_fields = ["id", "date_joined"]
        extra_kwargs = {
            "manager": {"required": False, "allow_null": True},
        }

    def get_manager_detail(self, obj) -> dict | None:
        if obj.manager:
            return {
                "id": obj.manager.id,
                "username": obj.manager.username,
                "full_name": obj.manager.get_full_name(),
            }
        return None

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


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Minimal read-only serializer — safe for embedding in other resources.
    """

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserModel  
        fields = ["id", "username", "full_name", "role"]
        read_only_fields = fields

    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username