from news.models import Comment, NewsPage


def get_comments(news_page: NewsPage):
    return Comment.objects.filter(
        news_page=news_page,
        parent_id=None,
    ).order_by("-posted_date")


def get_comment_count(news_page: NewsPage):
    return Comment.objects.filter(
        news_page=news_page,
    ).count()