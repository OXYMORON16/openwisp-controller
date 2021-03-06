from django.db.models import Q
from django_netjsonconfig.controller.generics import (BaseDeviceChecksumView, BaseDeviceDownloadConfigView,
                                                      BaseDeviceRegisterView, BaseDeviceReportStatusView,
                                                      BaseVpnChecksumView, BaseVpnDownloadConfigView)
from django_netjsonconfig.utils import invalid_response

from ..models import Device, OrganizationConfigSettings, Vpn


class ActiveOrgMixin(object):
    """
    adds check to organization.is_active to ``get_object`` method
    """
    def get_object(self, *args, **kwargs):
        kwargs['organization__is_active'] = True
        return super(ActiveOrgMixin, self).get_object(*args, **kwargs)


class DeviceChecksumView(ActiveOrgMixin, BaseDeviceChecksumView):
    model = Device


class DeviceDownloadConfigView(ActiveOrgMixin, BaseDeviceDownloadConfigView):
    model = Device


class DeviceReportStatusView(ActiveOrgMixin, BaseDeviceReportStatusView):
    model = Device


class DeviceRegisterView(BaseDeviceRegisterView):
    model = Device

    def forbidden(self, request):
        """
        ensures request is authorized:
            - secret matches an organization's shared_secret
            - the organization has registration_enabled set to True
        """
        try:
            secret = request.POST.get('secret')
            org_settings = OrganizationConfigSettings.objects \
                                                     .select_related('organization') \
                                                     .get(shared_secret=secret,
                                                          organization__is_active=True)
        except OrganizationConfigSettings.DoesNotExist:
            return invalid_response(request, 'error: unrecognized secret', status=403)
        if not org_settings.registration_enabled:
            return invalid_response(request, 'error: registration disabled', status=403)
        # set an organization attribute as a side effect
        # this attribute will be used in ``init_object``
        self.organization = org_settings.organization

    def init_object(self, **kwargs):
        config = super(DeviceRegisterView, self).init_object(**kwargs)
        config.organization = self.organization
        config.device.organization = self.organization
        return config

    def get_template_queryset(self, config):
        queryset = super(DeviceRegisterView, self).get_template_queryset(config)
        # filter templates of the same organization or shared templates
        return queryset.filter(Q(organization=self.organization) |
                               Q(organization=None))


class VpnChecksumView(BaseVpnChecksumView):
    model = Vpn


class VpnDownloadConfigView(BaseVpnDownloadConfigView):
    model = Vpn


device_checksum = DeviceChecksumView.as_view()
device_download_config = DeviceDownloadConfigView.as_view()
device_report_status = DeviceReportStatusView.as_view()
device_register = DeviceRegisterView.as_view()
vpn_checksum = VpnChecksumView.as_view()
vpn_download_config = VpnDownloadConfigView.as_view()
