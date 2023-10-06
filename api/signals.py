from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Review


@receiver(post_save, sender=Review)
def update_pharmacy_review(sender, instance, created, **kwargs):
    """
    Update the associated Pharmacy's review_count and rating when a new review is created.
    """
    if created:
        print("Update review signal triggered")
        pharmacy = instance.reviewee.owner
        pharmacy.review_count = Review.objects.filter(
            reviewee__owner=pharmacy).count()
        pharmacy.calculate_average_rating()
        pharmacy.save()
