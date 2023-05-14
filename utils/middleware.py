from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware


class MySessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        super(MySessionMiddleware, self).process_request(request)
        # request.session.set_expiry(  todo commento la scadenza della sessione
        #     int(
        #         timedelta(
        #             minutes=int(settings.SESSION_MINUTE_EXPIRATION)
        #         ).total_seconds()
        #     )
        # )

    def process_response(self, request, response):
        return super(MySessionMiddleware, self).process_response(
            request, response
        )
