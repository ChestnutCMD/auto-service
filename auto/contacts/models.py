from django.db import models


class Contact(models.Model):
    ICON_CHOICES = [
        ('fas fa-phone', '📞 Телефон'),
        ('fas fa-map-marker-alt', '📍 Адрес'),
        ('fas fa-envelope', '✉️ Email'),
        ('fas fa-clock', '🕒 График работы'),
        ('fas fa-car', '🚗 Автомобиль'),
        ('fas fa-tools', '🛠️ Инструменты'),
        ('fas fa-wrench', '🔧 Ремонт'),
        ('fas fa-oil-can', '🛢️ Масло'),
        ('fas fa-tire', '🎫 Шины'),
        ('fas fa-battery-full', '🔋 Аккумулятор'),
        ('fas fa-bolt', '⚡ Электрика'),
        ('fas fa-thermometer-half', '🌡️ Диагностика'),
        ('fab fa-whatsapp', '💚 WhatsApp'),
        ('fab fa-telegram', '✈️ Telegram'),
        ('fab fa-vk', '🔵 VKontakte'),
        ('fas fa-globe', '🌐 Сайт'),
        ('fas fa-user', '👤 Контактное лицо'),
        ('fas fa-building', '🏢 Компания'),
        ('fas fa-home', '🏠 Офис'),
        ('fas fa-subway', '🚇 Метро'),
        ('fas fa-bus', '🚌 Автобус'),
        ('fas fa-parking', '🅿️ Парковка'),
    ]
    name = models.CharField(max_length=100, verbose_name='Название')
    value = models.CharField(max_length=255, verbose_name='Значение')
    icon = models.CharField(
        max_length=50,
        choices=ICON_CHOICES,
        default='fas fa-phone',
        verbose_name='Иконка'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        ordering = ['order']

    def __str__(self):
        return self.name

#
# class SiteSettings(models.Model):
#     site_name = models.CharField(max_length=100, default='AutoExpert', verbose_name='Название сайта')
#     site_description = models.CharField(max_length=200, default='Профессиональный автосервис',
#                                         verbose_name='Описание сайта')
#     company_name = models.CharField(max_length=100, default='ООО "АвтоЭксперт"', verbose_name='Название компании')
#     company_address = models.TextField(verbose_name='Полный адрес')
#     working_hours = models.TextField(verbose_name='График работы')
#     email = models.EmailField(verbose_name='Email для связи')
#     phone = models.CharField(max_length=20, verbose_name='Основной телефон')
#
#     class Meta:
#         verbose_name = 'Настройки сайта'
#         verbose_name_plural = 'Настройки сайта'
#
#     def __str__(self):
#         return "Настройки сайта"
#
#     def save(self, *args, **kwargs):
#         self.__class__.objects.exclude(id=self.id).delete()
#         super().save(*args, **kwargs)
