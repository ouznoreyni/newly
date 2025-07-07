"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

def health_check(request):
    return JsonResponse({
        'status': 'ok', 
        'message': 'News API Server is running',
        'version': '1.0.0'
    })

def api_root(request):
    """API root endpoint with all available endpoints"""
    base_url = request.build_absolute_uri('/api/news/')
    
    return JsonResponse({
        'message': 'Newsly News API',
        'version': '1.0.0',
        'documentation': request.build_absolute_uri('/api/docs/'),
        'endpoints': {
            # Main endpoints
            'categories': {
                'list': f'{base_url}categories/',
                'create': f'{base_url}categories/',
                'detail': f'{base_url}categories/{{id}}/',
                'stats': f'{base_url}categories/stats/',
                'articles': f'{base_url}categories/{{id}}/articles/',
            },
            'tags': {
                'list': f'{base_url}tags/',
                'create': f'{base_url}tags/',
                'detail': f'{base_url}tags/{{id}}/',
                'articles': f'{base_url}tags/{{id}}/articles/',
            },
            'authors': {
                'list': f'{base_url}authors/',
                'detail': f'{base_url}authors/{{id}}/',
                'update': f'{base_url}authors/{{id}}/',
                'stats': f'{base_url}authors/stats/',
                'articles': f'{base_url}authors/{{id}}/articles/',
            },
            'articles': {
                'list': f'{base_url}articles/',
                'create': f'{base_url}articles/',
                'detail': f'{base_url}articles/{{id}}/',
                'update': f'{base_url}articles/{{id}}/',
                'delete': f'{base_url}articles/{{id}}/',
                'featured': f'{base_url}articles/featured/',
                'trending': f'{base_url}articles/trending/',
                'breaking': f'{base_url}articles/breaking/',
                'latest': f'{base_url}articles/latest/',
                'stats': f'{base_url}articles/stats/',
                'increment_views': f'{base_url}articles/{{id}}/increment_views/',
            },
            'newsletter': {
                'list': f'{base_url}newsletter/',
                'detail': f'{base_url}newsletter/{{id}}/',
                'subscribe': f'{base_url}newsletter/subscribe/',
                'confirm': f'{base_url}newsletter/{{id}}/confirm/',
                'unsubscribe': f'{base_url}newsletter/{{id}}/unsubscribe/',
                'resubscribe': f'{base_url}newsletter/{{id}}/resubscribe/',
            },
            'campaigns': {
                'list': f'{base_url}campaigns/',
                'create': f'{base_url}campaigns/',
                'detail': f'{base_url}campaigns/{{id}}/',
                'update': f'{base_url}campaigns/{{id}}/',
                'send': f'{base_url}campaigns/{{id}}/send/',
                'preview': f'{base_url}campaigns/{{id}}/preview/',
            },
            'analytics': {
                'overview': f'{base_url}analytics/overview/',
                'trending': f'{base_url}analytics/trending/',
                'performance': f'{base_url}analytics/performance/',
            },
            'search': {
                'global': f'{base_url}search/search/',
            },
            'admin': request.build_absolute_uri('/admin/'),
            'health': request.build_absolute_uri('/health/'),
        },
        'filtering_examples': {
            'articles_by_category': f'{base_url}articles/?category_slug=technology',
            'featured_articles': f'{base_url}articles/?is_featured=true',
            'articles_by_author': f'{base_url}articles/?author_username=john_doe',
            'recent_articles': f'{base_url}articles/?published_after=2024-01-01',
            'trending_last_3_days': f'{base_url}articles/trending/?days=3',
            'breaking_news_limit_3': f'{base_url}articles/breaking/?limit=3',
            'search_django_articles': f'{base_url}articles/?search=django',
            'high_view_articles': f'{base_url}articles/?views_min=1000',
            'verified_author_articles': f'{base_url}articles/?verified_authors=true',
            'articles_with_tags': f'{base_url}articles/?tag_slugs=python,django',
        },
        'nested_endpoints_examples': {
            'technology_category_articles': f'{base_url}categories/1/articles/',
            'python_tag_articles': f'{base_url}tags/2/articles/',
            'author_john_articles': f'{base_url}authors/3/articles/',
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API root and documentation
    path('api/', api_root, name='api-root'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # Health check
    path('health/', health_check, name='health-check'),
    # API Endpoints
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/', include('rest_framework.urls')),
    path('news/', include('news.urls')),
    path('interactions/', include('interactions.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# handler404 = 'home.views.handler404'