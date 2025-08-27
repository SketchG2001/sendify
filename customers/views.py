from pip._internal.configuration import Configuration
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser, Configurations
from .serializers import ConfigurationsSerializer

class AuthViewSet(viewsets.ViewSet):

    @action(detail=False, methods=["get", "post"])
    def signup(self, request):
        if request.method == "GET":
            return Response({"message": "Send POST request with email, name, password to register"})
        
        # Handle actual signup (POST)
        email = request.data.get("email")
        name = request.data.get("name")
        password = request.data.get("password")
        
        if not all([email, name, password]):
            return Response(
                {"error": "Email, name, and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new user
        try:
            user = CustomUser.objects.create_user(
                email=email,
                name=name,
                password=password
            )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "message": "User registered successfully",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                },
                "user": {
                    "email": user.email,
                    "name": user.name
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Registration failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get", "post"])
    def login(self, request):
        if request.method == "GET":
            return Response({"message": "Send POST request with email & password to login"})
        
        email = request.data.get("email")
        password = request.data.get("password")
        
        if not all([email, password]):
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(email=email, password=password)
        
        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login successful",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            },
            "user": {
                "email": user.email,
                "name": user.name
            }
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout by blacklisting the refresh token"""
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # requires simplejwt blacklist app enabled
            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_205_RESET_CONTENT
            )
        except TokenError:
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )
    @action(detail=False, methods=["post"])
    def refresh(self, request):
        """Refresh access token using refresh token"""
        refresh_token = request.data.get("refresh")
        
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            })
        except Exception as e:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )



class ConfigurationsView(views.APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request,config_id=None):
        """Get all configurations for the authenticated user"""
        if config_id:
            try:
                configuration = Configurations.objects.get(id=config_id, user=request.user)
            except Configurations.DoesNotExist:
                return Response({"error": "Configuration not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = ConfigurationsSerializer(configuration)
            data = serializer.data
            data['app_password'] = configuration.app_password
            return Response(data, status=status.HTTP_200_OK)

        configurations = Configurations.objects.filter(user=request.user)
        serializer = ConfigurationsSerializer(configurations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new configuration"""
        serializer = ConfigurationsSerializer(
            data=request.data,
            context={"request": request}  # 👈 pass request to serializer
        )
        if serializer.is_valid():
            serializer.save()  # user will be set inside serializer
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, config_id):
        """Update an existing configuration"""
        try:
            configuration = Configurations.objects.get(id=config_id, user=request.user)
        except Configurations.DoesNotExist:
            return Response(
                {"error": "Configuration not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ConfigurationsSerializer(
            configuration,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, config_id):
        """Delete a configuration"""
        try:
            configuration = Configurations.objects.get(id=config_id, user=request.user)
        except Configurations.DoesNotExist:
            return Response(
                {"error": "Configuration not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        configuration.delete()
        return Response(
            {"message": "Configuration deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
