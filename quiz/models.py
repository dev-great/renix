from ckeditor.fields import RichTextField
from django.db import models
from uuid import uuid4
from random import shuffle
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

# Base Class


class BaseModel(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(default='')
    total_marks = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    image = models.ImageField(
        upload_to='media/', default=None, null=True, blank=True)
    total_time = models.IntegerField(default=60)

    def __str__(self) -> str:
        return self.name

    def get_total(self):
        questions = Question.objects.filter(category=self)
        self.total_marks = sum(question.mark for question in questions)
        self.total_questions = len(questions)


class StudyCategoryModel(BaseModel):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class StudyTopicModel(BaseModel):
    category = models.ForeignKey(
        StudyCategoryModel, on_delete=models.CASCADE, related_name='category')
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class StudyModel(BaseModel):
    topic = models.ForeignKey(
        StudyTopicModel, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    is_video = models.BooleanField(default=False)
    video_uri = models.CharField(max_length=200)
    content = RichTextField()

    def __str__(self):
        return self.title


class Question(BaseModel):
    category = models.ForeignKey(
        StudyTopicModel, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    mark = models.IntegerField(default=5)

    def __str__(self) -> str:
        return f'Qut-{self.question} Cat-{self.category} Mark-{self.mark}'

    def get_answer(self):
        answers = list(Answer.objects.filter(question=self))
        shuffle(answers)
        return [
            {'answer': answer.answer, 'is_correct': answer.is_correct} for answer in answers
        ]

    class Meta:
        ordering = ['uid']


class Answer(BaseModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answers')
    answer = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.question} Ans-{self.answer} is correct-{self.is_correct}'

    class Meta:
        ordering = ['uid']


class GivenQuizQuestions(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    time_taken = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.question.question


class Quiz(BaseModel):
    status_choice = (
        ('no', 'no'),
        ('yes', 'yes'),
        ('incomplete', 'incomplete'),

    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(
        StudyTopicModel, on_delete=models.CASCADE, related_name='topic', default=None)
    given_question = models.ManyToManyField(GivenQuizQuestions, blank=True)
    marks = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)
    status = models.CharField(
        max_length=10, blank=True, default='no', null=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} {str(self.total_marks)}'

    def get_total_answered_questions_across_all_categories(self):
        all_questions = Question.objects.all()
        given_questions = GivenQuizQuestions.objects.filter(quiz=self)
        answered_questions = given_questions.values_list('question', flat=True)
        total_answered = all_questions.filter(
            uid__in=answered_questions).count()
        total_remaining = all_questions.count() - total_answered

        total_correct = given_questions.filter(answer__is_correct=True).count()
        total_wrong = given_questions.filter(answer__is_correct=False).count()

        return {
            'total_answered': total_answered,
            'total_remaining': total_remaining,
            'total_correct': total_correct,
            'total_wrong': total_wrong,
            'all_questions': all_questions.count()
        }
