# Feedback viewer

!!! warning "This is a proposed group"
    This group is not yet available in the application and this document is a proposal for its definition and purpose.

Users in this group should be able to view all feedback submitted through the feedback forms on the website.

Users in this group get the following permissions:

## Object permissions

- `django_feedback_govuk.view_feedback_submission`: Can view **ALL** feedback submissions

Optionally, we can create groups per feedback type by using their specific permissions:

- `feedback.view_hrfeedback`: Can view feedback associated with the `feedback.HRFeedback` model
- `feedback.view_searchfeedbackv1`: Can view feedback associated with the `feedback.SearchFeedbackV1` model
- `feedback.view_searchfeedbackv2`: Can view feedback associated with the `feedback.SearchFeedbackV2` model
