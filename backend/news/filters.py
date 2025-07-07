import django_filters
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Article, Category, Tag, Author, Newsletter, NewsletterCampaign

class ArticleFilter(django_filters.FilterSet):
    # Date filters
    published_after = django_filters.DateTimeFilter(
        field_name='published_at', 
        lookup_expr='gte',
        help_text="Filter articles published after this date"
    )
    published_before = django_filters.DateTimeFilter(
        field_name='published_at', 
        lookup_expr='lte',
        help_text="Filter articles published before this date"
    )
    created_after = django_filters.DateTimeFilter(
        field_name='created_at', 
        lookup_expr='gte',
        help_text="Filter articles created after this date"
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at', 
        lookup_expr='lte',
        help_text="Filter articles created before this date"
    )
    
    # Category filters
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        help_text="Filter by category ID"
    )
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        help_text="Filter by category slug"
    )
    category_name = django_filters.CharFilter(
        field_name='category__name',
        lookup_expr='icontains',
        help_text="Filter by category name (case-insensitive)"
    )
    
    # Tag filters
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        help_text="Filter by tag IDs (multiple allowed)"
    )
    tag_slugs = django_filters.CharFilter(
        method='filter_by_tag_slugs',
        help_text="Filter by tag slugs (comma-separated)"
    )
    has_tags = django_filters.BooleanFilter(
        method='filter_has_tags',
        help_text="Filter articles that have tags"
    )
    
    # Author filters
    author = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        help_text="Filter by author ID"
    )
    author_username = django_filters.CharFilter(
        field_name='author__username',
        lookup_expr='icontains',
        help_text="Filter by author username"
    )
    verified_authors = django_filters.BooleanFilter(
        field_name='author__author_profile__is_verified',
        help_text="Filter by verified authors"
    )
    staff_writers = django_filters.BooleanFilter(
        field_name='author__author_profile__is_staff_writer',
        help_text="Filter by staff writers"
    )
    
    # Status and feature filters
    is_featured = django_filters.BooleanFilter(
        help_text="Filter featured articles"
    )
    is_breaking = django_filters.BooleanFilter(
        help_text="Filter breaking news"
    )
    is_trending = django_filters.BooleanFilter(
        help_text="Filter trending articles"
    )
    allow_comments = django_filters.BooleanFilter(
        help_text="Filter articles that allow comments"
    )
    
    # Numeric range filters
    views_min = django_filters.NumberFilter(
        field_name='views_count',
        lookup_expr='gte',
        help_text="Minimum view count"
    )
    views_max = django_filters.NumberFilter(
        field_name='views_count',
        lookup_expr='lte',
        help_text="Maximum view count"
    )
    read_time_min = django_filters.NumberFilter(
        field_name='read_time',
        lookup_expr='gte',
        help_text="Minimum read time in minutes"
    )
    read_time_max = django_filters.NumberFilter(
        field_name='read_time',
        lookup_expr='lte',
        help_text="Maximum read time in minutes"
    )
    
    # Text search
    title_contains = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        help_text="Search in article titles"
    )
    content_contains = django_filters.CharFilter(
        field_name='content',
        lookup_expr='icontains',
        help_text="Search in article content"
    )
    
    # Location filter
    location = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text="Filter by location"
    )
    
    class Meta:
        model = Article
        fields = [
            'status', 'priority', 'is_featured', 'is_breaking', 
            'is_trending', 'allow_comments', 'category', 'tags'
        ]
    
    def filter_by_tag_slugs(self, queryset, name, value):
        """Filter by comma-separated tag slugs"""
        if value:
            tag_slugs = [slug.strip() for slug in value.split(',')]
            return queryset.filter(tags__slug__in=tag_slugs).distinct()
        return queryset
    
    def filter_has_tags(self, queryset, name, value):
        """Filter articles that have or don't have tags"""
        if value:
            return queryset.filter(tags__isnull=False).distinct()
        else:
            return queryset.filter(tags__isnull=True)

class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    has_articles = django_filters.BooleanFilter(method='filter_has_articles')
    
    class Meta:
        model = Category
        fields = ['is_active']
    
    def filter_has_articles(self, queryset, name, value):
        if value:
            return queryset.filter(articles__isnull=False).distinct()
        else:
            return queryset.filter(articles__isnull=True)

class TagFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    has_articles = django_filters.BooleanFilter(method='filter_has_articles')
    
    class Meta:
        model = Tag
        fields = ['name']
    
    def filter_has_articles(self, queryset, name, value):
        if value:
            return queryset.filter(articles__isnull=False).distinct()
        else:
            return queryset.filter(articles__isnull=True)

class AuthorFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    is_verified = django_filters.BooleanFilter()
    is_staff_writer = django_filters.BooleanFilter()
    has_articles = django_filters.BooleanFilter(method='filter_has_articles')
    
    class Meta:
        model = Author
        fields = ['is_verified', 'is_staff_writer']
    
    def filter_has_articles(self, queryset, name, value):
        if value:
            return queryset.filter(user__articles__isnull=False).distinct()
        else:
            return queryset.filter(user__articles__isnull=True)

class NewsletterFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    is_confirmed = django_filters.BooleanFilter(method='filter_is_confirmed')
    categories = django_filters.ModelMultipleChoiceFilter(queryset=Category.objects.all())
    
    class Meta:
        model = Newsletter
        fields = ['is_active']
    
    def filter_is_confirmed(self, queryset, name, value):
        if value:
            return queryset.filter(confirmed_at__isnull=False)
        else:
            return queryset.filter(confirmed_at__isnull=True)