from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from care.facility.api.serializers.prescription import PrescriptionSerializer, MedicineAdministrationSerializer
from care.facility.models import Prescription, MedicineAdministration, PrescriptionType, generate_choices
from care.utils.filters import CareChoiceFilter
from care.utils.queryset.consultation import get_consultation_queryset


def inverse_choices(choices):
    output = {}
    for choice in choices:
        output[choice[1]] = choice[0]
    return output


inverse_prescription_type = inverse_choices(generate_choices(PrescriptionType))


class MedicineAdminstrationFilter(filters.FilterSet):
    prescription = filters.UUIDFilter(field_name="prescription__external_id")


class MedicineAdministrationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = MedicineAdministrationSerializer
    permission_classes = (
        IsAuthenticated,
    )
    queryset = MedicineAdministration.objects.all().order_by("-created_date")
    lookup_field = "external_id"
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MedicineAdminstrationFilter

    def get_consultation_obj(self):
        return get_object_or_404(
            get_consultation_queryset(self.request.user).filter(external_id=self.kwargs["consultation_external_id"]))

    def get_queryset(self):
        consultation_obj = self.get_consultation_obj()
        return self.queryset.filter(
            prescription__consultation_id=consultation_obj.id
        )


class ConsultationPrescriptionFilter(filters.FilterSet):
    is_prn = filters.BooleanFilter()
    prescription_type = CareChoiceFilter(choice_dict=inverse_prescription_type)


class ConsultationPrescriptionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = PrescriptionSerializer
    permission_classes = (
        IsAuthenticated,
    )
    queryset = Prescription.objects.all().order_by("-created_date")
    lookup_field = "external_id"
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ConsultationPrescriptionFilter

    def get_consultation_obj(self):
        return get_object_or_404(
            get_consultation_queryset(self.request.user).filter(external_id=self.kwargs["consultation_external_id"]))

    def get_queryset(self):
        consultation_obj = self.get_consultation_obj()
        return self.queryset.filter(
            consultation_id=consultation_obj.id
        )

    def perform_create(self, serializer):
        consultation_obj = self.get_consultation_obj()
        serializer.save(prescribed_by=self.request.user, consultation=consultation_obj)

    @action(methods=["POST"], detail=True)
    def discontinue(self, request, *args, **kwargs):
        prescription_obj = self.get_object()
        prescription_obj.discontinued = True
        prescription_obj.discontinued_reason = request.data.get("discontinued_reason", None)
        prescription_obj.save()
        return Response({}, status=status.HTTP_201_CREATED)

    @action(methods=["POST"], detail=True, serializer_class=MedicineAdministrationSerializer)
    def administer(self, request, *args, **kwargs):
        prescription_obj = self.get_object()
        serializer = MedicineAdministrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(prescription=prescription_obj, administered_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # @action(methods=["GET"], detail=True)
    # def get_administrations(self, request, *args, **kwargs):
    #     prescription_obj = self.get_object()
    #     serializer = MedicineAdministrationSerializer(
    #         MedicineAdministration.objects.filter(prescription_id=prescription_obj.id),
    #         many=True)
    #     return Response(serializer.data)

    # @action(methods=["DELETE"], detail=True)
    # def delete_administered(self, request, *args, **kwargs):
    #     if not request.query_params.get("id", None):
    #         return Response({"success": False, "error": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
    #     administered_obj = MedicineAdministration.objects.get(external_id=request.query_params.get("id", None))
    #     administered_obj.delete()
    #     return Response({"success": True}, status=status.HTTP_200_OK)
