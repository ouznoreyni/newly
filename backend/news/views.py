from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Prefetch, Avg, Sum
from django.contrib.auth.models import User
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse,
    OpenApiExample
)
from drf_spectacular.types import OpenApiTypes

from .models import (
    Category, Tag, Author, Article, ArticleView, 
    Newsletter, NewsletterCampaign
)
from .serializers import (
    CategoryListSerializer, CategoryDetailSerializer, CategoryCreateUpdateSerializer,
    TagListSerializer, TagDetailSerializer, TagCreateUpdateSerializer,
    AuthorListSerializer, AuthorDetailSerializer, AuthorCreateUpdateSerializer,
    ArticleListSerializer, ArticleDetailSerializer, ArticleCreateSerializer,
    ArticleUpdateSerializer, ArticleNestedSerializer,
    NewsletterListSerializer, NewsletterSerializer, 
    NewsletterCreateSerializer, NewsletterUpdateSerializer,
    NewsletterCampaignListSerializer, NewsletterCampaignSerializer,
    NewsletterCampaignCreateUpdateSerializer,
    ArticleStatsSerializer, CategoryStatsSerializer, AuthorStatsSerializer
)
from .filters import (
    ArticleFilter, CategoryFilter, TagFilter, AuthorFilter, NewsletterFilter
)
from .permissions import (
    IsAuthorOrReadOnly, IsOwnerOrReadOnly, IsStaffOrReadOnly,
    IsAuthorProfileOwner, IsNewsletterOwner
)

# =============================================================================
# CATEGORY VIEWS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List all categories",
        description="Get a list of all active categories with article counts",
        responses={200: CategoryListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                description='Filter by active status'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in category names and descriptions'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                description='Order by: name, order, created_at, article_count'
            ),
        ]
    ),
    create=extend_schema(
        summary="Create a new category",
        description="Create a new category (staff only)",
        request=CategoryCreateUpdateSerializer,
        responses={201: CategoryDetailSerializer}
    ),
    retrieve=extend_schema(
        summary="Get category details",
        description="Get detailed information about a category including recent articles",
        responses={200: CategoryDetailSerializer}
    ),
    update=extend_schema(
        summary="Update category",
        description="Update category information (staff only)",
        request=CategoryCreateUpdateSerializer,
        responses={200: CategoryDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Delete category",
        description="Delete a category (staff only)",
        responses={204: None}
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'order', 'created_at', 'article_count']
    ordering = ['order', 'name']
    
    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('articles', queryset=Article.objects.filter(status='published'))
            )
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action == 'retrieve':
            return CategoryDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        return CategoryListSerializer
    
    @extend_schema(
        summary="Get category statistics",
        description="Get statistics for all categories",
        responses={200: CategoryStatsSerializer}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get category statistics"""
        total_categories = Category.objects.count()
        active_categories = Category.objects.filter(is_active=True).count()
        most_popular = Category.objects.annotate(
            article_count=Count('articles', filter=Q(articles__status='published'))
        ).order_by('-article_count').first()
        
        stats = {
            'total_categories': total_categories,
            'active_categories': active_categories,
            'most_popular_category': most_popular.name if most_popular else 'None'
        }
        
        serializer = CategoryStatsSerializer(stats)
        return Response(serializer.data)

@extend_schema_view(
    list=extend_schema(
        summary="List articles in category",
        description="Get all published articles in a specific category",
        responses={200: ArticleListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='category_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Category ID'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in article titles, content, and excerpt'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                description='Order by: published_at, created_at, views_count, title'
            ),
        ]
    )
)
class CategoryArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Nested viewset for articles within a category"""
    serializer_class = ArticleListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ArticleFilter
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['published_at', 'created_at', 'views_count', 'title']
    ordering = ['-published_at']
    
    def get_queryset(self):
        category_pk = self.kwargs['category_pk']
        return Article.objects.filter(
            category_id=category_pk,
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')

# =============================================================================
# TAG VIEWS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List all tags",
        description="Get a list of all tags with article counts",
        responses={200: TagListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in tag names and descriptions'
            ),
            OpenApiParameter(
                name='has_articles',
                type=OpenApiTypes.BOOL,
                description='Filter tags that have articles'
            ),
        ]
    ),
    create=extend_schema(
        summary="Create a new tag",
        description="Create a new tag (authenticated users)",
        request=TagCreateUpdateSerializer,
        responses={201: TagDetailSerializer}
    ),
    retrieve=extend_schema(
        summary="Get tag details",
        description="Get detailed information about a tag including recent articles",
        responses={200: TagDetailSerializer}
    ),
    update=extend_schema(
        summary="Update tag",
        description="Update tag information (authenticated users)",
        request=TagCreateUpdateSerializer,
        responses={200: TagDetailSerializer}
    )
)
class TagViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TagFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'article_count']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = Tag.objects.all()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('articles', queryset=Article.objects.filter(status='published'))
            )
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TagListSerializer
        elif self.action == 'retrieve':
            return TagDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TagCreateUpdateSerializer
        return TagListSerializer

@extend_schema_view(
    list=extend_schema(
        summary="List articles with tag",
        description="Get all published articles with a specific tag",
        responses={200: ArticleListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='tag_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Tag ID'
            ),
        ]
    )
)
class TagArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Nested viewset for articles within a tag"""
    serializer_class = ArticleListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ArticleFilter
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['published_at', 'created_at', 'views_count', 'title']
    ordering = ['-published_at']
    
    def get_queryset(self):
        tag_pk = self.kwargs['tag_pk']
        return Article.objects.filter(
            tags=tag_pk,
            status='published'
        ).select_related('author', 'category').prefetch_related('tags')

# =============================================================================
# AUTHOR VIEWS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List all authors",
        description="Get a list of all authors with their profiles",
        responses={200: AuthorListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='is_verified',
                type=OpenApiTypes.BOOL,
                description='Filter by verified status'
            ),
            OpenApiParameter(
                name='is_staff_writer',
                type=OpenApiTypes.BOOL,
                description='Filter by staff writer status'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in author names and bio'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Get author details",
        description="Get detailed information about an author including recent articles",
        responses={200: AuthorDetailSerializer}
    ),
    update=extend_schema(
        summary="Update author profile",
        description="Update author profile (owner or staff only)",
        request=AuthorCreateUpdateSerializer,
        responses={200: AuthorDetailSerializer}
    )
)
class AuthorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthorProfileOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuthorFilter
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'bio']
    ordering_fields = ['user__username', 'created_at', 'article_count']
    ordering = ['user__username']
    
    def get_queryset(self):
        queryset = Author.objects.select_related('user')
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('user__articles', queryset=Article.objects.filter(status='published'))
            )
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AuthorListSerializer
        elif self.action == 'retrieve':
            return AuthorDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AuthorCreateUpdateSerializer
        return AuthorListSerializer
    
    @extend_schema(
        summary="Get author statistics",
        description="Get statistics for all authors",
        responses={200: AuthorStatsSerializer}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get author statistics"""
        total_authors = Author.objects.count()
        verified_authors = Author.objects.filter(is_verified=True).count()
        staff_writers = Author.objects.filter(is_staff_writer=True).count()
        most_prolific = Author.objects.annotate(
            article_count=Count('user__articles', filter=Q(user__articles__status='published'))
        ).order_by('-article_count').first()
        
        stats = {
            'total_authors': total_authors,
            'verified_authors': verified_authors,
            'staff_writers': staff_writers,
            'most_prolific_author': str(most_prolific) if most_prolific else 'None'
        }
        
        serializer = AuthorStatsSerializer(stats)
        return Response(serializer.data)

@extend_schema_view(
    list=extend_schema(
        summary="List articles by author",
        description="Get all published articles by a specific author",
        responses={200: ArticleListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='author_pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Author ID'
            ),
        ]
    )
)
class AuthorArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Nested viewset for articles by an author"""
    serializer_class = ArticleListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ArticleFilter
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['published_at', 'created_at', 'views_count', 'title']
    ordering = ['-published_at']
    
    def get_queryset(self):
        author_pk = self.kwargs['author_pk']
        try:
            author = Author.objects.get(pk=author_pk)
            return Article.objects.filter(
                author=author.user,
                status='published'
            ).select_related('author', 'category').prefetch_related('tags')
        except Author.DoesNotExist:
            return Article.objects.none()

# =============================================================================
# ARTICLE VIEWS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List all articles",
        description="Get a paginated list of articles with filtering and search",
        responses={200: ArticleListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                description='Filter by status (draft, review, published, archived)',
                enum=['draft', 'review', 'published', 'archived']
            ),
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.INT,
                description='Filter by category ID'
            ),
            OpenApiParameter(
                name='category_slug',
                type=OpenApiTypes.STR,
                description='Filter by category slug'
            ),
            OpenApiParameter(
                name='tags',
                type=OpenApiTypes.STR,
                description='Filter by tag IDs (comma-separated)'
            ),
            OpenApiParameter(
                name='tag_slugs',
                type=OpenApiTypes.STR,
                description='Filter by tag slugs (comma-separated)'
            ),
            OpenApiParameter(
                name='author_username',
                type=OpenApiTypes.STR,
                description='Filter by author username'
            ),
            OpenApiParameter(
                name='is_featured',
                type=OpenApiTypes.BOOL,
                description='Filter featured articles'
            ),
            OpenApiParameter(
                name='is_breaking',
                type=OpenApiTypes.BOOL,
                description='Filter breaking news'
            ),
            OpenApiParameter(
                name='is_trending',
                type=OpenApiTypes.BOOL,
                description='Filter trending articles'
            ),
            OpenApiParameter(
                name='published_after',
                type=OpenApiTypes.DATETIME,
                description='Filter articles published after this date'
            ),
            OpenApiParameter(
                name='published_before',
                type=OpenApiTypes.DATETIME,
                description='Filter articles published before this date'
            ),
            OpenApiParameter(
                name='views_min',
                type=OpenApiTypes.INT,
                description='Minimum view count'
            ),
            OpenApiParameter(
                name='views_max',
                type=OpenApiTypes.INT,
                description='Maximum view count'
            ),
            OpenApiParameter(
                name='location',
                type=OpenApiTypes.STR,
                description='Filter by location'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in title, content, excerpt, and author username'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                description='Order by: published_at, created_at, views_count, title (prefix with - for descending)'
            ),
        ]
    ),
    create=extend_schema(
        summary="Create a new article",
        description="Create a new article (authenticated users)",
        request=ArticleCreateSerializer,
        responses={201: ArticleDetailSerializer}
    ),
    retrieve=extend_schema(
        summary="Get article details",
        description="Get detailed information about an article (increments view count for published articles)",
        responses={200: ArticleDetailSerializer}
    ),
    update=extend_schema(
        summary="Update article",
        description="Update article (author or staff only)",
        request=ArticleUpdateSerializer,
        responses={200: ArticleDetailSerializer}
    ),
    partial_update=extend_schema(
        summary="Partially update article",
        description="Partially update article (author or staff only)",
        request=ArticleUpdateSerializer,
        responses={200: ArticleDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Delete article",
        description="Delete article (author or staff only)",
        responses={204: None}
    )
)
class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ArticleFilter
    search_fields = ['title', 'content', 'excerpt', 'author__username']
    ordering_fields = ['published_at', 'created_at', 'views_count', 'title']
    ordering = ['-published_at', '-created_at']
    
    def get_queryset(self):
        queryset = Article.objects.select_related('author', 'category').prefetch_related('tags')
        
        # Show only published articles to anonymous users
        if not self.request.user.is_authenticated:
            return queryset.filter(status='published')
        
        # Show all articles to authenticated users, but filter by author for non-staff
        if not self.request.user.is_staff:
            return queryset.filter(
                Q(status='published') | Q(author=self.request.user)
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        elif self.action == 'retrieve':
            return ArticleDetailSerializer
        elif self.action == 'create':
            return ArticleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ArticleUpdateSerializer
        return ArticleDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to track article views"""
        instance = self.get_object()
        
        # Track view if it's a published article
        if instance.status == 'published':
            self.track_article_view(request, instance)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def track_article_view(self, request, article):
        """Track article view for analytics"""
        # Get client IP
        ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip:
            ip = ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # Get or create article view
        view_data = {
            'article': article,
            'ip_address': ip,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referrer': request.META.get('HTTP_REFERER', ''),
            'session_key': request.session.session_key or '',
        }
        
        if request.user.is_authenticated:
            view_data['user'] = request.user
        
        # Only create if not exists (based on session)
        ArticleView.objects.get_or_create(
            article=article,
            session_key=view_data['session_key'],
            defaults=view_data
        )
        
        # Increment article view count
        article.views_count += 1
        article.save(update_fields=['views_count'])
    
    @extend_schema(
        summary="Get featured articles",
        description="Get a list of featured articles",
        responses={200: ArticleListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured articles"""
        articles = self.get_queryset().filter(is_featured=True, status='published')
        page = self.paginate_queryset(articles)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get trending articles",
        description="Get articles trending in the last 7 days based on views",
        responses={200: ArticleListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                description='Number of days to look back (default: 7)'
            ),
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                description='Maximum number of articles to return (default: 10)'
            ),
        ]
    )
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending articles based on recent views"""
        from datetime import timedelta
        
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))
        
        since = timezone.now() - timedelta(days=days)
        articles = self.get_queryset().filter(
            status='published',
            published_at__gte=since
        ).order_by('-views_count')[:limit]
        
        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get breaking news",
        description="Get latest breaking news articles",
        responses={200: ArticleListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                description='Maximum number of articles to return (default: 5)'
            ),
        ]
    )
    @action(detail=False, methods=['get'])
    def breaking(self, request):
        """Get breaking news"""
        limit = int(request.query_params.get('limit', 5))
        articles = self.get_queryset().filter(is_breaking=True, status='published')[:limit]
        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get latest articles",
        description="Get the most recently published articles",
        responses={200: ArticleListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='limit',
                type=OpenApiTypes.INT,
                description='Maximum number of articles to return (default: 20)'
            ),
        ]
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest published articles"""
        limit = int(request.query_params.get('limit', 20))
        articles = self.get_queryset().filter(status='published')[:limit]
        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get article statistics",
        description="Get statistics for all articles",
        responses={200: ArticleStatsSerializer}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get article statistics"""
        total_articles = Article.objects.count()
        published_articles = Article.objects.filter(status='published').count()
        draft_articles = Article.objects.filter(status='draft').count()
        total_views = Article.objects.aggregate(Sum('views_count'))['views_count__sum'] or 0
        total_likes = Article.objects.aggregate(
            total_likes=Count('likes')
        )['total_likes'] or 0
        total_comments = Article.objects.aggregate(
            total_comments=Count('comments', filter=Q(comments__is_approved=True))
        )['total_comments'] or 0
        featured_articles = Article.objects.filter(is_featured=True).count()
        breaking_articles = Article.objects.filter(is_breaking=True).count()
        trending_articles = Article.objects.filter(is_trending=True).count()
        
        stats = {
            'total_articles': total_articles,
            'published_articles': published_articles,
            'draft_articles': draft_articles,
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'featured_articles': featured_articles,
            'breaking_articles': breaking_articles,
            'trending_articles': trending_articles,
        }
        
        serializer = ArticleStatsSerializer(stats)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Increment article views",
        description="Manually increment article view count",
        responses={200: OpenApiResponse(description="View count incremented")}
    )
    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Manually increment article views"""
        article = self.get_object()
        article.views_count += 1
        article.save(update_fields=['views_count'])
        return Response({
            'views_count': article.views_count,
            'message': 'View count incremented successfully'
        })

# =============================================================================
# NEWSLETTER VIEWS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List newsletter subscriptions",
        description="Get a list of newsletter subscriptions (staff only)",
        responses={200: NewsletterListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                description='Filter by active status'
            ),
            OpenApiParameter(
                name='is_confirmed',
                type=OpenApiTypes.BOOL,
                description='Filter by confirmation status'
            ),
            OpenApiParameter(
                name='email',
                type=OpenApiTypes.STR,
                description='Search by email'
            ),
        ]
    ),
    create=extend_schema(
        summary="Subscribe to newsletter",
        description="Subscribe to the newsletter",
        request=NewsletterCreateSerializer,
        responses={201: NewsletterSerializer}
    ),
    retrieve=extend_schema(
        summary="Get newsletter subscription details",
        description="Get details of a newsletter subscription (staff only)",
        responses={200: NewsletterSerializer}
    ),
    update=extend_schema(
        summary="Update newsletter subscription",
        description="Update newsletter subscription preferences (staff only)",
        request=NewsletterUpdateSerializer,
        responses={200: NewsletterSerializer}
    )
)
class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    permission_classes = [IsNewsletterOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NewsletterFilter
    search_fields = ['email', 'name']
    ordering_fields = ['email', 'created_at', 'confirmed_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NewsletterListSerializer
        elif self.action == 'retrieve':
            return NewsletterSerializer
        elif self.action == 'create':
            return NewsletterCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NewsletterUpdateSerializer
        return NewsletterListSerializer
    
    @extend_schema(
        summary="Subscribe to newsletter",
        description="Subscribe to the newsletter (public endpoint)",
        request=NewsletterCreateSerializer,
        responses={
            201: NewsletterSerializer,
            400: OpenApiResponse(description="Validation error")
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[])
    def subscribe(self, request):
        """Subscribe to newsletter (public endpoint)"""
        serializer = NewsletterCreateSerializer(data=request.data)
        if serializer.is_valid():
            newsletter = serializer.save()
            response_serializer = NewsletterSerializer(newsletter, context={'request': request})
            return Response({
                'message': 'Successfully subscribed to newsletter',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Confirm newsletter subscription",
        description="Confirm newsletter subscription using token",
        responses={200: OpenApiResponse(description="Subscription confirmed")}
    )
    @action(detail=True, methods=['post'], permission_classes=[])
    def confirm(self, request, pk=None):
        """Confirm newsletter subscription"""
        newsletter = self.get_object()
        if not newsletter.confirmed_at:
            newsletter.confirmed_at = timezone.now()
            newsletter.save()
            return Response({'message': 'Newsletter subscription confirmed successfully'})
        return Response({'message': 'Newsletter subscription already confirmed'})
    
    @extend_schema(
        summary="Unsubscribe from newsletter",
        description="Unsubscribe from newsletter (public endpoint)",
        responses={200: OpenApiResponse(description="Successfully unsubscribed")}
    )
    @action(detail=True, methods=['post'], permission_classes=[])
    def unsubscribe(self, request, pk=None):
        """Unsubscribe from newsletter"""
        newsletter = self.get_object()
        newsletter.is_active = False
        newsletter.unsubscribed_at = timezone.now()
        newsletter.save()
        return Response({'message': 'Successfully unsubscribed from newsletter'})
    
    @extend_schema(
        summary="Resubscribe to newsletter",
        description="Reactivate newsletter subscription",
        responses={200: OpenApiResponse(description="Successfully resubscribed")}
    )
    @action(detail=True, methods=['post'], permission_classes=[])
    def resubscribe(self, request, pk=None):
        """Resubscribe to newsletter"""
        newsletter = self.get_object()
        newsletter.is_active = True
        newsletter.unsubscribed_at = None
        newsletter.save()
        return Response({'message': 'Successfully resubscribed to newsletter'})

# =============================================================================
# NEWSLETTER CAMPAIGN VIEWS
# =============================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List newsletter campaigns",
        description="Get a list of newsletter campaigns (staff only)",
        responses={200: NewsletterCampaignListSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                description='Filter by campaign status',
                enum=['draft', 'scheduled', 'sent']
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in campaign title and subject'
            ),
        ]
    ),
    create=extend_schema(
        summary="Create newsletter campaign",
        description="Create a new newsletter campaign (staff only)",
        request=NewsletterCampaignCreateUpdateSerializer,
        responses={201: NewsletterCampaignSerializer}
    ),
    retrieve=extend_schema(
        summary="Get campaign details",
        description="Get detailed information about a newsletter campaign (staff only)",
        responses={200: NewsletterCampaignSerializer}
    ),
    update=extend_schema(
        summary="Update newsletter campaign",
        description="Update newsletter campaign (staff only)",
        request=NewsletterCampaignCreateUpdateSerializer,
        responses={200: NewsletterCampaignSerializer}
    )
)
class NewsletterCampaignViewSet(viewsets.ModelViewSet):
    queryset = NewsletterCampaign.objects.all()
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'subject']
    ordering_fields = ['created_at', 'scheduled_at', 'sent_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NewsletterCampaignListSerializer
        elif self.action == 'retrieve':
            return NewsletterCampaignSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return NewsletterCampaignCreateUpdateSerializer
        return NewsletterCampaignListSerializer
    
    @extend_schema(
        summary="Send newsletter campaign",
        description="Send a newsletter campaign to all active subscribers",
        responses={200: OpenApiResponse(description="Campaign sent successfully")}
    )
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send newsletter campaign"""
        campaign = self.get_object()
        
        if campaign.status == 'sent':
            return Response(
                {'error': 'Campaign has already been sent'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active subscribers
        subscribers = Newsletter.objects.filter(
            is_active=True,
            confirmed_at__isnull=False
        )
        
        if not subscribers.exists():
            return Response(
                {'error': 'No active subscribers found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Here you would implement the actual email sending logic
        # For now, just mark as sent
        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.sent_count = subscribers.count()
        campaign.save()
        
        return Response({
            'message': f'Campaign sent successfully to {campaign.sent_count} subscribers',
            'sent_count': campaign.sent_count,
            'sent_at': campaign.sent_at
        })
    
    @extend_schema(
        summary="Preview newsletter campaign",
        description="Get a preview of the newsletter campaign",
        responses={200: OpenApiResponse(description="Campaign preview")}
    )
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Preview newsletter campaign"""
        campaign = self.get_object()
        
        # Generate preview content
        preview_data = {
            'title': campaign.title,
            'subject': campaign.subject,
            'content': campaign.content,
            'articles': ArticleNestedSerializer(
                campaign.articles.all(), 
                many=True, 
                context={'request': request}
            ).data,
            'subscriber_count': Newsletter.objects.filter(
                is_active=True,
                confirmed_at__isnull=False
            ).count()
        }
        
        return Response(preview_data)

# =============================================================================
# ANALYTICS AND DASHBOARD VIEWS
# =============================================================================

@extend_schema(
    summary="Get dashboard analytics",
    description="Get comprehensive analytics for the news platform dashboard",
    responses={200: OpenApiResponse(description="Dashboard analytics data")}
)
class DashboardAnalyticsView(viewsets.ViewSet):
    """Analytics dashboard viewset"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get dashboard overview",
        description="Get overview statistics for the dashboard",
    )
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get dashboard overview statistics"""
        from datetime import timedelta
        
        # Date ranges
        today = timezone.now().date()
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        # Article statistics
        total_articles = Article.objects.count()
        published_articles = Article.objects.filter(status='published').count()
        articles_this_week = Article.objects.filter(
            created_at__date__gte=last_week
        ).count()
        articles_this_month = Article.objects.filter(
            created_at__date__gte=last_month
        ).count()
        
        # View statistics
        total_views = Article.objects.aggregate(
            total=Sum('views_count')
        )['total'] or 0
        
        views_this_week = ArticleView.objects.filter(
            created_at__date__gte=last_week
        ).count()
        
        # Category statistics
        total_categories = Category.objects.filter(is_active=True).count()
        most_popular_category = Category.objects.annotate(
            article_count=Count('articles', filter=Q(articles__status='published'))
        ).order_by('-article_count').first()
        
        # Author statistics
        total_authors = Author.objects.count()
        active_authors = User.objects.filter(
            articles__created_at__date__gte=last_month
        ).distinct().count()
        
        # Newsletter statistics
        total_subscribers = Newsletter.objects.filter(is_active=True).count()
        confirmed_subscribers = Newsletter.objects.filter(
            is_active=True,
            confirmed_at__isnull=False
        ).count()
        
        data = {
            'articles': {
                'total': total_articles,
                'published': published_articles,
                'this_week': articles_this_week,
                'this_month': articles_this_month,
            },
            'views': {
                'total': total_views,
                'this_week': views_this_week,
            },
            'categories': {
                'total': total_categories,
                'most_popular': most_popular_category.name if most_popular_category else None,
            },
            'authors': {
                'total': total_authors,
                'active_this_month': active_authors,
            },
            'newsletter': {
                'total_subscribers': total_subscribers,
                'confirmed_subscribers': confirmed_subscribers,
            }
        }
        
        return Response(data)
    
    @extend_schema(
        summary="Get trending content",
        description="Get trending articles and categories",
    )
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending content"""
        from datetime import timedelta
        
        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        
        # Trending articles
        trending_articles = Article.objects.filter(
            status='published',
            published_at__gte=since
        ).order_by('-views_count')[:10]
        
        # Trending categories
        trending_categories = Category.objects.annotate(
            recent_views=Sum(
                'articles__views_count',
                filter=Q(articles__published_at__gte=since)
            )
        ).filter(recent_views__gt=0).order_by('-recent_views')[:5]
        
        data = {
            'articles': ArticleListSerializer(
                trending_articles, 
                many=True, 
                context={'request': request}
            ).data,
            'categories': CategoryListSerializer(
                trending_categories, 
                many=True, 
                context={'request': request}
            ).data,
        }
        
        return Response(data)
    
    @extend_schema(
        summary="Get content performance",
        description="Get performance metrics for content",
    )
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get content performance metrics"""
        from datetime import timedelta
        
        # Top performing articles by views
        top_by_views = Article.objects.filter(
            status='published'
        ).order_by('-views_count')[:10]
        
        # Top performing articles by engagement (likes + comments)
        top_by_engagement = Article.objects.filter(
            status='published'
        ).annotate(
            engagement_score=Count('likes') + Count('comments')
        ).order_by('-engagement_score')[:10]
        
        # Recent high-performing articles
        last_week = timezone.now() - timedelta(days=7)
        recent_popular = Article.objects.filter(
            status='published',
            published_at__gte=last_week
        ).order_by('-views_count')[:5]
        
        data = {
            'top_by_views': ArticleListSerializer(
                top_by_views, 
                many=True, 
                context={'request': request}
            ).data,
            'top_by_engagement': ArticleListSerializer(
                top_by_engagement, 
                many=True, 
                context={'request': request}
            ).data,
            'recent_popular': ArticleListSerializer(
                recent_popular, 
                many=True, 
                context={'request': request}
            ).data,
        }
        
        return Response(data)

# =============================================================================
# SEARCH VIEWS
# =============================================================================

@extend_schema(
    summary="Global search",
    description="Search across articles, categories, tags, and authors",
    parameters=[
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            description='Search query',
            required=True
        ),
        OpenApiParameter(
            name='type',
            type=OpenApiTypes.STR,
            description='Search type: all, articles, categories, tags, authors',
            enum=['all', 'articles', 'categories', 'tags', 'authors']
        ),
    ]
)
class GlobalSearchView(viewsets.ViewSet):
    """Global search across all content"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Perform global search"""
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')
        
        if not query:
            return Response({
                'error': 'Search query is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = {}
        
        if search_type in ['all', 'articles']:
            articles = Article.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query),
                status='published'
            ).select_related('author', 'category').prefetch_related('tags')[:10]
            
            results['articles'] = ArticleListSerializer(
                articles, 
                many=True, 
                context={'request': request}
            ).data
        
        if search_type in ['all', 'categories']:
            categories = Category.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query),
                is_active=True
            )[:5]
            
            results['categories'] = CategoryListSerializer(
                categories, 
                many=True, 
                context={'request': request}
            ).data
        
        if search_type in ['all', 'tags']:
            tags = Tag.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )[:5]
            
            results['tags'] = TagListSerializer(
                tags, 
                many=True, 
                context={'request': request}
            ).data
        
        if search_type in ['all', 'authors']:
            authors = Author.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(bio__icontains=query)
            ).select_related('user')[:5]
            
            results['authors'] = AuthorListSerializer(
                authors, 
                many=True, 
                context={'request': request}
            ).data
        
        # Add search metadata
        total_results = sum(len(items) for items in results.values())
        
        return Response({
            'query': query,
            'total_results': total_results,
            'results': results
        })