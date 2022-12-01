from .models import Post
from django.core.paginator import Paginator
POST_PER_PAGE = 10


def paginator(request, post_list):
    paginator = Paginator(post_list, POST_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def get_paginator_helper(request, filter_name='', filter_value=None):
    if filter_name == 'author':
        post_list = Post.objects.filter(author=filter_value)
    elif filter_name == 'group':
        post_list = Post.objects.filter(group=filter_value)
    else:
        post_list = Post.objects.all()
    paginator = Paginator(post_list, POST_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return {
        'page_obj': page_obj,
        'count_post': post_list.count()
    }
