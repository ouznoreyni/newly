from django.db import models
from django.contrib.auth.models import User
from news.models import Article
from common.models import BaseModel

# Create your models here.
class Comment(BaseModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    
    # Analytics
    like_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'is_approved']),
            models.Index(fields=['author', 'created_at']),
        ]
    
    def __str__(self):
        return f'Comment by {self.author.username} on {self.article.title}'
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    def get_replies(self):
        return self.replies.filter(is_approved=True).order_by('created_at')

class Like(BaseModel):
    """
    Article likes
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='article_likes')
    
    class Meta:
        unique_together = ['article', 'user']
        indexes = [
            models.Index(fields=['article']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f'{self.user.username} likes {self.article.title}'

class CommentLike(BaseModel):
    """
    Comment likes
    """
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    
    class Meta:
        unique_together = ['comment', 'user']
    
    def __str__(self):
        return f'{self.user.username} likes comment by {self.comment.author.username}'

class Bookmark(BaseModel):
    """
    User bookmarks for articles
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    notes = models.TextField(blank=True, max_length=500)
    
    class Meta:
        unique_together = ['article', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} bookmarked {self.article.title}'

class Share(BaseModel):
    """
    Track article shares
    """
    SHARE_PLATFORMS = [
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('copy_link', 'Copy Link'),
        ('other', 'Other'),
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='shares')
    platform = models.CharField(max_length=20, choices=SHARE_PLATFORMS)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        indexes = [
            models.Index(fields=['article', 'platform']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.article.title} shared on {self.platform}'

class UserPreference(BaseModel):
    """
    User reading preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    preferred_categories = models.ManyToManyField('news.Category', blank=True)
    preferred_tags = models.ManyToManyField('news.Tag', blank=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=False)
    reading_history_tracking = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.user.username} preferences'

class ReadingHistory(BaseModel):
    """
    Track user reading history
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_history')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='readers')
    read_percentage = models.PositiveIntegerField(default=0, help_text='Percentage of article read')
    time_spent = models.PositiveIntegerField(default=0, help_text='Time spent reading in seconds')
    
    class Meta:
        unique_together = ['user', 'article']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.user.username} read {self.article.title}'