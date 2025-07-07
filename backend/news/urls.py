from django.urls import path, include
from rest_framework_nested import routers
from . import views

# Main router
router = routers.DefaultRouter()

# Register main viewsets
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'authors', views.AuthorViewSet, basename='author')
router.register(r'articles', views.ArticleViewSet, basename='article')
router.register(r'newsletter', views.NewsletterViewSet, basename='newsletter')
router.register(r'campaigns', views.NewsletterCampaignViewSet, basename='campaign')
router.register(r'analytics', views.DashboardAnalyticsView, basename='analytics')
router.register(r'search', views.GlobalSearchView, basename='search')

# Nested routers for categories
categories_router = routers.NestedDefaultRouter(
    router, 
    r'categories', 
    lookup='category'
)
categories_router.register(
    r'articles', 
    views.CategoryArticleViewSet, 
    basename='category-articles'
)

# Nested routers for tags
tags_router = routers.NestedDefaultRouter(
    router, 
    r'tags', 
    lookup='tag'
)
tags_router.register(
    r'articles', 
    views.TagArticleViewSet, 
    basename='tag-articles'
)

# Nested routers for authors
authors_router = routers.NestedDefaultRouter(
    router, 
    r'authors', 
    lookup='author'
)
authors_router.register(
    r'articles', 
    views.AuthorArticleViewSet, 
    basename='author-articles'
)

app_name = 'news'

urlpatterns = [
    # Main API routes
    path('', include(router.urls)),
    
    # Nested routes
    path('', include(categories_router.urls)),
    path('', include(tags_router.urls)),
    path('', include(authors_router.urls)),
]