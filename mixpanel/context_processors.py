from django.conf import settings


def api_key(request):
    return {'MIXPANEL_API_TOKEN': settings.MIXPANEL_API_TOKEN}
