# CloudFront WAF

## Overview

This project is hosted behind a CloudFront Web Application Firewall (WAF).


## File uploads

This firewall causes some issues with users who are uploading files, this means that we need to bypass the WAF on any URLs that are used for file uploads.

Below is a list of all the known URLs that should be bypassed:

- `/django-admin/*` 
- `/admin/pages/{PAGE_ID}/edit/` where `{PAGE_ID}` is an integer
- `/admin/pages/add/*`
- `/admin/media/audio/add/`
- `/admin/media/audio/chooser/upload/`
- `/admin/media/audio/chooser/create/`
- `/admin/media/audio/multiple/add/`
- `/admin/media/edit/{MEDIA_ID}/` where `{MEDIA_ID}` is an integer
- `/admin/media/video/add/`
- `/admin/media/video/chooser/upload/`
- `/admin/media/video/chooser/create/`
- `/admin/media/video/multiple/add/`
- `/admin/documents/edit/{DOCUMENT_ID}/` where `{DOCUMENT_ID}` is an integer
- `/admin/documents/multiple/add/`
- `/admin/documents/chooser/upload/`
- `/admin/documents/chooser/create/`
- `/admin/images/edit/{IMAGE_ID}/` where `{IMAGE_ID}` is an integer
- `/admin/images/multiple/add/`
- `/admin/images/chooser/upload/`
- `/admin/images/chooser/create/`
- `/people/{PERSON_UUID}/edit/personal/` where `{PERSON_UUID}` is a UUID string

This has been implemented by adding a custom WAF rule to the CloudFront distribution. This rule is a regular expression that matches the URLs above and bypasses the WAF for them.
