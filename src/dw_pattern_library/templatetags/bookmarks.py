from pattern_library.monkey_utils import override_tag

from interactions.templatetags.bookmarks import register


override_tag(register, name="bookmark_list")
