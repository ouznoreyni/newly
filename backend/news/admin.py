# ===== news/admin.py (Fixed version) =====
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone
from django.contrib.admin import SimpleListFilter
from .models import Category, Tag, Author, Article, ArticleView, Newsletter, NewsletterCampaign

# =============================================================================
# CUSTOM FILTERS
# =============================================================================

class PublishedFilter(SimpleListFilter):
    title = 'Published Status'
    parameter_name = 'published'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Published'),
            ('no', 'Not Published'),
            ('scheduled', 'Scheduled'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(status='published', published_at__isnull=False)
        if self.value() == 'no':
            return queryset.exclude(status='published')
        if self.value() == 'scheduled':
            return queryset.filter(status='published', published_at__gt=timezone.now())

class ViewCountFilter(SimpleListFilter):
    title = 'View Count'
    parameter_name = 'views'

    def lookups(self, request, model_admin):
        return (
            ('high', 'High (1000+)'),
            ('medium', 'Medium (100-999)'),
            ('low', 'Low (0-99)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(views_count__gte=1000)
        if self.value() == 'medium':
            return queryset.filter(views_count__gte=100, views_count__lt=1000)
        if self.value() == 'low':
            return queryset.filter(views_count__lt=100)

# =============================================================================
# CATEGORY ADMIN
# =============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'colored_name', 'slug', 'article_count_display', 
        'is_active', 'order', 'created_at_display'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'slug']
    list_editable = ['is_active', 'order']
    list_per_page = 25
    ordering = ['order', 'name']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'article_count_display']
    
    fieldsets = (
        ('📝 Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('🎨 Appearance', {
            'fields': ('color', 'icon'),
            'description': 'Visual settings for the category'
        }),
        ('⚙️ Settings', {
            'fields': ('is_active', 'order'),
            'description': 'Category visibility and ordering'
        }),
        ('📊 Statistics', {
            'fields': ('article_count_display',),
            'classes': ('collapse',),
            'description': 'Category performance metrics'
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def colored_name(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            obj.color,
            obj.name
        )
    colored_name.short_description = '🏷️ Category'
    colored_name.admin_order_field = 'name'
    
    def article_count_display(self, obj):
        count = obj.article_count
        if count == 0:
            color = '#dc3545'  # Red
            icon = '📭'
        elif count < 5:
            color = '#ffc107'  # Yellow
            icon = '📄'
        else:
            color = '#28a745'  # Green
            icon = '📚'
        
        url = reverse('admin:news_article_changelist') + f'?category__id__exact={obj.id}'
        return format_html(
            '<a href="{}" style="color: {}; text-decoration: none;">'
            '{} {} articles</a>',
            url, color, icon, count
        )
    article_count_display.short_description = '📊 Articles'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = '📅 Created'
    created_at_display.admin_order_field = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            article_count=Count('articles')
        )

# =============================================================================
# TAG ADMIN
# =============================================================================

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = [
        'name_with_icon', 'slug', 'article_count_display', 'created_at_display'
    ]
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'slug']
    list_per_page = 50
    ordering = ['name']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'article_count_display']
    
    fieldsets = (
        ('📝 Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('📊 Statistics', {
            'fields': ('article_count_display',),
            'classes': ('collapse',),
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def name_with_icon(self, obj):
        return format_html('🔖 {}', obj.name)
    name_with_icon.short_description = '🏷️ Tag Name'
    name_with_icon.admin_order_field = 'name'
    
    def article_count_display(self, obj):
        count = obj.article_count
        url = reverse('admin:news_article_changelist') + f'?tags__id__exact={obj.id}'
        
        if count == 0:
            return format_html(
                '<span style="color: #6c757d;">📭 No articles</span>'
            )
        
        return format_html(
            '<a href="{}" style="color: #007bff; text-decoration: none;">'
            '📄 {} articles</a>',
            url, count
        )
    article_count_display.short_description = '📊 Usage'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')
    created_at_display.short_description = '📅 Created'
    created_at_display.admin_order_field = 'created_at'

# =============================================================================
# AUTHOR ADMIN
# =============================================================================

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = [
        'author_info', 'is_verified', 'is_staff_writer', 
        'article_count_display', 'joined_date'
    ]
    list_filter = [
        'is_verified', 'is_staff_writer', 'created_at', 
        ('user__is_staff', admin.BooleanFieldListFilter)
    ]
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'bio'
    ]
    list_editable = ['is_verified', 'is_staff_writer']
    list_per_page = 25
    ordering = ['user__username']
    readonly_fields = ['created_at', 'updated_at', 'article_count_display', 'user_info']
    
    fieldsets = (
        ('👤 User Information', {
            'fields': ('user', 'user_info'),
            'description': 'Basic user account information'
        }),
        ('📝 Profile', {
            'fields': ('bio', 'profile_picture', 'website', 'twitter_handle'),
            'description': 'Author profile information'
        }),
        ('🏆 Status', {
            'fields': ('is_verified', 'is_staff_writer'),
            'description': 'Author verification and privileges'
        }),
        ('📊 Statistics', {
            'fields': ('article_count_display',),
            'classes': ('collapse',),
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def author_info(self, obj):
        avatar = '👤'
        if obj.profile_picture:
            avatar = format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%;">',
                obj.profile_picture.url
            )
        
        full_name = obj.user.get_full_name() or obj.user.username
        return format_html('{} <strong>{}</strong><br><small>{}</small>', 
                          avatar, full_name, obj.user.email)
    author_info.short_description = '👤 Author'
    
    def article_count_display(self, obj):
        count = obj.article_count
        url = reverse('admin:news_article_changelist') + f'?author__id__exact={obj.user.id}'
        
        if count == 0:
            return format_html('<span style="color: #6c757d;">📭 No articles</span>')
        elif count < 5:
            color = '#ffc107'
            icon = '📄'
        else:
            color = '#28a745'
            icon = '📚'
        
        return format_html(
            '<a href="{}" style="color: {}; text-decoration: none;">'
            '{} {} articles</a>',
            url, color, icon, count
        )
    article_count_display.short_description = '📊 Articles'
    
    def joined_date(self, obj):
        return obj.user.date_joined.strftime('%Y-%m-%d')
    joined_date.short_description = '📅 Joined'
    joined_date.admin_order_field = 'user__date_joined'
    
    def user_info(self, obj):
        return format_html(
            '<strong>Username:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Staff:</strong> {}<br>'
            '<strong>Active:</strong> {}',
            obj.user.username,
            obj.user.email,
            '✅' if obj.user.is_staff else '❌',
            '✅' if obj.user.is_active else '❌'
        )
    user_info.short_description = 'ℹ️ User Details'

# =============================================================================
# ARTICLE ADMIN
# =============================================================================

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title_with_status', 'author_info', 'category_display', 
        'status', 'is_featured', 'priority', 'engagement_stats', 
        'published_display', 'created_at_display'
    ]
    list_filter = [
        'status', 'priority', 'is_featured', 'is_breaking', 'is_trending',
        'allow_comments', 'category', 'created_at', 'published_at',
        PublishedFilter, ViewCountFilter
    ]
    search_fields = [
        'title', 'content', 'excerpt', 'author__username', 
        'author__first_name', 'author__last_name'
    ]
    filter_horizontal = ['tags']
    list_editable = ['status', 'is_featured', 'priority']
    list_per_page = 25
    date_hierarchy = 'published_at'
    ordering = ['-created_at']
    readonly_fields = [
        'slug', 'views_count', 'read_time', 'created_at', 'updated_at',
        'engagement_summary', 'seo_preview'
    ]
    
    fieldsets = (
        ('📝 Content', {
            'fields': ('title', 'slug', 'subtitle', 'content', 'excerpt'),
            'description': 'Main article content and summary'
        }),
        ('👤 Author & Classification', {
            'fields': ('author', 'category', 'tags'),
            'description': 'Author and content categorization'
        }),
        ('🖼️ Media', {
            'fields': ('featured_image', 'featured_image_alt', 'featured_image_caption'),
            'description': 'Article images and media'
        }),
        ('📊 Publishing', {
            'fields': ('status', 'priority', 'published_at'),
            'description': 'Publication settings and scheduling'
        }),
        ('🔍 SEO & Metadata', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'seo_preview'),
            'classes': ('collapse',),
            'description': 'Search engine optimization'
        }),
        ('⭐ Features', {
            'fields': ('is_featured', 'is_breaking', 'is_trending', 'allow_comments', 'location'),
            'description': 'Special article features and settings'
        }),
        ('📈 Analytics', {
            'fields': ('views_count', 'read_time', 'engagement_summary'),
            'classes': ('collapse',),
            'description': 'Article performance metrics'
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def title_with_status(self, obj):
        icons = []
        if obj.is_featured:
            icons.append('⭐')
        if obj.is_breaking:
            icons.append('🚨')
        if obj.is_trending:
            icons.append('🔥')
        
        icon_str = ' '.join(icons)
        title = obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
        
        return format_html(
            '<strong>{}</strong> {}',
            title, icon_str
        )
    title_with_status.short_description = '📰 Title'
    title_with_status.admin_order_field = 'title'
    
    def author_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.author.get_full_name() or obj.author.username,
            obj.author.email
        )
    author_info.short_description = '👤 Author'
    
    def category_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            obj.category.color,
            obj.category.name
        )
    category_display.short_description = '🏷️ Category'
    category_display.admin_order_field = 'category__name'
    
    def engagement_stats(self, obj):
        stats = []
        
        # Views
        if obj.views_count > 0:
            if obj.views_count >= 1000:
                stats.append(f'👀 {obj.views_count:,}')
            else:
                stats.append(f'👀 {obj.views_count}')
        
        # Comments (when implemented)
        comment_count = getattr(obj, 'comment_count', 0)
        if comment_count > 0:
            stats.append(f'💬 {comment_count}')
        
        # Likes (when implemented)
        like_count = getattr(obj, 'like_count', 0)
        if like_count > 0:
            stats.append(f'❤️ {like_count}')
        
        # Read time
        if obj.read_time > 0:
            stats.append(f'⏱️ {obj.read_time}min')
        
        return format_html('<br>'.join(stats)) if stats else '—'
    engagement_stats.short_description = '📊 Engagement'
    
    def published_display(self, obj):
        if obj.published_at:
            if obj.published_at > timezone.now():
                return format_html(
                    '<span style="color: #ffc107;">🕐 Scheduled<br>{}</span>',
                    obj.published_at.strftime('%Y-%m-%d %H:%M')
                )
            return format_html(
                '<span style="color: #28a745;">✅ Published<br>{}</span>',
                obj.published_at.strftime('%Y-%m-%d %H:%M')
            )
        return format_html('<span style="color: #6c757d;">❌ Not published</span>')
    published_display.short_description = '📅 Published'
    published_display.admin_order_field = 'published_at'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = '📅 Created'
    created_at_display.admin_order_field = 'created_at'
    
    def engagement_summary(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>📊 Engagement Summary</strong><br>'
            '👀 Views: {}<br>'
            '💬 Comments: {}<br>'
            '❤️ Likes: {}<br>'
            '⏱️ Read Time: {} minutes<br>'
            '📅 Published: {}'
            '</div>',
            obj.views_count,
            getattr(obj, 'comment_count', 0),
            getattr(obj, 'like_count', 0),
            obj.read_time,
            obj.published_at.strftime('%Y-%m-%d %H:%M') if obj.published_at else 'Not published'
        )
    engagement_summary.short_description = '📊 Engagement Summary'
    
    def seo_preview(self, obj):
        title = obj.meta_title or obj.title
        description = obj.meta_description or obj.excerpt
        
        return format_html(
            '<div style="border: 1px solid #ddd; padding: 10px; max-width: 500px;">'
            '<div style="color: #1a0dab; font-size: 18px; text-decoration: underline;">{}</div>'
            '<div style="color: #006621; font-size: 14px;">https://newsly.com/articles/{}/</div>'
            '<div style="color: #545454; font-size: 13px; margin-top: 5px;">{}</div>'
            '</div>',
            title[:60] + '...' if len(title) > 60 else title,
            obj.slug,
            description[:160] + '...' if len(description) > 160 else description
        )
    seo_preview.short_description = '🔍 SEO Preview'
    
    actions = ['make_featured', 'make_published', 'make_draft']
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} articles marked as featured.')
    make_featured.short_description = '⭐ Mark selected articles as featured'
    
    def make_published(self, request, queryset):
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} articles published.')
    make_published.short_description = '✅ Publish selected articles'
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} articles moved to draft.')
    make_draft.short_description = '📝 Move selected articles to draft'

# =============================================================================
# ARTICLE VIEW ADMIN
# =============================================================================

@admin.register(ArticleView)
class ArticleViewAdmin(admin.ModelAdmin):
    list_display = [
        'article_title', 'user_info', 'ip_address', 
        'referrer_display', 'created_at_display'
    ]
    list_filter = ['created_at', 'article__category']
    search_fields = ['article__title', 'user__username', 'ip_address']
    readonly_fields = ['article', 'user', 'ip_address', 'user_agent', 'referrer', 'session_key', 'created_at']
    list_per_page = 50
    ordering = ['-created_at']
    
    def article_title(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:news_article_change', args=[obj.article.id]),
            obj.article.title[:50] + '...' if len(obj.article.title) > 50 else obj.article.title
        )
    article_title.short_description = '📰 Article'
    
    def user_info(self, obj):
        if obj.user:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                obj.user.get_full_name() or obj.user.username,
                obj.user.email
            )
        return format_html('<span style="color: #6c757d;">🔒 Anonymous</span>')
    user_info.short_description = '👤 User'
    
    def referrer_display(self, obj):
        if obj.referrer:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.referrer,
                obj.referrer[:30] + '...' if len(obj.referrer) > 30 else obj.referrer
            )
        return '—'
    referrer_display.short_description = '🔗 Referrer'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.short_description = '📅 Viewed At'
    created_at_display.admin_order_field = 'created_at'

# =============================================================================
# NEWSLETTER ADMIN
# =============================================================================

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = [
        'email_with_status', 'name', 'subscription_status', 
        'categories_display', 'subscription_date'
    ]
    list_filter = [
        'is_active', 'created_at', 'confirmed_at', 'unsubscribed_at',
        ('confirmed_at', admin.DateFieldListFilter)
    ]
    search_fields = ['email', 'name']
    filter_horizontal = ['categories']
    readonly_fields = [
        'confirmation_token', 'confirmed_at', 'unsubscribed_at', 
        'created_at', 'updated_at', 'subscription_summary'
    ]
    list_per_page = 50
    ordering = ['-created_at']
    
    fieldsets = (
        ('📧 Subscriber Information', {
            'fields': ('email', 'name', 'is_active')
        }),
        ('🏷️ Preferences', {
            'fields': ('categories',),
            'description': 'Newsletter categories of interest'
        }),
        ('🔐 Subscription Details', {
            'fields': ('confirmation_token', 'confirmed_at', 'unsubscribed_at'),
            'classes': ('collapse',),
        }),
        ('📊 Summary', {
            'fields': ('subscription_summary',),
            'classes': ('collapse',),
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def email_with_status(self, obj):
        icon = '✅' if obj.is_confirmed else '⏳'
        return format_html('{} {}', icon, obj.email)
    email_with_status.short_description = '📧 Email'
    email_with_status.admin_order_field = 'email'
    
    def subscription_status(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: #dc3545;">❌ Unsubscribed</span>')
        elif obj.is_confirmed:
            return format_html('<span style="color: #28a745;">✅ Active</span>')
        else:
            return format_html('<span style="color: #ffc107;">⏳ Pending</span>')
    subscription_status.short_description = '📊 Status'
    
    def categories_display(self, obj):
        categories = obj.categories.all()[:3]  # Show first 3
        if not categories:
            return format_html('<span style="color: #6c757d;">📭 None</span>')
        
        category_list = [f'<span style="color: {cat.color};">● {cat.name}</span>' for cat in categories]
        if obj.categories.count() > 3:
            category_list.append(f'<small>+{obj.categories.count() - 3} more</small>')
        
        return format_html('<br>'.join(category_list))
    categories_display.short_description = '🏷️ Categories'
    
    def subscription_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')
    subscription_date.short_description = '📅 Subscribed'
    subscription_date.admin_order_field = 'created_at'
    
    def subscription_summary(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>📊 Subscription Summary</strong><br>'
            '📧 Email: {}<br>'
            '📅 Subscribed: {}<br>'
            '✅ Confirmed: {}<br>'
            '❌ Unsubscribed: {}<br>'
            '🏷️ Categories: {}'
            '</div>',
            obj.email,
            obj.created_at.strftime('%Y-%m-%d %H:%M'),
            obj.confirmed_at.strftime('%Y-%m-%d %H:%M') if obj.confirmed_at else 'Not confirmed',
            obj.unsubscribed_at.strftime('%Y-%m-%d %H:%M') if obj.unsubscribed_at else 'Active',
            obj.categories.count()
        )
    subscription_summary.short_description = '📊 Summary'

# =============================================================================
# NEWSLETTER CAMPAIGN ADMIN
# =============================================================================

@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'title_with_status', 'campaign_status', 'article_count_display',
        'recipient_info', 'schedule_info', 'created_at_display'
    ]
    list_filter = [
        'status', 'created_at', 'scheduled_at', 'sent_at',
        ('scheduled_at', admin.DateFieldListFilter),
        ('sent_at', admin.DateFieldListFilter)
    ]
    search_fields = ['title', 'subject', 'content']
    filter_horizontal = ['articles']
    readonly_fields = [
        'sent_at', 'sent_count', 'created_at', 'updated_at',
        'campaign_summary', 'preview_content'
    ]
    list_per_page = 25
    ordering = ['-created_at']
    
    fieldsets = (
        ('📧 Campaign Details', {
            'fields': ('title', 'subject', 'content'),
            'description': 'Campaign title, email subject, and content'
        }),
        ('📰 Articles', {
            'fields': ('articles',),
            'description': 'Articles to include in this campaign'
        }),
        ('📊 Campaign Settings', {
            'fields': ('status', 'scheduled_at'),
            'description': 'Campaign status and scheduling'
        }),
        ('📈 Campaign Results', {
            'fields': ('sent_at', 'sent_count'),
            'classes': ('collapse',),
            'description': 'Campaign delivery statistics'
        }),
        ('👀 Preview', {
            'fields': ('preview_content',),
            'classes': ('collapse',),
            'description': 'Email content preview'
        }),
        ('📊 Summary', {
            'fields': ('campaign_summary',),
            'classes': ('collapse',),
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def title_with_status(self, obj):
        title = obj.title[:40] + '...' if len(obj.title) > 40 else obj.title
        return format_html('<strong>{}</strong>', title)
    title_with_status.short_description = '📧 Campaign'
    title_with_status.admin_order_field = 'title'
    
    def campaign_status(self, obj):
        status_colors = {
            'draft': '#6c757d',
            'scheduled': '#ffc107',
            'sent': '#28a745'
        }
        status_icons = {
            'draft': '📝',
            'scheduled': '⏰',
            'sent': '✅'
        }
        
        color = status_colors.get(obj.status, '#6c757d')
        icon = status_icons.get(obj.status, '❓')
        
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    campaign_status.short_description = '📊 Status'
    campaign_status.admin_order_field = 'status'
    
    def article_count_display(self, obj):
        count = obj.articles.count()
        if count == 0:
            return format_html('<span style="color: #6c757d;">📭 No articles</span>')
        
        return format_html(
            '<span style="color: #007bff;">📄 {} articles</span>',
            count
        )
    article_count_display.short_description = '📰 Articles'
    
    def recipient_info(self, obj):
        if obj.status == 'sent':
            return format_html(
                '<span style="color: #28a745;">📧 {} recipients</span>',
                obj.sent_count
            )
        else:
            # Count active subscribers
            active_subscribers = Newsletter.objects.filter(
                is_active=True,
                confirmed_at__isnull=False
            ).count()
            return format_html(
                '<span style="color: #007bff;">👥 {} potential</span>',
                active_subscribers
            )
    recipient_info.short_description = '👥 Recipients'
    
    def schedule_info(self, obj):
        if obj.status == 'sent' and obj.sent_at:
            return format_html(
                '<span style="color: #28a745;">✅ Sent<br>{}</span>',
                obj.sent_at.strftime('%Y-%m-%d %H:%M')
            )
        elif obj.status == 'scheduled' and obj.scheduled_at:
            if obj.scheduled_at > timezone.now():
                return format_html(
                    '<span style="color: #ffc107;">⏰ Scheduled<br>{}</span>',
                    obj.scheduled_at.strftime('%Y-%m-%d %H:%M')
                )
            else:
                return format_html(
                    '<span style="color: #dc3545;">⚠️ Overdue<br>{}</span>',
                    obj.scheduled_at.strftime('%Y-%m-%d %H:%M')
                )
        return format_html('<span style="color: #6c757d;">📝 Draft</span>')
    schedule_info.short_description = '📅 Schedule'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = '📅 Created'
    created_at_display.admin_order_field = 'created_at'
    
    def campaign_summary(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<strong>📊 Campaign Summary</strong><br>'
            '📧 Title: {}<br>'
            '📝 Subject: {}<br>'
            '📰 Articles: {}<br>'
            '📊 Status: {}<br>'
            '📅 Created: {}<br>'
            '⏰ Scheduled: {}<br>'
            '✅ Sent: {}<br>'
            '👥 Recipients: {}'
            '</div>',
            obj.title,
            obj.subject,
            obj.articles.count(),
            obj.get_status_display(),
            obj.created_at.strftime('%Y-%m-%d %H:%M'),
            obj.scheduled_at.strftime('%Y-%m-%d %H:%M') if obj.scheduled_at else 'Not scheduled',
            obj.sent_at.strftime('%Y-%m-%d %H:%M') if obj.sent_at else 'Not sent',
            obj.sent_count if obj.sent_count else 'N/A'
        )
    campaign_summary.short_description = '📊 Summary'
    
    def preview_content(self, obj):
        content_preview = obj.content[:200] + '...' if len(obj.content) > 200 else obj.content
        
        articles_preview = ''
        if obj.articles.exists():
            articles_preview = '<br><strong>📰 Included Articles:</strong><br>'
            for article in obj.articles.all()[:3]:
                articles_preview += f'• {article.title}<br>'
            if obj.articles.count() > 3:
                articles_preview += f'• ... and {obj.articles.count() - 3} more'
        
        return format_html(
            '<div style="border: 1px solid #ddd; padding: 10px; max-width: 500px; background: white;">'
            '<strong>Subject:</strong> {}<br><br>'
            '<strong>Content:</strong><br>{}{}'
            '</div>',
            obj.subject,
            content_preview,
            articles_preview
        )
    preview_content.short_description = '👀 Email Preview'
    
    actions = ['schedule_campaigns', 'send_campaigns', 'move_to_draft']
    
    def schedule_campaigns(self, request, queryset):
        updated = queryset.filter(status='draft').update(
            status='scheduled',
            scheduled_at=timezone.now() + timezone.timedelta(hours=1)
        )
        self.message_user(request, f'{updated} campaigns scheduled for 1 hour from now.')
    schedule_campaigns.short_description = '⏰ Schedule selected campaigns'
    
    def send_campaigns(self, request, queryset):
        sent_count = 0
        for campaign in queryset.filter(status__in=['draft', 'scheduled']):
            # Here you would implement actual email sending
            campaign.status = 'sent'
            campaign.sent_at = timezone.now()
            campaign.sent_count = Newsletter.objects.filter(
                is_active=True,
                confirmed_at__isnull=False
            ).count()
            campaign.save()
            sent_count += 1
        
        self.message_user(request, f'{sent_count} campaigns sent successfully.')
    send_campaigns.short_description = '📧 Send selected campaigns'
    
    def move_to_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} campaigns moved to draft.')
    move_to_draft.short_description = '📝 Move to draft'

# =============================================================================
# ADMIN SITE CUSTOMIZATION
# =============================================================================

# Customize admin site header and title
admin.site.site_header = '📰 Newsly Administration'
admin.site.site_title = 'Newsly Admin'
admin.site.index_title = '📊 Content Management Dashboard'

# =============================================================================
# ADMIN ACTIONS
# =============================================================================

def make_featured(modeladmin, request, queryset):
    """Make selected articles featured"""
    updated = queryset.update(is_featured=True)
    modeladmin.message_user(request, f'{updated} articles marked as featured.')
make_featured.short_description = '⭐ Mark selected articles as featured'

def make_published(modeladmin, request, queryset):
    """Publish selected articles"""
    updated = queryset.update(status='published', published_at=timezone.now())
    modeladmin.message_user(request, f'{updated} articles published.')
make_published.short_description = '✅ Publish selected articles'

def make_draft(modeladmin, request, queryset):
    """Move selected articles to draft"""
    updated = queryset.update(status='draft')
    modeladmin.message_user(request, f'{updated} articles moved to draft.')
make_draft.short_description = '📝 Move selected articles to draft'

# Register global actions
admin.site.add_action(make_featured, 'make_featured')
admin.site.add_action(make_published, 'make_published')
admin.site.add_action(make_draft, 'make_draft')