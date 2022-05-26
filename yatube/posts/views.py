from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from posts.models import Post, Group, User, Follow
from posts.forms import CommentForm, PostForm
from django.contrib.auth.decorators import login_required


depth = 10


def index(request):
    # Одна строка вместо тысячи слов на SQL:
    # в переменную posts будет сохранена выборка из 10 объектов модели Post,
    # отсортированных по полю pub_date по убыванию (от больших
    # значений к меньшим)
    post_list = Post.objects.all().order_by('-pub_date')
    paginator = Paginator(post_list, depth)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by('-pub_date')
    paginator = Paginator(post_list, depth)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    # Здесь код запроса к модели и создание словаря контекста
    r = request.user
    author_name = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author_name).order_by('-pub_date')
    paginator = Paginator(posts, depth)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    user_posts_q = Post.objects.filter(author=author_name).count()
    list1 = Follow.objects.all()
    if Follow.objects.filter(author=author_name).exists():
        following = True
    else:
        following = False
    context = {
        'posts': posts,
        'user_posts_q': user_posts_q,
        'page_obj': page_obj,
        'author_name': author_name,
        'following': following,
        'list1': list1,
        'r': r,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    # Здесь код запроса к модели и создание словаря контекста
    post = get_object_or_404(Post, id=post_id)
    author1 = post.author
    user_posts_q = Post.objects.filter(author=author1).count()
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'user_posts_q': user_posts_q,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST, files=request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(id=post_id)
    form = PostForm(request.POST, files=request.FILES or None, instance=post)
    if post.author == request.user:
        is_edit = True
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
        context = {
            'form': form,
            'is_edit': is_edit
        }
        return render(request, 'posts/create_post.html', context)
    else:
        return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    post_list = Post.objects.all().order_by('-pub_date')
    new_post_list = []
    follow_list = ['авторы']
    user_list = ['юзер']
    followings = Follow.objects.all()
    for follow in (followings):
        y = follow.author
        x = follow.user
        user_list.append(x)
        follow_list.append(y)
        new_post_list += post_list.filter(author=y)
    paginator = Paginator(new_post_list, depth)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'follow_list': follow_list,
        'user_list': user_list,

    }
    return render(request, 'posts/follow.html', context)
