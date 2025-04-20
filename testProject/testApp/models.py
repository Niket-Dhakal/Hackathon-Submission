from django.db import models

# Create your models here.
class UserSearchInfo(models.Model):
    vocabularyTerm = models.CharField(max_length=50)
    searchRegion = models.CharField(max_length=50)

    def __str__(self):
        return self.vocabularyTerm.title()
