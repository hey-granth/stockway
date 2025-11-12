# analytics/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class AnalyticsSummary(models.Model):
    """
    Store pre-computed analytics summaries for different entity types.
    Supports system-wide, warehouse, rider, and shopkeeper metrics.
    """

    REF_TYPE_CHOICES = [
        ('system', 'System'),
        ('warehouse', 'Warehouse'),
        ('rider', 'Rider'),
        ('shopkeeper', 'Shopkeeper'),
    ]

    ref_type = models.CharField(max_length=20, choices=REF_TYPE_CHOICES, db_index=True)
    ref_id = models.IntegerField(null=True, blank=True, db_index=True, help_text="ID of the referenced entity (null for system-wide)")
    date = models.DateField(db_index=True, help_text="Date for which metrics are computed")
    metrics = models.JSONField(default=dict, help_text="JSON object containing computed metrics")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_summary'
        ordering = ['-date', 'ref_type']
        unique_together = [['ref_type', 'ref_id', 'date']]
        indexes = [
            models.Index(fields=['ref_type', 'date']),
            models.Index(fields=['ref_type', 'ref_id', 'date']),
        ]
        verbose_name = 'Analytics Summary'
        verbose_name_plural = 'Analytics Summaries'

    def __str__(self):
        if self.ref_id:
            return f"{self.ref_type} #{self.ref_id} - {self.date}"
        return f"{self.ref_type} - {self.date}"

