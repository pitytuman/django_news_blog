from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.views import login_required
from django.shortcuts import render, HttpResponse, redirect
from django.views.generic import UpdateView, DeleteView, ListView
from django.utils.datetime_safe import datetime

from .models import Category, Article, Comment, ArticleCountViews
from .forms import LoginForm, RegistrationForm, ArticleForm, CommentForm, CustomUserChangeForm


# Отображение главной страницы с помощью класса
class HomePageView(ListView):
    model = Article
    template_name = 'web_site/index.html'
    context_object_name = 'articles'


class SearchResult(HomePageView):
    def get_queryset(self):
        query = self.request.GET.get('q')
        return Article.objects.filter(
            Q(title__iregex=query) | Q(content__iregex=query)
        )


# def home_page(request):
#     articles = Article.objects.all()
#     context = {
#         'articles': articles
#     }
#     return render(request, 'web_site/index.html', context)


def category_articles(request, category_id):
    category = Category.objects.filter(pk=category_id).first()
    articles = Article.objects.filter(category=category)
    context = {
        'articles': articles,
        'category': category
    }
    return render(request, 'web_site/index.html', context)


def article_detail(request, article_id):
    article = Article.objects.filter(pk=article_id).first()

    if not request.session.session_key:
        request.session.save()

    session_id = request.session.session_key

    views = ArticleCountViews()
    views.article = article

    if not request.user.is_authenticated:
        views_items = ArticleCountViews.objects.filter(session_id=session_id, article=article)
        if not views_items.count() and str(session_id) != 'None':
            views.session_id = session_id

    else:
        views_items = ArticleCountViews.objects.filter(article=article, user=request.user)
        if not views_items.count():
            views.user = request.user

    if views.session_id or views.user:
        views.save()
        article.views += 1
        article.save()


    if request.method == "POST":
        form = CommentForm(data=request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.article = article
            form.author = request.user
            form.save()
            return redirect('article_detail', article.pk)
    else:
        form = CommentForm()

    comments = Comment.objects.filter(article=article)

    context = {
        'article': article,
        'title': article.title,
        'form': form,
        'comments': comments
    }
    return render(request, 'web_site/article_detail.html', context)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            print(username, password)
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')

    else:
        form = LoginForm()

    context = {
        'form': form
    }

    return render(request, 'web_site/login.html', context)


def registration_view(request):
    if request.method == 'POST':
        print(request.POST)
        form = RegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()

    context = {
        'form': form
    }
    return render(request, 'web_site/registration.html', context)


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login')
def create_article(request):
    if request.method == 'POST':
        form = ArticleForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            form = form.save(commit=False)
            form.author = request.user
            form.save()
            return redirect('article_detail', form.pk)
    else:
        form = ArticleForm()
    context = {
        'form': form
    }
    return render(request, 'web_site/article_form.html', context)


@login_required(login_url='login')
def author_articles_view(request, username):
    author = User.objects.get(username=username)
    articles = Article.objects.filter(author=author)

    total_views = sum([article.views for article in articles])
    total_comments = sum([article.comment_set.all().count() for article in articles])
    days_left = datetime.now().date() - author.date_joined.date()

    context = {
        'articles': articles,
        'total_views': total_views,
        'total_comments': total_comments,
        'total_posts': articles.count(),
        'days_left': days_left.days
    }
    return render(request, 'web_site/my_articles.html',context)


class UpdateArticle(UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'web_site/article_form.html'

class DeleteArticle(DeleteView):
    model = Article
    success_url = '/'
    template_name = 'web_site/article_confirm_delete.html'


class ChangeUserData(UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'web_site/profile.html'
    success_url = 'home'

def user_profile(request, username):
    return render(request, 'web_site/profile.html')


def delete_comment(request, comment_id):
    comment = Comment.objects.get(pk=comment_id)
    comment.delete()
    article_id = comment.article.pk
    return redirect('article_detail', article_id)


class UpdateComment(UpdateView):
    model = Comment
    template_name = 'web_site/article_detail.html'
    form_class = CommentForm

    def form_valid(self, form):
        obj = self.get_object()
        article = Article.objects.get(pk=obj.article.pk)
        form.save()
        return redirect('article_detail', article.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        article = Article.objects.get(pk=obj.article.pk)
        comments = Comment.objects.filter(article=article)
        context['article'] = article
        context['comments'] = comments
        return context
