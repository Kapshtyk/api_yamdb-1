
from datetime import date

from django.core.validators import (MaxValueValidator,
                                    MinValueValidator,
                                    validate_slug)
from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import get_object_or_404


User = get_user_model()


class Category(models.Model):
    """
    Модель для категории (типы) произведений («Фильмы», «Книги», «Музыка»).
    Одно произведение может быть привязано только к одной категории.
    """

    name = models.CharField(
        "Название категории",
        max_length=256,
    )
    slug = models.SlugField(
        "Слаг категории",
        unique=True,
        max_length=50,
        validators=[validate_slug],
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Genre(models.Model):
    """
    Модель для жанров произведений.
    Одно произведение может быть привязано к нескольким жанрам.
    """

    name = models.CharField(
        "Название жанра",
        max_length=256,
    )
    slug = models.SlugField(
        "Слаг жанра", unique=True, max_length=50, validators=[validate_slug]
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"

    def __str__(self):
        return self.name


class Title(models.Model):
    """
    Произведения, к которым пишут отзывы
    (определённый фильм, книга или песенка).
    """

    name = models.CharField(
        "Название произведения",
        max_length=256,
    )
    year = models.PositiveIntegerField(
        "Год выпуска произведения",
        validators=[
            MaxValueValidator(
                date.today().year,
                message="Нельзя добавить произведения из будущего",
            ),
        ],
    )
    description = models.TextField(
        "Описание",
        blank=True,
    )
    genre = models.ManyToManyField(
        Genre,
        blank=True,
        null=True,
        related_name="titles",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="titles",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Произведение"
        verbose_name_plural = "Произведения"

    def __str__(self):
        return self.name


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        verbose_name="Оцениваемое произведение",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор отзыва",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    text = models.TextField(verbose_name="Текст отзыва", null=False)
    score = models.IntegerField(
        verbose_name="Оценка автора отзыва",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации отзыва", auto_now_add=True
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        constraints = [
            models.UniqueConstraint(
                fields=["author", "title"], name="unique_author_title_pair"
            )
        ]

    def __str__(self):
        return (
            f"Отзыв {self.author.username} на произведение {self.title.name}"
        )

    def get_mean_score(self, title_id):
        title = get_object_or_404(Title, pk=title_id)
        try:
            return round(
                Review.objects.filter(title=title).aggregate(
                    models.Avg("score")
                )
            )
        except:
            return 0


class Comment(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации комментария", auto_now_add=True
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        constraints = [
            models.CheckConstraint(
                check=~models.Q(author=models.F("review__author")),
                name="self_commenting_check",
            )
        ]

    def __str__(self):
        return (
            f"Комментарий {self.author.username} на "
            f"отзыв {self.review.author.name}"
        )
