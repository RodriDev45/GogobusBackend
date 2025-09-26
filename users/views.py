from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import RegisterSerializer, UserSerializer, EmailTokenObtainPairSerializer
from utils.responses import success_response, error_response

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return success_response(
                data=response.data,
                message="Login exitoso"
            )
        except Exception as e:
            return error_response(message="Credenciales inválidas", status_code=401)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        user = result["user"]
        tokens = result["tokens"]

        return success_response(
            data={
                "user": UserSerializer(user).data,
                "tokens": tokens
            },
            message="Registro exitoso",
            status_code=status.HTTP_201_CREATED
        )

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=UserSerializer(self.get_object()).data,
            message="Detalle del usuario"
        )
    
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="Logout exitoso", status_code=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return error_response(message="Token inválido", status_code=status.HTTP_400_BAD_REQUEST)
