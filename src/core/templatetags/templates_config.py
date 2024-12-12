FEEDBACK = "feedback"

TEMPLATES = {
    FEEDBACK: {
        "title": "Give feedback",
        "description": "Did you find what you were looking for?",
        "template_name": "dwds/components/feedback.html",
    },
}

TEMPLATE_SECTIONS = [
    {"page_type": "primary_page", "actions": []},
    {
        "page_type": "secondary_page",
        "actions": [
            {
                "action_type": FEEDBACK,
                "is_visible": lambda context: is_visible(context, FEEDBACK),
                "render": lambda: render_template(FEEDBACK),
            },
        ],
    },
]


def is_visible(context, action_type):
    if action_type == FEEDBACK:
        return context.get("USER_IS_AUTHENTICATED", False)
    return False


def render_template(action_type):
    return TEMPLATES.get(action_type, {})
