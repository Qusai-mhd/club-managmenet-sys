from django.contrib.auth import get_user_model


def customer_applications_context_processor(request):
    customer_applications_count = get_user_model().objects.filter(confirmed=False).count()
    return {'applications_count': customer_applications_count}
