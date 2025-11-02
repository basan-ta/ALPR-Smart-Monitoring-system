from django.utils import timezone
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Vehicle, Sighting, Alert, PredictedRoute
from .serializers import (
    VehicleSerializer,
    SightingSerializer,
    AlertSerializer,
    PredictedRouteSerializer,
    VerificationRequestSerializer,
    VerificationResponseSerializer,
)
from .services.verification import verify_vehicle
from django.db import transaction

logger = logging.getLogger(__name__)


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().order_by('plate_number')
    serializer_class = VehicleSerializer

    @action(detail=False, methods=['get'])
    def filter_by_status(self, request):
        status_q = request.query_params.get('status')
        qs = self.get_queryset()
        if status_q:
            qs = qs.filter(status=status_q)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['get'])
    def predicted(self, request, pk=None):
        vehicle = self.get_object()
        route = PredictedRoute.objects.filter(plate_number__iexact=vehicle.plate_number).order_by('-generated_at').first()
        if route:
            return Response(PredictedRouteSerializer(route).data)
        return Response({"plate_number": vehicle.plate_number, "path": []})


class SightingViewSet(viewsets.ModelViewSet):
    queryset = Sighting.objects.all().order_by('-timestamp')
    serializer_class = SightingSerializer

    @action(detail=False, methods=['get'])
    def recent(self, request):
        minutes = int(request.query_params.get('minutes', '10'))
        since = timezone.now() - timezone.timedelta(minutes=minutes)
        qs = Sighting.objects.filter(timestamp__gte=since).order_by('-timestamp')[:500]
        payload = self.get_serializer(qs, many=True).data
        try:
            logger.info("SightingViewSet.recent: minutes=%s count=%s", minutes, len(payload))
        except Exception:
            pass
        return Response(payload)


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all().order_by('-timestamp')
    serializer_class = AlertSerializer

    @action(detail=False, methods=['get'])
    def recent(self, request):
        minutes = int(request.query_params.get('minutes', '60'))
        since = timezone.now() - timezone.timedelta(minutes=minutes)
        qs = Alert.objects.filter(timestamp__gte=since).order_by('-timestamp')[:200]
        payload = self.get_serializer(qs, many=True).data
        try:
            logger.info("AlertViewSet.recent: minutes=%s count=%s", minutes, len(payload))
        except Exception:
            pass
        return Response(payload)

    @action(detail=True, methods=['get', 'post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.acknowledged = True
        alert.dispatched = True  # simulate dispatch action
        alert.save(update_fields=['acknowledged', 'dispatched'])
        return Response(self.get_serializer(alert).data)


class PredictedRouteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PredictedRoute.objects.all().order_by('-generated_at')
    serializer_class = PredictedRouteSerializer


class StatsView(APIView):
    def get(self, request):
        now = timezone.now()
        since_24h = now - timezone.timedelta(hours=24)
        since_5m = now - timezone.timedelta(minutes=5)
        vehicles_scanned = Sighting.objects.filter(timestamp__gte=since_24h).count()
        alerts_triggered = Alert.objects.filter(timestamp__gte=since_24h).count()
        total_vehicles_online = Sighting.objects.filter(timestamp__gte=since_5m).values('plate_number').distinct().count()
        return Response({
            'vehicles_scanned_24h': vehicles_scanned,
            'alerts_triggered_24h': alerts_triggered,
            'total_vehicles_online': total_vehicles_online,
        })


class DatasetView(APIView):
    """Unified dataset endpoint returning vehicles, recent sightings, and alerts in one payload.

    Query params:
    - minutesSightings: int (default 60)
    - minutesAlerts: int (default 120)
    - limitSightings: int (default 500)
    - limitAlerts: int (default 200)
    """

    @transaction.non_atomic_requests
    def get(self, request):
        minutes_sightings = int(request.query_params.get('minutesSightings', '60'))
        minutes_alerts = int(request.query_params.get('minutesAlerts', '120'))
        limit_sightings = int(request.query_params.get('limitSightings', '500'))
        limit_alerts = int(request.query_params.get('limitAlerts', '200'))

        now = timezone.now()
        since_s = now - timezone.timedelta(minutes=minutes_sightings)
        since_a = now - timezone.timedelta(minutes=minutes_alerts)

        vehicles_qs = Vehicle.objects.all().order_by('plate_number')
        sightings_qs = Sighting.objects.filter(timestamp__gte=since_s).order_by('-timestamp')[:limit_sightings]
        alerts_qs = Alert.objects.filter(timestamp__gte=since_a).order_by('-timestamp')[:limit_alerts]

        vehicles = VehicleSerializer(vehicles_qs, many=True).data
        sightings = SightingSerializer(sightings_qs, many=True).data
        alerts = AlertSerializer(alerts_qs, many=True).data

        resp = {
            'vehicles': vehicles,
            'sightings': sightings,
            'alerts': alerts,
            'source': 'api',
        }
        try:
            logger.info(
                "DatasetView.get: minutesSightings=%s minutesAlerts=%s limits=(%s,%s) counts=(%s,%s,%s)",
                minutes_sightings, minutes_alerts, limit_sightings, limit_alerts,
                len(vehicles), len(sightings), len(alerts)
            )
        except Exception:
            pass
        return Response(resp)


class VerificationView(APIView):
    """Verify incoming vehicle data against police records."""
    def post(self, request):
        ser = VerificationRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'detail': 'Invalid payload', 'errors': ser.errors}, status=status.HTTP_400_BAD_REQUEST)
        result = verify_vehicle(ser.validated_data)
        out = VerificationResponseSerializer(data=result)
        out.is_valid(raise_exception=True)
        return Response(out.data)
