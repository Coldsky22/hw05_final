from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import get_paginator_helper, paginator
from django.views.decorators.cache import cache_page

SYMBOLS_QUANTITY: int = 30


@cache_page(20, key_prefix='index_page')
def index(request):
    paginator_obj = get_paginator_helper(request)
    context = {
        'title': 'Последние обновления на сайте',
        'page_obj': paginator_obj['page_obj']
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    paginator_obj = get_paginator_helper(request, filter_name='group',
                                         filter_value=group)
    title = group.title
    text = group.description
    context = {
        'text': text,
        'title': title,
        'page_obj': paginator_obj['page_obj'],
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    paginator_obj = get_paginator_helper(request, filter_name='author',
                                         filter_value=author)
    following = True
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists

    context = {
        'title': f'Профайл пользователя {author.get_full_name()}',
        'author': author,
        'page_obj': paginator_obj['page_obj'],
        'post_total': paginator_obj['count_post'],
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    comments = post.comments.all()
    post_list = Post.objects.filter(author=author)
    count_posts = post_list.count()
    title = f"Пост {post.text[:SYMBOLS_QUANTITY]}"
    context = {
        "title": title,
        'form': CommentForm(),
        'comments': comments,
        "post": post,
        "count_posts": count_posts,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("posts:profile", request.user)


@login_required
def post_edit(request, post_id):
    post_edit_flag = True
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'GET':
        if request.user != post.author:
            return redirect('posts:profile', request.user)
        form = PostForm(instance=post)

    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            form.save()
        return redirect('posts:post_detail', post.id)

    return render(request, 'posts/create_post.html', {
        'form': form,
        'post': post,
        'post_edit_flag': post_edit_flag
    })


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user).all()
    page_obj = paginator(request=request, post_list=post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=username)
    if Follow.objects.filter(author=author, user=request.user).exists():
        return redirect('posts:profile', username=username)
    Follow.objects.create(
        user=request.user,
        author=author
    )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(author=author, user=request.user)
    follow.delete()
    return redirect('posts:profile', username=username)
