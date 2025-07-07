from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Category, Tag, Author, Article, ArticleView, 
    Newsletter, NewsletterCampaign
)

# ===== USER SERIALIZERS =====
class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with additional info"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'date_joined', 'last_login', 'is_active', 'article_count'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_article_count(self, obj):
        return obj.articles.filter(status='published').count()

# ===== CATEGORY SERIALIZERS =====
class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Category serializer for create/update operations"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'color', 'icon', 'is_active', 'order']

class CategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for category lists"""
    article_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'color', 'icon', 
            'is_active', 'order', 'article_count', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at', 'article_count']

class CategorySerializer(serializers.ModelSerializer):
    """Standard category serializer"""
    article_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'color', 'icon', 
            'is_active', 'order', 'article_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'article_count']
    
    def validate_color(self, value):
        """Validate hex color format"""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be a valid hex code (e.g., #007bff)")
        return value

class CategoryDetailSerializer(CategorySerializer):
    """Category serializer with nested articles"""
    recent_articles = serializers.SerializerMethodField()
    featured_articles = serializers.SerializerMethodField()
    
    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['recent_articles', 'featured_articles']
    
    def get_recent_articles(self, obj):
        from .models import Article
        recent = obj.articles.filter(status='published').order_by('-published_at')[:5]
        return ArticleNestedSerializer(recent, many=True, context=self.context).data
    
    def get_featured_articles(self, obj):
        from .models import Article
        featured = obj.articles.filter(status='published', is_featured=True)[:3]
        return ArticleNestedSerializer(featured, many=True, context=self.context).data

# ===== TAG SERIALIZERS =====
class TagListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for tag lists"""
    article_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'article_count']
        read_only_fields = ['slug', 'article_count']

class TagCreateUpdateSerializer(serializers.ModelSerializer):
    """Tag serializer for create/update operations"""
    
    class Meta:
        model = Tag
        fields = ['name', 'description']

class TagSerializer(serializers.ModelSerializer):
    """Standard tag serializer"""
    article_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'slug', 'description', 'article_count', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'article_count']

class TagDetailSerializer(TagSerializer):
    """Tag serializer with nested articles"""
    recent_articles = serializers.SerializerMethodField()
    
    class Meta(TagSerializer.Meta):
        fields = TagSerializer.Meta.fields + ['recent_articles']
    
    def get_recent_articles(self, obj):
        recent = obj.articles.filter(status='published').order_by('-published_at')[:5]
        return ArticleNestedSerializer(recent, many=True, context=self.context).data

# ===== AUTHOR SERIALIZERS =====
class AuthorCreateUpdateSerializer(serializers.ModelSerializer):
    """Author serializer for create/update operations"""
    
    class Meta:
        model = Author
        fields = [
            'bio', 'profile_picture', 'website', 'twitter_handle',
            'is_verified', 'is_staff_writer'
        ]

class AuthorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for author lists"""
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    article_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Author
        fields = [
            'id', 'username', 'full_name', 'profile_picture', 
            'is_verified', 'is_staff_writer', 'article_count'
        ]
        read_only_fields = ['article_count']

class AuthorSerializer(serializers.ModelSerializer):
    """Standard author serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    article_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Author
        fields = [
            'id', 'username', 'email', 'full_name', 'first_name', 'last_name',
            'bio', 'profile_picture', 'website', 'twitter_handle', 
            'is_verified', 'is_staff_writer', 'article_count', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'article_count']
    
    def validate_twitter_handle(self, value):
        """Validate Twitter handle format"""
        if value and not value.startswith('@'):
            value = f'@{value}'
        return value

class AuthorDetailSerializer(AuthorSerializer):
    """Author serializer with nested articles and user info"""
    user = UserDetailSerializer(read_only=True)
    recent_articles = serializers.SerializerMethodField()
    popular_articles = serializers.SerializerMethodField()
    
    class Meta(AuthorSerializer.Meta):
        fields = AuthorSerializer.Meta.fields + ['user', 'recent_articles', 'popular_articles']
    
    def get_recent_articles(self, obj):
        recent = obj.user.articles.filter(status='published').order_by('-published_at')[:5]
        return ArticleNestedSerializer(recent, many=True, context=self.context).data
    
    def get_popular_articles(self, obj):
        popular = obj.user.articles.filter(status='published').order_by('-views_count')[:3]
        return ArticleNestedSerializer(popular, many=True, context=self.context).data

# ===== ARTICLE SERIALIZERS =====
class ArticleCreateSerializer(serializers.ModelSerializer):
    """Article serializer for creation"""
    
    class Meta:
        model = Article
        fields = [
            'title', 'subtitle', 'content', 'excerpt', 'category', 'tags',
            'featured_image', 'featured_image_alt', 'featured_image_caption',
            'status', 'priority', 'published_at', 'meta_title', 'meta_description',
            'meta_keywords', 'is_featured', 'is_breaking', 'is_trending',
            'allow_comments', 'location'
        ]
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        if validated_data.get('status') == 'published' and not validated_data.get('published_at'):
            validated_data['published_at'] = timezone.now()
        return super().create(validated_data)

class ArticleUpdateSerializer(serializers.ModelSerializer):
    """Article serializer for updates"""
    
    class Meta:
        model = Article
        fields = [
            'title', 'subtitle', 'content', 'excerpt', 'category', 'tags',
            'featured_image', 'featured_image_alt', 'featured_image_caption',
            'status', 'priority', 'published_at', 'meta_title', 'meta_description',
            'meta_keywords', 'is_featured', 'is_breaking', 'is_trending',
            'allow_comments', 'location'
        ]

class ArticleNestedSerializer(serializers.ModelSerializer):
    """Minimal serializer for nested contexts (e.g., in category.articles)"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'featured_image', 'featured_image_alt',
            'author_name', 'author_username', 'category_name', 'published_at', 
            'views_count', 'read_time', 'is_featured', 'is_breaking'
        ]

class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer for article lists with essential information"""
    author = AuthorListSerializer(source='author.author_profile', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    category = CategoryListSerializer(read_only=True)
    tags = TagListSerializer(many=True, read_only=True)
    comment_count = serializers.ReadOnlyField()
    like_count = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    time_since_published = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'subtitle', 'excerpt', 'featured_image',
            'featured_image_alt', 'featured_image_caption', 'author', 'author_name', 
            'author_username', 'category', 'tags', 'status', 'priority',
            'published_at', 'time_since_published', 'is_featured', 'is_breaking', 
            'is_trending', 'views_count', 'read_time', 'location', 'comment_count', 
            'like_count', 'is_published', 'created_at'
        ]
    
    def get_time_since_published(self, obj):
        """Calculate time since publication"""
        if obj.published_at:
            delta = timezone.now() - obj.published_at
            if delta.days > 0:
                return f"{delta.days} days ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hours ago"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return "Just now"
        return None

class ArticleDetailSerializer(serializers.ModelSerializer):
    """Complete serializer for article details"""
    author = AuthorSerializer(source='author.author_profile', read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comment_count = serializers.ReadOnlyField()
    like_count = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    time_since_published = serializers.SerializerMethodField()
    related_articles = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'subtitle', 'content', 'excerpt',
            'author', 'category', 'tags', 'featured_image', 'featured_image_alt', 
            'featured_image_caption', 'status', 'priority', 'published_at', 
            'time_since_published', 'meta_title', 'meta_description', 'meta_keywords', 
            'is_featured', 'is_breaking', 'is_trending', 'allow_comments', 
            'views_count', 'read_time', 'location', 'comment_count', 'like_count', 
            'is_published', 'related_articles', 'created_at', 'updated_at'
        ]
    
    def get_time_since_published(self, obj):
        """Calculate time since publication"""
        if obj.published_at:
            delta = timezone.now() - obj.published_at
            if delta.days > 0:
                return f"{delta.days} days ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hours ago"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return "Just now"
        return None
    
    def get_related_articles(self, obj):
        """Get related articles based on category and tags"""
        # Get articles from same category
        category_articles = Article.objects.filter(
            category=obj.category,
            status='published'
        ).exclude(id=obj.id)
        
        # Get articles with same tags
        tag_articles = Article.objects.filter(
            tags__in=obj.tags.all(),
            status='published'
        ).exclude(id=obj.id).distinct()
        
        # Combine and get top 5
        related = (category_articles | tag_articles).distinct()[:5]
        return ArticleNestedSerializer(related, many=True, context=self.context).data

class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating articles"""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of tag IDs to associate with the article"
    )
    
    class Meta:
        model = Article
        fields = [
            'title', 'subtitle', 'content', 'excerpt', 'category', 'tag_ids',
            'featured_image', 'featured_image_alt', 'featured_image_caption',
            'status', 'priority', 'published_at', 'meta_title', 'meta_description',
            'meta_keywords', 'is_featured', 'is_breaking', 'is_trending',
            'allow_comments', 'location'
        ]
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance and self.instance.status == 'published' and value == 'draft':
            raise serializers.ValidationError("Cannot change published article back to draft")
        return value
    
    def validate_published_at(self, value):
        """Validate publication date"""
        if value and value > timezone.now():
            # Allow future dates for scheduling
            pass
        return value
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Set author to current user
        validated_data['author'] = self.context['request'].user
        
        # Auto-set published_at if status is published and no date is set
        if validated_data.get('status') == 'published' and not validated_data.get('published_at'):
            validated_data['published_at'] = timezone.now()
        
        article = Article.objects.create(**validated_data)
        
        if tag_ids:
            article.tags.set(tag_ids)
        
        return article
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Auto-set published_at if status is being changed to published
        if (validated_data.get('status') == 'published' and 
            instance.status != 'published' and 
            not validated_data.get('published_at')):
            validated_data['published_at'] = timezone.now()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        return instance

# ===== ARTICLE VIEW SERIALIZERS =====
class ArticleViewSerializer(serializers.ModelSerializer):
    """Serializer for article view tracking"""
    article_title = serializers.CharField(source='article.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ArticleView
        fields = [
            'id', 'article', 'article_title', 'user', 'user_username',
            'ip_address', 'user_agent', 'referrer', 'session_key', 'created_at'
        ]
        read_only_fields = ['created_at']

# ===== NEWSLETTER SERIALIZERS =====
class NewsletterListSerializer(serializers.ModelSerializer):
    """Newsletter serializer for list views"""
    categories = CategorySerializer(many=True, read_only=True)
    is_confirmed = serializers.ReadOnlyField()
    
    class Meta:
        model = Newsletter
        fields = [
            'id', 'email', 'name', 'is_active', 'categories',
            'is_confirmed', 'confirmed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['confirmed_at', 'created_at', 'updated_at']

class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    """Serializer for newsletter subscription"""
    categories = CategoryListSerializer(many=True, read_only=True)
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of category IDs to subscribe to"
    )
    is_confirmed = serializers.ReadOnlyField()
    
    class Meta:
        model = Newsletter
        fields = [
            'id', 'email', 'name', 'is_active', 'categories', 'category_ids',
            'is_confirmed', 'created_at'
        ]
        read_only_fields = ['confirmation_token', 'confirmed_at', 'unsubscribed_at', 'created_at']
    
    def validate_email(self, value):
        """Validate email format and uniqueness"""
        if Newsletter.objects.filter(email=value).exists():
            if self.instance and self.instance.email == value:
                return value  # Allow updating same email
            raise serializers.ValidationError("This email is already subscribed")
        return value
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        newsletter = Newsletter.objects.create(**validated_data)
        if category_ids:
            newsletter.categories.set(category_ids)
        return newsletter
    
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if category_ids is not None:
            instance.categories.set(category_ids)
        
        return instance

class NewsletterSerializer(NewsletterSubscriberSerializer):
    """Extended newsletter serializer for admin use"""
    
    class Meta(NewsletterSubscriberSerializer.Meta):
        fields = NewsletterSubscriberSerializer.Meta.fields + [
            'confirmation_token', 'confirmed_at', 'unsubscribed_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class NewsletterCreateSerializer(serializers.ModelSerializer):
    """Newsletter serializer for subscription"""
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Newsletter
        fields = ['email', 'name', 'category_ids']
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        newsletter = Newsletter.objects.create(**validated_data)
        if category_ids:
            newsletter.categories.set(category_ids)
        return newsletter

class NewsletterUpdateSerializer(serializers.ModelSerializer):
    """Newsletter serializer for updates"""
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Newsletter
        fields = ['name', 'is_active', 'category_ids']

# ===== NEWSLETTER CAMPAIGN SERIALIZERS =====
class NewsletterCampaignListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for campaign lists"""
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsletterCampaign
        fields = [
            'id', 'title', 'subject', 'status', 'article_count',
            'scheduled_at', 'sent_at', 'sent_count', 'created_at'
        ]
    
    def get_article_count(self, obj):
        return obj.articles.count()

class NewsletterCampaignSerializer(serializers.ModelSerializer):
    """Standard newsletter campaign serializer"""
    articles = ArticleNestedSerializer(many=True, read_only=True)
    article_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of article IDs to include in campaign"
    )
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsletterCampaign
        fields = [
            'id', 'title', 'subject', 'content', 'articles', 'article_ids',
            'article_count', 'status', 'scheduled_at', 'sent_at', 'sent_count', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['sent_at', 'sent_count', 'created_at', 'updated_at']
    
    def get_article_count(self, obj):
        return obj.articles.count()
    
    def validate_scheduled_at(self, value):
        """Validate scheduling date"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            if self.instance.status == 'sent' and value != 'sent':
                raise serializers.ValidationError("Cannot change status of sent campaign")
        return value
    
    def create(self, validated_data):
        article_ids = validated_data.pop('article_ids', [])
        campaign = NewsletterCampaign.objects.create(**validated_data)
        if article_ids:
            campaign.articles.set(article_ids)
        return campaign
    
    def update(self, instance, validated_data):
        article_ids = validated_data.pop('article_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if article_ids is not None:
            instance.articles.set(article_ids)
        
        return instance

class NewsletterCampaignCreateUpdateSerializer(serializers.ModelSerializer):
    """Newsletter campaign serializer for create/update"""
    article_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = NewsletterCampaign
        fields = ['title', 'subject', 'content', 'article_ids', 'status', 'scheduled_at']
    
    def create(self, validated_data):
        article_ids = validated_data.pop('article_ids', [])
        campaign = NewsletterCampaign.objects.create(**validated_data)
        if article_ids:
            campaign.articles.set(article_ids)
        return campaign
    
# ===== SUMMARY/STATS SERIALIZERS =====
class CategoryStatsSerializer(serializers.Serializer):
    """Serializer for category statistics"""
    category = CategoryListSerializer()
    article_count = serializers.IntegerField()
    total_views = serializers.IntegerField()
    avg_read_time = serializers.FloatField()

class AuthorStatsSerializer(serializers.Serializer):
    """Serializer for author statistics"""
    author = AuthorListSerializer()
    article_count = serializers.IntegerField()
    total_views = serializers.IntegerField()
    avg_views_per_article = serializers.FloatField()

class ArticleStatsSerializer(serializers.Serializer):
    """Serializer for article statistics"""
    total_articles = serializers.IntegerField()
    published_articles = serializers.IntegerField()
    draft_articles = serializers.IntegerField()
    total_views = serializers.IntegerField()
    avg_read_time = serializers.FloatField()
    most_viewed_article = ArticleNestedSerializer()
    recent_articles = ArticleNestedSerializer(many=True)

# ===== SEARCH SERIALIZERS =====
class SearchResultSerializer(serializers.Serializer):
    """Serializer for search results"""
    articles = ArticleListSerializer(many=True)
    categories = CategoryListSerializer(many=True)
    authors = AuthorListSerializer(many=True)
    tags = TagListSerializer(many=True)
    total_results = serializers.IntegerField()
    query = serializers.CharField()