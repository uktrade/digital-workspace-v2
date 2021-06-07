

def set_last_viewed_cookie(request, response):
    if not request.COOKIES.get("seen_cookie_banner"):
        response.set_cookie(
            "seen_cookie_banner",
            1,
            secure=False,
        )

    response.set_cookie(
        "last_viewed",
        request.build_absolute_uri(),
        secure=True,
    )
