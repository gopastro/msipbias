from django.db import models

# Create your models here.
class TemperatureChannel(models.Model):
    channel = models.IntegerField(help_text="Channel Number")
    description = models.CharField(blank=True, null=True,
                                   max_length=100,
                                   help_text="Description of where the temperature sensor is")
    polarization = models.IntegerField(help_text="Polarization (one of 0 or 1)")
    sensor = models.IntegerField(help_text="sensor number within the polarization")

class Temperature(models.Model):
    tempchannel = models.ForeignKey(TemperatureChannel)
    temperature = models.FloatField(help_text="temperature in K")
    create_time = models.DateTimeField(auto_now_add=True,
                                       help_text="When temperature was measured")

