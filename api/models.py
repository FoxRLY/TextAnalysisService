from django.db import models


class ReferenceSample(models.Model):
    id = models.UUIDField(primary_key=True)  # The composite primary key (id, part) found, that is not supported. The first column is selected.
    part = models.IntegerField()
    order1 = models.TextField(blank=True, null=True)
    order2 = models.TextField(blank=True, null=True)
    order3 = models.TextField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)
    theme = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'reference_samples'
        unique_together = (('id', 'part'),)



class UploadedFile(models.Model):
    file = models.FileField(upload_to="downloaded_files")
