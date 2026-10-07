from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """Unauthenticated liveness/readiness probe for the ALB target group
    defined in infra/templates/edge.yaml (HealthCheckPath). Confirms the
    app can actually reach its database, not just that the process is up."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "error"}, status=503)
    return JsonResponse({"status": "ok"})
