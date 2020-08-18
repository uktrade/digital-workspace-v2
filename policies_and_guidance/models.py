from wagtail.core.models import Page

from working_at_dit.models import PageWithTopics


class PoliciesAndGuidanceHome(Page):
    subpage_types = ["policies_and_guidance.PoliciesHome", "policies_and_guidance.GuidanceHome", ]
    # model just for use in editor hierarchy


class PoliciesHome(Page):
    subpage_types = ["policies_and_guidance.Policy", ]
    # model just for use in editor hierarchy


class GuidanceHome(Page):
    subpage_types = ["policies_and_guidance.Guidance", ]
    # model just for use in editor hierarchy


class Guidance(PageWithTopics):
    is_creatable = True

    subpage_types = ["policies_and_guidance.Guidance"]


class Policy(PageWithTopics):
    is_creatable = True

    subpage_types = ["policies_and_guidance.Policy"]
