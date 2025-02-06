from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from blog.models import Category, Comment, Post

from .constants import POSTS_PER_PAGE
from .forms import CommentForm, PostForm


def get_post_or_404(post_id):
    return get_object_or_404(
        Post.objects.select_related('author', 'category'),
        id=post_id
    )


def paginate_queryset(queryset, request):
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


class OnlyAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return (
            object.author == self.request.user
            or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.get_object().id)


def index(request):
    post_list = Post.objects.available()
    page_obj = paginate_queryset(post_list, request)
    for post in page_obj.object_list:
        post.comment_count = post.comments.count()

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_post_or_404(post_id)
    if not post.is_published and post.author != request.user:
        raise Http404
    comments = post.comments.all()
    form = CommentForm()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )
    post_list = category.posts.available()
    page_obj = paginate_queryset(post_list, request)
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)


class UserProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'posts'
    paginate_by = POSTS_PER_PAGE

    def get_user(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        user = self.get_user()
        return (
            user.posts.with_comment_count()
            .select_related('author', 'category')
            .order_by('-pub_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_user()
        return context


class UserProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'username', 'email']

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostEditView(
    LoginRequiredMixin,
    OnlyAuthorMixin,
    UpdateView
):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(
    LoginRequiredMixin,
    OnlyAuthorMixin,
    DeleteView
):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


@login_required
def add_comment(request, post_id):
    post = get_post_or_404(post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(
        request,
        'blog/comment.html',
        {'form': form, 'comment': comment}
    )


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(
        request,
        'blog/comment.html',
        {'comment': comment}
    )
