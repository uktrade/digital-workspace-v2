def set_seen_cookie_banner(request, response):
    if not request.COOKIES.get("seen_cookie_banner"):
        response.set_cookie(
            "seen_cookie_banner",
            1,
            secure=False,
        )
