from django.db import models

class Category(models.Model):
    name=models.CharField(max_length=30)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return self.name
