from drf_spectacular.extensions import OpenApiAuthenticationExtension

class FirebaseAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'core.authentication.FirebaseAuthentication'
    name = 'FirebaseAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
