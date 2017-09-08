from django.db import models
from django.utils import timezone
# Create your models here.

class TorData(models.Model):
    title = models.CharField(max_length=500)
    resolution = models.CharField(max_length=10, default='720p')
    magnet = models.TextField()
    req_id = models.CharField(max_length=300, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    down_date = models.DateTimeField(null=True, blank=True)
    exist = models.BooleanField(default=False)
    v_link = models.URLField(null=True, blank=True)

    def __str__(self):
    	return self.title