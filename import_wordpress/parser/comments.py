from datetime import datetime

from django.conf import settings

namespaces = settings.NAMESPACES


def get_comments(item_tag):
    comments = []
    comment_tags = item_tag.findall("wp:comment", namespaces)

    for comment_tag in comment_tags:
        comment_id = comment_tag.find("wp:comment_id", namespaces).text
        author_email = comment_tag.find("wp:comment_author_email", namespaces).text
        comment_date = datetime.strptime(
            comment_tag.find("wp:comment_date", namespaces).text,
            "%Y-%m-%d %H:%M:%S",
        )
        content = comment_tag.find("wp:comment_content", namespaces).text
        parent_id = comment_tag.find("wp:comment_parent", namespaces).text
        comments.append(
            {
                "comment_id": comment_id,
                "author_email": author_email,
                "comment_date": comment_date,
                "content": content,
                "parent_id": parent_id,
                "legacy_id": comment_id,
            }
        )

    return comments
