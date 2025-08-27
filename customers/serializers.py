from rest_framework import serializers
from .models import CustomUser,Configurations

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "email", "name"]
        read_only_fields = ["id"]

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = CustomUser
        fields = ["email", "name", "password"]

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=validated_data["password"],
        )
        return user

class ConfigurationsSerializer(serializers.ModelSerializer):
    app_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = Configurations
        fields = ['id', 'user', 'email', 'app_password', 'is_active']
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        app_password = validated_data.pop("app_password")
        user = self.context["request"].user   # 👈 safe way to get the logged-in user

        config = Configurations(
            user=user,
            email=validated_data.get("email"),
            is_active=validated_data.get("is_active", True)
        )
        config.app_password = app_password  # encrypts via model property
        config.save()
        return config

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.is_active = validated_data.get("is_active", instance.is_active)

        if "app_password" in validated_data:
            instance.app_password = validated_data["app_password"]  # encrypts

        instance.save()
        return instance


