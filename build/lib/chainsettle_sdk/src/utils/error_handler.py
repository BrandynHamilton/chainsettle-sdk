from functools import wraps
from typing import Callable, Any
import requests

def handle_api_error(func: Callable) -> Callable:
    """
    Decorador para manejar errores comunes de la API de ChainSettle.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.ConnectionError):
                raise Exception("Error de conexión con ChainSettle. Por favor, verifica tu conexión a internet.")
            elif isinstance(e, requests.exceptions.Timeout):
                raise Exception("La solicitud a ChainSettle ha excedido el tiempo de espera.")
            elif isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 404:
                    raise Exception("El recurso solicitado no fue encontrado en ChainSettle.")
                elif e.response.status_code == 401:
                    raise Exception("No autorizado para acceder a ChainSettle.")
                elif e.response.status_code == 403:
                    raise Exception("Acceso denegado a ChainSettle.")
                elif e.response.status_code == 429:
                    raise Exception("Demasiadas solicitudes a ChainSettle. Por favor, espera un momento.")
                else:
                    raise Exception(f"Error HTTP {e.response.status_code}: {e.response.text}")
            else:
                raise Exception(f"Error al comunicarse con ChainSettle: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Error de validación: {str(e)}")
        except Exception as e:
            raise Exception(f"Error inesperado: {str(e)}")
    
    return wrapper 