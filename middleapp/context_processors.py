from middleapp.models import *


def background_context_processor(request):
    org = Organization.objects.all().first()
    background_url = org.background.url if (org and org.background) else ''

    return {'bg_url': background_url}
